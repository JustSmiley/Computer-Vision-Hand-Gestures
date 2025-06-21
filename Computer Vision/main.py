import sys

# Dependency checks
try:
    import cv2
    import mediapipe as mp
    import math
    import numpy as np
    import time
    import sounddevice as sd
    import threading
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
except ImportError as exception:
    print(f"Missing module: {exception.name}. Please install it using pip.")
    sys.exit(1)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.7)

def find_working_cameras(max_index=10):
    cameras = []
    for index in range(max_index):
        temp_cap = cv2.VideoCapture(index)
        if temp_cap.isOpened():
            success, _ = temp_cap.read()
            if success:
                cameras.append(index)
            temp_cap.release()
    if not cameras:
        raise RuntimeError("No working webcams found. ❌")
    return cameras

def set_volume(volume):
    if 0 <= volume <= 100:
        try:
            cast(AudioUtilities
                 .GetSpeakers()
                 .Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None),
                 POINTER(IAudioEndpointVolume)
            ).SetMasterVolumeLevelScalar(volume / 100, None)
        except Exception as exception:
            print(f"Error setting volume:\n{exception}")
    else:
        print(f"Error: Volume {volume} is out of range (0–100).")

def draw_star_of_david(dist, frame, width, height, color=(185, 0, 0), thickness=3):
    radius = max(0, min(170, int((dist / 100) * 170)))
    center = (width // 2, height // 2)

    def triangle_points(center, radius, rotation_deg):
        return [
            (
                int(center[0] + radius * math.cos(math.radians(120 * i + rotation_deg))),
                int(center[1] + radius * math.sin(math.radians(120 * i + rotation_deg)))
            )
            for i in range(3)
        ]

    triangle_up = triangle_points(center, radius, -90)
    triangle_down = triangle_points(center, radius, -30)

    cv2.polylines(frame, [np.array(triangle_up, np.int32)], isClosed=True, color=color, thickness=thickness)
    cv2.polylines(frame, [np.array(triangle_down, np.int32)], isClosed=True, color=color, thickness=thickness)

def count_fingers(hand_landmarks, hand_label):
    fingers = []
    tips_ids = [4, 8, 12, 16, 20]
    pip_ids = [3, 6, 10, 14, 18]

    if hand_label == "Right":
        fingers.append(int(hand_landmarks.landmark[tips_ids[0]].x < hand_landmarks.landmark[pip_ids[0]].x))
    else:
        fingers.append(int(hand_landmarks.landmark[tips_ids[0]].x > hand_landmarks.landmark[pip_ids[0]].x))

    for i in range(1, 5):
        fingers.append(int(hand_landmarks.landmark[tips_ids[i]].y < hand_landmarks.landmark[pip_ids[i]].y))

    return sum(fingers)

def switch_camera(current_cam_idx, working_cameras, cap):
    if cap is not None:
        cap.release()
    current_cam_idx = (current_cam_idx + 1) % len(working_cameras)
    new_cap = cv2.VideoCapture(working_cameras[current_cam_idx])
    return current_cam_idx, new_cap

def play_tone(frequency=440, duration=0.2, volume=0.5, samplerate=44100):
    def _play():
        t = np.linspace(0, duration, int(samplerate * duration), False)
        wave = volume * np.sin(2 * np.pi * frequency * t)
        sd.play(wave, samplerate, blocking=True)
    threading.Thread(target=_play, daemon=True).start()

last_play_time = 0
play_interval = 0.3

# Setup
working_cameras = find_working_cameras()
current_cam_idx = 0
cap = cv2.VideoCapture(working_cameras[current_cam_idx])

switching = False
switch_start_time = 0
switch_duration = 2.5

min_hand_dist = 30
max_hand_dist = None  # will be set dynamically

try:
    while True:
        success, frame = cap.read()
        if not success:
            print("Warning: Failed to grab frame. ❌")
            continue

        height, width, _ = frame.shape

        if switching:
            switch_frame = np.zeros((height, width, 3), dtype=np.uint8)
            cv2.putText(switch_frame, "Switching camera...", (width // 4, height // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3)
            cv2.imshow("Webcam", switch_frame)

            if time.time() - switch_start_time > switch_duration:
                switching = False

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            continue

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(frame_rgb)

        valid_hands = []
        valid_labels = []

        if result.multi_hand_landmarks and result.multi_handedness:
            for hand_landmarks, hand_handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                wrist_y_px = int(hand_landmarks.landmark[0].y * height)
                if wrist_y_px < height // 2:
                    valid_hands.append(hand_landmarks)
                    valid_labels.append(hand_handedness.classification[0].label)

        cv2.line(frame, (0, height // 2), (width, height // 2), (0, 255, 255), 2)

        if len(valid_hands) < 1:
            cv2.putText(frame, "No hands detected", (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        elif len(valid_hands) == 1:
            cv2.putText(frame, "Only 1 hand detected", (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)
        else:
            measure_hand = valid_hands[0]
            trigger_hand = valid_hands[1]
            measure_label = valid_labels[0]
            trigger_label = valid_labels[1]

            fingers_up_count = count_fingers(trigger_hand, trigger_label)

            thumb_tip = measure_hand.landmark[4]
            index_tip = measure_hand.landmark[8]
            thumb_pos = (int(thumb_tip.x * width), int(thumb_tip.y * height))
            index_pos = (int(index_tip.x * width), int(index_tip.y * height))

            # Dynamically set max_hand_dist to 1/4 of the screen height
            max_hand_dist = height / 4

            dist_raw = math.hypot(index_pos[0] - thumb_pos[0], index_pos[1] - thumb_pos[1])
            dist_clamped = max(min_hand_dist, min(max_hand_dist, dist_raw))

            # Map to 0–100 where 100 = 1/4 screen height
            volume_level = round((dist_clamped - min_hand_dist) / (max_hand_dist - min_hand_dist) * 100)
            volume_level = min(volume_level, 100)

            cv2.line(frame, thumb_pos, index_pos, (255, 255, 255), 3)

            if fingers_up_count == 1:
                set_volume(volume_level)
                cv2.putText(frame, f'Volume: {volume_level}', (10, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 220), 2)
                current_time = time.time()
                if current_time - last_play_time > play_interval:
                    play_tone(frequency=440 + volume_level * 2, volume=0.4)
                    last_play_time = current_time

            elif fingers_up_count == 2:
                draw_star_of_david(volume_level, frame, width, height)
                cv2.putText(frame, f'Star size: {volume_level}', (10, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 220), 2)

        if len(working_cameras) > 1:
            cv2.putText(frame, "Press 'c' to cycle cameras", (10, height - 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.putText(frame, "Press 'q' to quit", (10, height - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("Webcam", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('c') and len(working_cameras) > 1:
            switching = True
            switch_start_time = time.time()
            current_cam_idx, cap = switch_camera(current_cam_idx, working_cameras, cap)

except Exception as exception:
    print(f"Unexpected error:\n{exception}\n")

finally:
    hands.close()
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()

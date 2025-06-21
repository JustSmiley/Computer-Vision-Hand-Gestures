# ✋ Computer Vision Hand Gesture Demo

A demonstration project showcasing the potential of computer vision and hand tracking technology using your webcam.  
It detects hand gestures to control volume and display dynamic symbols — illustrating how intuitive gesture-based interfaces can be built.

---

## 🚀 Features

- Detects up to two hands simultaneously using MediaPipe.  
- Adjusts system volume by measuring the distance between thumb and index finger when one finger is raised.  
- Displays a Star of David symbol when two fingers are raised, with size based on hand distance.  
- Plays a tone corresponding to the volume level for auditory feedback.  
- Supports multiple webcams with easy switching (`c` key).  
- Quit the program anytime with the `q` key.  
- Demonstrates real-time computer vision capabilities and user interaction.

---

## 📋 Requirements

Install required Python packages:

```bash
pip install -r requirements.txt

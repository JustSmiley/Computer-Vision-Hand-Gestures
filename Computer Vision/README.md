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

## 💡 Instructions

- Position your hands **above the halfway line** (the program draws a horizontal line across the middle of the webcam feed). Only hands detected above this line are used to control gestures.  
  This helps avoid accidental activation during normal tasks and improves user experience.

- **Trigger hand** and **measuring hand** selection:  
  - The first detected hand becomes the *trigger hand*.  
  - The trigger hand controls the number of fingers raised (the command selector).  
  - The other hand is the *measuring hand* used to measure thumb-to-index finger distance.

- When **one finger** is raised on the *trigger hand*:  
  - Move your **thumb and index finger** on the *measuring hand* closer or farther apart.  
  - The program measures the distance between these fingertips.  
  - This distance maps to a volume level from 0 to 100.  
  - The maximum distance corresponds roughly to **1/4 of the screen height** (the upper quarter of the webcam frame).  
  - Changing the distance adjusts the system volume accordingly.

- When **two fingers** are raised on the *trigger hand*:  
  - The program draws a Star of David symbol centered on the screen.  
  - The size of the star is based on the thumb-to-index finger distance on the measuring hand.  
  - The maximum size corresponds to about **1/4 of the screen height**.

- Press **`c`** to cycle through all connected webcams.

- Press **`q`** to quit the application.

---

## 📋 Requirements

Install required Python packages:

```bash
pip install -r requirements.txt

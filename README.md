<div align="center">

# 🚀 Assistive Communication System

A multi-modal assistive communication application designed to bridge communication gaps between blind, deaf, mute, and non-disabled users using Braille input, ASL recognition, and Text-to-Speech output.

</div>

---

<div align="center">
    
## 📌 Overview

</div>

Assistive Communication System is a Python-based application that combines multiple accessibility technologies into a single interface.

The project allows users to communicate through:

- 🟦 Text-to-Speech (TTS)
- ✋ American Sign Language (ASL) recognition
- ⠿ Braille keyboard input using a Raspberry Pi

All communication methods are converted into text and can then be spoken aloud using TTS output.

This project has:

- Real-time ASL hand tracking using MediaPipe
- Deep learning MLP classification with TensorFlow Keras
- Socket communication between Raspberry Pi and PC
- Accessibility-focused interface design
- Multi-modal communication integration
  
---

<div align="center">

## ✨ Key Features

</div>

- 🔊 Text-to-Speech conversion
- ✋ Real-time ASL alphabet recognition
- ⠿ Braille keyboard input support via Raspberry Pi
- 🖥 Centralized GUI built with CustomTkinter
- 🔗 Socket-based communication between devices
- 📷 Live webcam hand tracking using MediaPipe
- 🧠 TensorFlow-based sign classification model
- ⌨ Braille chorded keyboard input system

---

<div align="center">

## 🏗️ Modules

</div>

🔊 Text-to-Speech (TTS)
- Converts typed or generated text into spoken audio
- Acts as the final communication output for all modules

✋ ASL Recognition Module
- Detects ASL hand signs using webcam input
- Uses MediaPipe hand landmarks + TensorFlow model
- Converts detected signs into text, then TTS

Current Limitations
- T detection may be inaccurate due to fist orientation differences
- Motion-based letters (J and Z) are replaced with static image approximations
- D and Q are detected using the left hand instead of the right hand

⠿ Braille Module
- Raspberry Pi acts as the Braille sender
- PC application acts as the receiver
- Braille inputs are translated into text, then passed into TTS

Braille Keybinds
- Dots 2 3 4 → Left column
- Dots 5 6 7 → Right column
- 1 → Backspace
- Spacebar → Space
- 8 → Enter / Trigger TTS

<div align="center">

## 🔄 Communication Flow

</div>

Text Input
- Text → TTS

ASL Input
- Sign Language → Text → TTS

Braille Input
- Braille → Text → TTS

---
<div align="center">
  
## 🏗️ Tech Stack

</div>

- Language: Python
- GUI: CustomTkinter
- Computer Vision: OpenCV (cv2)
- Hand Tracking: MediaPipe
- Deep Learning: TensorFlow / Keras
- Hardware: Raspberry Pi
- Communication: Python Sockets
- 
---

<div align="center">

## ⚙️ Setup & Installation

</div>

1. Clone the repository:

    `git clone https://github.com/Soulstriderx/assistive-communication-system.git`

2. Install Python dependencies:
   
    `pip install customtkinter opencv-python numpy tensorflow mediapipe pillow paramiko pygame edge-tts`

3. Configure socket IP addresses in `./modules/braille_receiver.py` and `./for Pi/braille_sender.py` if needed

4. Install dependencies in Raspberry Pi (install evtest to test input/eventX):

    `sudo apt install python3-evdev`

5. Connect the Raspberry Pi to the same network as the PC

6. Run the application:
   
    `python main.py`

Note: You do not need the Raspberry Pi module if you do not have one, but its the only way to run the braille module.

---

<div align="center">

## 📊 How It Works

</div>

ASL Module
- Webcam captures live hand movement
- MediaPipe extracts hand landmarks
- TensorFlow model classifies the sign
- Detected letters are converted into text
- TTS outputs the generated sentence

Braille Module
- Raspberry Pi captures Braille key combinations
- Inputs are sent to the PC through sockets
- PC translates Braille patterns into text
- Generated text is spoken using TTS

TTS Module
- Receives text from manual typing, ASL, or Braille
- Converts text into audible speech output

---

<div align="center">

## 📷 Screenshots

</div>

<p align="center">
  <img src="https://i.imgur.com/jwM129r.png" width="45%"/>
  <img src="https://i.imgur.com/FctVnJA.png" width="45%"/>
</p>

Images show:
- The ASL Module
- Raspberry Pi Braille Module

---

<div align="center">

## 🚀 Future Improvements

</div>

- Improved ASL motion tracking for J and Z
- Better detection accuracy for similar hand signs
- Sentence prediction / autocomplete
- Support for additional sign languages
- Portable standalone deployment
- Wireless Braille keyboard support
- Speech-to-text integration

---

<div align="center">

## 👤 Author

</div>

Alex Sim  
GitHub: https://github.com/Soulstriderx

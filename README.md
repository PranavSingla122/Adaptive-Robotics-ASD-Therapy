# Adaptive Robotics for ASD Therapy

A low-cost, AI-driven therapeutic robotics platform designed to support motor skill development in children with Autism Spectrum Disorder (ASD). The system uses reinforcement learning, computer vision, and multisensory feedback to scaffold users through a structured three-phase learning workflow — progressing from full robot autonomy to full child control.

---

## Overview

Children with ASD interact with a small robotic car by performing hand gestures that correspond to real-world traffic signals (stop, forward, left, right, slow down). A Q-learning agent continuously monitors performance and dynamically blends system control with user input, transitioning phases as the child meets accuracy and anticipation thresholds.

The platform is designed for affordability and broad deployment — built entirely on commodity hardware (Raspberry Pi, Arduino, USB webcam) with a ~7 KB on-device gesture model.

---

## Features

- **Three-Phase Therapy Workflow** — Autonomous → Shared Control → Full User Control
- **Edge Gesture Recognition** — TensorFlow Lite model (6 classes, ~7 KB) with MediaPipe hand landmark pipeline
- **Adaptive RL Agent** — Q-learning dynamically adjusts autonomy level based on real-time reward signal
- **Traffic Light Integration** — TC3200 color sensor detects physical traffic signals; Arduino handles motor + LED responses
- **Fail-Safe Mode** — Falls back to rule-based gesture mapping if the TFLite model fails
- **Session Analytics** — Per-gesture accuracy, phase transition logs, anticipation rate, and learning curves exported to CSV/JSON

---

## System Architecture

```
┌──────────────────┐     Serial (115200)    ┌──────────────────────┐
│   Raspberry Pi   │ ─────────────────────► │   Arduino UNO/Nano   │
│                  │                        │                      │
│  • main.py       │                        │  • Motor control     │
│  • Gesture Engine│                        │  • LED feedback      │
│  • RL Agent      │                        │  • TC3200 sensor     │
│  • Data Logger   │                        │  • Buzzer / Vibration│
└──────────────────┘                        └──────────────────────┘
        ▲
        │ USB
┌───────┴──────┐
│  Logitech    │
│  C270 Webcam │
└──────────────┘
```

| Module | File | Responsibility |
|--------|------|----------------|
| Main Loop | `main.py` | Session management, phase execution, frame processing |
| Gesture Engine | `gesture_controller.py` | MediaPipe + TFLite inference pipeline |
| RL Agent | `reinforcement_learning.py` | Q-learning, reward calc, autonomy updates |
| Arduino Interface | `arduino_controller.py` | Serial comms, motor/LED/sensor control |
| Data Logger | `data_logger.py` | Per-attempt and session-level logging |
| Config | `config.py` | Hardware pins, thresholds, speed, camera settings |
| Traffic Detection | `traffic_light_detector.py` | HSV-based color classification |

---

## Recognized Gestures

| Gesture | Action |
|---------|--------|
| Open Palm | Stop |
| Index Finger Left | Turn Left |
| Index Finger Right | Turn Right |
| Thumbs Up | Move Forward |
| Thumbs Down | Slow Down |
| Other | Unknown (ignored) |

---

## Phase Progression

| Phase | Description | Transition Criteria |
|-------|-------------|---------------------|
| **Phase 1 — Autonomous** | Robot acts on traffic signals; child observes | Gesture accuracy ≥ 70% over 10 trials |
| **Phase 2 — Shared Control** | RL agent blends child gestures with autonomous logic | Accuracy ≥ 90% **and** anticipation rate ≥ 80% |
| **Phase 3 — Mastery** | Child has full control; system provides feedback only | — |

---

## Reward Function

```
r = 0.6 × Accuracy + 0.25 × Anticipation + 0.1 × ResponseTime − 0.15 × NoveltyPenalty
```

- **Accuracy** — Correct gesture classification rate
- **Anticipation** — Gesture issued before the traffic cue change (within 2 s)
- **Response Time** — Delay between cue onset and gesture
- **Novelty Penalty** — Applied when unrecognized gestures persist

---

## Hardware Requirements

| Component | Purpose |
|-----------|---------|
| Raspberry Pi (3B+ or 4) | Central compute — inference + RL |
| Arduino UNO / Nano | Motor driver + sensor interface |
| Logitech C270 Webcam | 640×480 gesture capture |
| TC3200 Color Sensor | Traffic light color detection |
| DC Motors + Motor Driver | Robot locomotion |
| RGB LEDs + Buzzer + Vibration Motor | Multisensory feedback |

---

## Software Requirements

```
Python 3.7+
opencv-python
mediapipe
tflite-runtime       # or tensorflow on non-Pi platforms
numpy
pyserial
```

Install dependencies:

```bash
pip install opencv-python mediapipe tflite-runtime numpy pyserial
```

> **Note:** On Raspberry Pi, install `tflite-runtime` from the official ARM wheel rather than full TensorFlow.

---

## Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/<your-username>/adaptive-robotics-asd-therapy.git
   cd adaptive-robotics-asd-therapy
   ```

2. **Connect hardware** — Raspberry Pi to Arduino via USB serial; webcam via USB.

3. **Configure settings** in `config.py`:
   - `ARDUINO_PORT` — typically `/dev/ttyUSB0` on Linux (auto-detected)
   - `CAMERA_INDEX` — `0` for the first USB webcam
   - Phase thresholds and speed settings as needed

4. **Run the system**
   ```bash
   python main.py
   ```

5. **Controls during session**
   - `q` — Quit and save session summary
   - `t` — Run hardware test (motors, LEDs, buzzer)

---

## Data Logging

Each session logs to CSV and JSON under `models/logs/session_logs/`:

**Per-attempt:**
- Timestamp, gesture attempted vs. correct, accuracy (bool), confidence score
- Response time, current phase, autonomy level, anticipation flag, traffic light state

**Session summary:**
- Total / correct attempts, overall accuracy, average response time
- Time in each phase, anticipation rate, trials to mastery per gesture
- Learning curve data, final autonomy level

---

## Project Structure

```
adaptive-robotics-asd-therapy/
├── main.py                    # Entry point
├── config.py                  # All configurable parameters
├── gesture_controller.py      # TFLite + MediaPipe gesture pipeline
├── arduino_controller.py      # Serial communication with Arduino
├── reinforcement_learning.py  # Q-learning agent
├── data_logger.py             # Session and attempt logging
├── traffic_light_detector.py  # HSV-based color detection
├── test.py                    # Hardware diagnostics
└── models/
    ├── gesture_classifier.tflite   # Quantized gesture model (~7 KB)
    └── logs/
        └── session_logs/           # Auto-generated session data
```

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Citation

If you use this system in research or clinical work, please cite:

```
Pranav Singla (2026). Adaptive Robotics for ASD Therapy: Structured Learning and Autonomy
Transition Using AI & Affordable Hardware.
```

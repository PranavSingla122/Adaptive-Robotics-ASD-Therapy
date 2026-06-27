# Camera Configuration
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
FPS = 30

# Arduino Configuration
ARDUINO_PORT = '/dev/ttyUSB0'  # Will auto-detect
ARDUINO_BAUDRATE = 115200

# Gesture Recognition Parameters
GESTURE_BUFFER_SIZE = 30
CONFIDENCE_THRESHOLD = 0.7
GESTURE_CLASSES = {
    0: "Stop",      # Fist
    1: "Forward",   # Thumbs up
    2: "Reverse",   # Thumbs down
    3: "Left",      # Index finger left
    4: "Right",     # Index finger right
    5: "Unknown"    # Any other gesture
}

# Speed Settings (m/s)
FULL_SPEED = 0.5
REDUCED_SPEED = 0.25
STOP_SPEED = 0.0

# RL Parameters
ACCURACY_WEIGHT = 0.6
ANTICIPATION_WEIGHT = 0.25
RESPONSE_TIME_WEIGHT = 0.1
NOVELTY_PENALTY = 0.15

# Phase Transition Thresholds
PHASE2_ACCURACY_THRESHOLD = 0.7
PHASE3_ACCURACY_THRESHOLD = 0.9
PHASE3_ANTICIPATION_THRESHOLD = 0.8
TRANSITION_TRIAL_COUNT = 10
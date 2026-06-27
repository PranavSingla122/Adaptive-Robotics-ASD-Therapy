import cv2
import numpy as np
import mediapipe as mp
import tensorflow as tf
from collections import deque
import time
import config

class GestureController:
    def __init__(self):
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        
        # Load TFLite model
        self.interpreter = tf.lite.Interpreter(
            model_path='models/gesture_classifier.tflite'
        )
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        
        # Frame buffer for stability
        self.frame_buffer = deque(maxlen=config.GESTURE_BUFFER_SIZE)
        self.last_gesture_time = time.time()
        self.last_stable_gesture = None
        
    def preprocess_landmarks(self, landmarks):
        """Convert landmarks to model input"""
        coords = []
        base_x = landmarks[0].x
        base_y = landmarks[0].y
        
        for landmark in landmarks:
            coords.append(landmark.x - base_x)
            coords.append(landmark.y - base_y)
            
        return np.array(coords, dtype=np.float32)
        
    def classify_gesture(self, landmarks):
        """Classify gesture using TFLite model"""
        input_data = self.preprocess_landmarks(landmarks)
        input_data = np.expand_dims(input_data, axis=0)
        
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        gesture_id = np.argmax(output_data[0])
        confidence = float(output_data[0][gesture_id])
        
        gesture_name = config.GESTURE_CLASSES.get(gesture_id, "unknown")
        
        # Filter low confidence
        if confidence < config.CONFIDENCE_THRESHOLD or gesture_id not in config.GESTURE_CLASSES:
            gesture_name = "unknown"
            gesture_id = 5
            
        return {
            'gesture': gesture_name,
            'gesture_id': gesture_id,
            'confidence': confidence
        }
        
    def get_stable_gesture(self):
        """Analyze buffer for stable gesture"""
        if len(self.frame_buffer) < config.GESTURE_BUFFER_SIZE:
            return None
            
        gesture_counts = {}
        total_confidence = {}
        
        for result in self.frame_buffer:
            if result is not None:
                gesture = result['gesture']
                if gesture not in gesture_counts:
                    gesture_counts[gesture] = 0
                    total_confidence[gesture] = 0
                gesture_counts[gesture] += 1
                total_confidence[gesture] += result['confidence']
                
        if not gesture_counts:
            return None
            
        most_common_gesture = max(gesture_counts, key=gesture_counts.get)
        occurrence_ratio = gesture_counts[most_common_gesture] / len(self.frame_buffer)
        
        # Require 60% of frames to have same gesture
        if occurrence_ratio >= 0.6:
            avg_confidence = total_confidence[most_common_gesture] / gesture_counts[most_common_gesture]
            response_time = time.time() - self.last_gesture_time
            
            return {
                'gesture': most_common_gesture,
                'confidence': avg_confidence,
                'stability': occurrence_ratio,
                'response_time': response_time
            }
            
        return None
        
    def process_frame(self, frame):
        """Process single frame for gesture recognition"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        gesture_result = None
        
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            
            # Draw landmarks
            self.mp_drawing.draw_landmarks(
                frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
            )
            
            # Classify gesture
            gesture_result = self.classify_gesture(hand_landmarks.landmark)
            
            # Add to buffer
            self.frame_buffer.append(gesture_result)
        else:
            # No hand detected
            self.frame_buffer.append(None)
            
        # Get stable gesture from buffer
        stable_gesture = self.get_stable_gesture()
        
        if stable_gesture and stable_gesture['gesture'] != self.last_stable_gesture:
            self.last_stable_gesture = stable_gesture['gesture']
            self.last_gesture_time = time.time()
            return stable_gesture
            
        return None
        
    def cleanup(self):
        """Clean up resources"""
        self.hands.close()
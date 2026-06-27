#!/usr/bin/env python3
import cv2
import numpy as np
import time
import signal
import sys
from datetime import datetime

from gesture_controller import GestureController
from arduino_controller import ArduinoController
from reinforcement_learning import RLAgent
from data_logger import DataLogger
import config

class ASDTherapyCar:
    def __init__(self):
        # Initialize components
        print("Initializing ASD Therapy Car System...")
        
        # Arduino controls all hardware
        self.arduino = ArduinoController()
        self.gesture_controller = GestureController()
        self.rl_agent = RLAgent()
        self.data_logger = DataLogger()
        
        # Camera setup
        self.cap = cv2.VideoCapture(config.CAMERA_INDEX)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, config.FPS)
        
        # System state
        self.running = True
        self.current_phase = 1
        self.autonomy_level = 0.0
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Metrics tracking
        self.gesture_attempts = []
        self.correct_attempts = 0
        self.total_attempts = 0
        self.anticipation_count = 0
        self.phase_start_time = time.time()
        
        # Traffic light state
        self.current_traffic_light = "green"
        self.last_traffic_light_change = time.time()
        
        # Enable auto traffic light detection
        self.arduino.enable_auto_detection(self.on_traffic_light_change)
        
        # Signal handling
        signal.signal(signal.SIGINT, self.signal_handler)
        
        print("System initialized successfully!")
        
    def on_traffic_light_change(self, color):
        """Callback for traffic light changes"""
        if color != self.current_traffic_light:
            print(f"Traffic light changed: {self.current_traffic_light} → {color}")
            self.current_traffic_light = color
            self.last_traffic_light_change = time.time()
            
    def signal_handler(self, sig, frame):
        """Handle cleanup on exit"""
        print("\nShutting down...")
        self.cleanup()
        sys.exit(0)
        
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        self.arduino.cleanup()
        self.cap.release()
        cv2.destroyAllWindows()
        
        # Save session summary
        self.data_logger.save_session_summary(
            session_id=self.session_id,
            total_attempts=self.total_attempts,
            correct_attempts=self.correct_attempts,
            phase_times={
                1: self.phase_start_time if self.current_phase == 1 else 0,
                2: 0,
                3: 0
            },
            final_autonomy=self.autonomy_level
        )
        
    def phase1_autonomous(self):
        """Phase 1: Full autonomous control based on traffic lights"""
        # Control car based on traffic light
        if self.current_traffic_light == "red":
            self.arduino.stop()
            self.arduino.set_led_color("red")
        elif self.current_traffic_light == "yellow":
            self.arduino.set_speed(config.REDUCED_SPEED)
            self.arduino.set_led_color("yellow")
        else:  # green
            self.arduino.forward(config.FULL_SPEED)
            self.arduino.set_led_color("green")
            
    def phase2_shared_control(self, gesture_result):
        """Phase 2: Blend autonomous and gesture control"""
        if gesture_result and gesture_result['gesture'] != 'unknown':
            # Check if gesture matches expected action
            expected_action = self.get_expected_action(self.current_traffic_light)
            is_correct = gesture_result['gesture'] == expected_action
            
            # Log attempt
            self.log_gesture_attempt(
                gesture_result['gesture'],
                expected_action,
                is_correct,
                gesture_result['confidence']
            )
            
            # Blend control based on autonomy level
            if is_correct:
                # Execute gesture with weighted autonomy
                self.execute_gesture_with_autonomy(
                    gesture_result['gesture'],
                    self.autonomy_level
                )
                self.arduino.set_led_color("green")
            else:
                # Incorrect - maintain autonomous control
                self.phase1_autonomous()
                self.arduino.set_led_color("red")
                
            # Update RL agent
            self.update_rl_agent(is_correct, gesture_result['response_time'])
        else:
            # No gesture - maintain autonomous control
            self.phase1_autonomous()
            
    def phase3_full_control(self, gesture_result):
        """Phase 3: Full child control"""
        if gesture_result and gesture_result['gesture'] != 'unknown':
            # Execute gesture directly
            self.execute_gesture(gesture_result['gesture'])
            
            # Check if gesture matches traffic light
            expected_action = self.get_expected_action(self.current_traffic_light)
            is_correct = gesture_result['gesture'] == expected_action
            
            # Check for anticipation
            is_anticipation = self.check_anticipation(
                gesture_result['gesture'],
                self.current_traffic_light
            )
            
            # Log attempt
            self.log_gesture_attempt(
                gesture_result['gesture'],
                expected_action,
                is_correct,
                gesture_result['confidence'],
                is_anticipation
            )
            
            # Provide feedback
            if is_correct:
                self.arduino.set_led_color("green")
            else:
                self.arduino.set_led_color("blue")
                
    def get_expected_action(self, traffic_light):
        """Get expected gesture based on traffic light"""
        if traffic_light == "red":
            return "stop"
        elif traffic_light == "yellow":
            return "stop"  # Conservative for safety
        else:
            return "forward"
            
    def check_anticipation(self, gesture, traffic_light):
        """Check if child anticipated traffic light change"""
        time_since_change = time.time() - self.last_traffic_light_change
        if time_since_change < 2.0:  # Within 2 seconds of change
            if (traffic_light == "red" and gesture == "stop") or \
               (traffic_light == "green" and gesture == "forward"):
                self.anticipation_count += 1
                return True
        return False
        
    def execute_gesture(self, gesture):
        """Execute gesture command"""
        if gesture == "stop":
            self.arduino.stop()
        elif gesture == "forward":
            self.arduino.forward(config.FULL_SPEED)
        elif gesture == "reverse":
            self.arduino.reverse(config.REDUCED_SPEED)
        elif gesture == "left":
            self.arduino.turn_left()
        elif gesture == "right":
            self.arduino.turn_right()
            
    def execute_gesture_with_autonomy(self, gesture, autonomy_level):
        """Execute gesture with weighted autonomy"""
        weight = autonomy_level
        if gesture == "forward" and self.current_traffic_light == "green":
            self.arduino.forward(config.FULL_SPEED * weight)
        elif gesture == "stop":
            self.arduino.stop()
        else:
            self.execute_gesture(gesture)
            
    def log_gesture_attempt(self, gesture, expected, is_correct, confidence, 
                           is_anticipation=False):
        """Log gesture attempt data"""
        attempt_data = {
            'timestamp': datetime.now().isoformat(),
            'gesture_attempted': gesture,
            'correct_gesture': expected,
            'accuracy': is_correct,
            'confidence': confidence,
            'response_time': time.time() - self.last_traffic_light_change,
            'current_phase': self.current_phase,
            'autonomy_level': self.autonomy_level,
            'anticipation': is_anticipation,
            'traffic_light_state': self.current_traffic_light
        }
        
        self.gesture_attempts.append(attempt_data)
        self.data_logger.log_attempt(self.session_id, attempt_data)
        
        # Update metrics
        self.total_attempts += 1
        if is_correct:
            self.correct_attempts += 1
            
    def update_rl_agent(self, is_correct, response_time):
        """Update RL agent and check for phase transition"""
        # Calculate current metrics
        accuracy = self.correct_attempts / max(self.total_attempts, 1)
        anticipation_rate = self.anticipation_count / max(self.total_attempts, 1)
        
        # Update RL agent
        reward = self.rl_agent.calculate_reward(
            accuracy=accuracy,
            anticipation=anticipation_rate,
            response_time=response_time,
            novelty=0
        )
        
        self.autonomy_level = self.rl_agent.update_autonomy(reward, self.current_phase)
        
        # Check for phase transition
        if self.current_phase == 1 and accuracy >= config.PHASE2_ACCURACY_THRESHOLD:
            if len(self.gesture_attempts) >= config.TRANSITION_TRIAL_COUNT:
                self.current_phase = 2
                self.phase_start_time = time.time()
                print(f"Transitioning to Phase 2! Accuracy: {accuracy:.2%}")
                
        elif self.current_phase == 2:
            recent_attempts = self.gesture_attempts[-config.TRANSITION_TRIAL_COUNT:]
            recent_accuracy = sum(1 for a in recent_attempts if a['accuracy']) / len(recent_attempts)
            
            if recent_accuracy >= config.PHASE3_ACCURACY_THRESHOLD and \
               anticipation_rate >= config.PHASE3_ANTICIPATION_THRESHOLD:
                self.current_phase = 3
                self.autonomy_level = 1.0
                self.phase_start_time = time.time()
                print(f"Transitioning to Phase 3! Full control enabled!")
                
    def run(self):
        """Main application loop"""
        print(f"\nStarting ASD Therapy Car - Session: {self.session_id}")
        print(f"Phase: {self.current_phase}")
        print("Press 'q' to quit, 't' to test hardware\n")
        
        frame_count = 0
        fps_start_time = time.time()
        
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to capture frame")
                continue
                
            # Process gesture recognition
            gesture_result = self.gesture_controller.process_frame(frame)
            
            # Execute phase-specific control
            if self.current_phase == 1:
                self.phase1_autonomous()
            elif self.current_phase == 2:
                self.phase2_shared_control(gesture_result)
            else:  # Phase 3
                self.phase3_full_control(gesture_result)
                
            # Display debug information
            self.display_debug_info(frame, gesture_result)
            
            # Calculate FPS
            frame_count += 1
            if frame_count % 30 == 0:
                fps = 30 / (time.time() - fps_start_time)
                fps_start_time = time.time()
                
            # Show frame
            cv2.imshow('ASD Therapy Car', frame)
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('t'):
                print("Running hardware test...")
                self.arduino.test_hardware()
                
        self.cleanup()
        
    def display_debug_info(self, frame, gesture_result):
        """Overlay debug information on frame"""
        info_text = [
            f"Phase: {self.current_phase}",
            f"Autonomy: {self.autonomy_level:.2f}",
            f"Accuracy: {self.correct_attempts}/{self.total_attempts}",
            f"Traffic Light: {self.current_traffic_light}"
        ]
        
        if gesture_result:
            info_text.append(f"Gesture: {gesture_result['gesture']} ({gesture_result['confidence']:.2f})")
            
        # Draw background rectangle
        cv2.rectangle(frame, (0, 0), (300, len(info_text) * 30 + 10), (0, 0, 0), -1)
        
        # Draw text
        y_offset = 25
        for text in info_text:
            cv2.putText(frame, text, (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            y_offset += 30

if __name__ == "__main__":
    car = ASDTherapyCar()
    car.run()
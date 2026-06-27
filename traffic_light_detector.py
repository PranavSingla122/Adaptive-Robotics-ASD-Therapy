import cv2
import numpy as np
import RPi.GPIO as GPIO
import config

class TrafficLightDetector:
    def __init__(self):
        # Initialize color sensor pins
        GPIO.setup(config.S0, GPIO.OUT)
        GPIO.setup(config.S1, GPIO.OUT)
        GPIO.setup(config.S2, GPIO.OUT)
        GPIO.setup(config.S3, GPIO.OUT)
        GPIO.setup(config.OUT, GPIO.IN)
        
        # Set frequency scaling to 20%
        GPIO.output(config.S0, GPIO.HIGH)
        GPIO.output(config.S1, GPIO.LOW)
        
        self.last_detection = "green"
        
    def read_color_sensor(self):
        """Read RGB values from TCS3200 color sensor"""
        # Read red
        GPIO.output(config.S2, GPIO.LOW)
        GPIO.output(config.S3, GPIO.LOW)
        red = self.count_pulses()
        
        # Read green
        GPIO.output(config.S2, GPIO.HIGH)
        GPIO.output(config.S3, GPIO.HIGH)
        green = self.count_pulses()
        
        # Read blue
        GPIO.output(config.S2, GPIO.LOW)
        GPIO.output(config.S3, GPIO.HIGH)
        blue = self.count_pulses()
        
        return red, green, blue
        
    def count_pulses(self, duration=0.1):
        """Count pulses from color sensor"""
        pulse_count = 0
        start_time = time.time()
        
        while (time.time() - start_time) < duration:
            if GPIO.input(config.OUT) == GPIO.HIGH:
                pulse_count += 1
                while GPIO.input(config.OUT) == GPIO.HIGH:
                    pass
                    
        return pulse_count
        
    def detect_from_sensor(self):
        """Detect traffic light color from hardware sensor"""
        red, green, blue = self.read_color_sensor()
        
        # Normalize values
        total = red + green + blue
        if total == 0:
            return self.last_detection
            
        red_ratio = red / total
        green_ratio = green / total
        
        # Determine color based on ratios
        if red_ratio > 0.5:
            return "red"
        elif green_ratio > 0.4:
            return "green"
        elif red_ratio > 0.3 and green_ratio > 0.3:
            return "yellow"
        else:
            return self.last_detection
            
    def detect_from_camera(self, frame):
        """Detect traffic light from camera image (backup method)"""
        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Create masks for each color
        red_mask1 = cv2.inRange(hsv, config.RED_LOWER, config.RED_UPPER)
        red_mask2 = cv2.inRange(hsv, config.RED_LOWER2, config.RED_UPPER2)
        red_mask = red_mask1 + red_mask2
        
        yellow_mask = cv2.inRange(hsv, config.YELLOW_LOWER, config.YELLOW_UPPER)
        green_mask = cv2.inRange(hsv, config.GREEN_LOWER, config.GREEN_UPPER)
        
        # Count pixels for each color
        red_pixels = cv2.countNonZero(red_mask)
        yellow_pixels = cv2.countNonZero(yellow_mask)
        green_pixels = cv2.countNonZero(green_mask)
        
        # Determine dominant color
        max_pixels = max(red_pixels, yellow_pixels, green_pixels)
        
        if max_pixels < 100:  # Threshold for minimum detection
            return self.last_detection
            
        if red_pixels == max_pixels:
            return "red"
        elif yellow_pixels == max_pixels:
            return "yellow"
        else:
            return "green"
            
    def detect(self, frame):
        """Main detection method - tries sensor first, then camera"""
        try:
            # Try hardware sensor first
            detection = self.detect_from_sensor()
        except:
            # Fallback to camera detection
            detection = self.detect_from_camera(frame)
            
        self.last_detection = detection
        return detection
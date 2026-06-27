import serial
import time
import threading
import queue
import config

class ArduinoController:
    """Unified controller for all Arduino-connected hardware"""
    
    def __init__(self, port=config.ARDUINO_PORT, baudrate=config.ARDUINO_BAUDRATE):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.connected = False
        
        # Command queue
        self.command_queue = queue.Queue()
        
        # State tracking
        self.current_speed = 0
        self.current_direction = "stop"
        self.current_led_color = "off"
        self.current_traffic_light = "green"
        self.auto_color_detection = False
        
        # Thread management
        self.comm_thread = None
        self.running = True
        
        # Callbacks for traffic light changes
        self.traffic_light_callback = None
        
        self.connect()
        
    def connect(self):
        """Connect to Arduino"""
        ports_to_try = ['/dev/ttyUSB0', '/dev/ttyACM0', '/dev/ttyUSB1', '/dev/ttyACM1']
        
        for port in ports_to_try:
            try:
                self.serial_conn = serial.Serial(port, self.baudrate, timeout=1)
                self.port = port
                print(f"Connected to Arduino on {port}")
                break
            except:
                continue
                
        if not self.serial_conn:
            raise Exception("Arduino not found on any port")
            
        time.sleep(2)  # Arduino reset time
        self.serial_conn.flushInput()
        
        # Test connection
        self.serial_conn.write(b"PING:0\n")
        time.sleep(0.1)
        
        response = self.serial_conn.readline().decode().strip()
        if response == "PONG":
            self.connected = True
            print("Arduino communication established")
            
            # Start communication thread
            self.comm_thread = threading.Thread(target=self._communication_loop)
            self.comm_thread.daemon = True
            self.comm_thread.start()
        else:
            raise Exception("Arduino not responding")
            
    def _communication_loop(self):
        """Background communication thread"""
        while self.running and self.connected:
            try:
                # Send queued commands
                while not self.command_queue.empty():
                    cmd = self.command_queue.get()
                    self.serial_conn.write(cmd.encode() + b'\n')
                    
                # Read responses
                if self.serial_conn.in_waiting > 0:
                    response = self.serial_conn.readline().decode().strip()
                    if response:
                        self._handle_response(response)
                        
                time.sleep(0.01)
                
            except Exception as e:
                print(f"Communication error: {e}")
                self.connected = False
                
    def _handle_response(self, response):
        """Handle Arduino responses"""
        if response.startswith("OK:"):
            # Command acknowledged
            pass
        elif response.startswith("ERROR:"):
            print(f"Arduino Error: {response}")
        elif response.startswith("LIGHT:"):
            # Traffic light change detected
            color = response.split(":")[1].lower()
            self.current_traffic_light = color
            if self.traffic_light_callback:
                self.traffic_light_callback(color)
        elif response.startswith("COLOR:"):
            # Color sensor reading
            color = response.split(":")[1].lower()
            self.current_traffic_light = color
        elif response.startswith("TEST:"):
            print(f"Test: {response}")
        else:
            # Debug output
            print(f"Arduino: {response}")
            
    def send_command(self, command):
        """Queue command for Arduino"""
        if self.connected:
            self.command_queue.put(command)
            
    # Motor control methods
    def set_motor_speed(self, speed_mps):
        """Convert m/s to PWM (0-255)"""
        pwm = int(min(255, (speed_mps / 1.0) * 255))
        return max(0, pwm)
        
    def stop(self):
        """Stop all motors"""
        self.send_command("S:0")
        self.current_speed = 0
        self.current_direction = "stop"
        
    def forward(self, speed_mps):
        """Move forward"""
        pwm = self.set_motor_speed(speed_mps)
        self.send_command(f"F:{pwm}")
        self.current_speed = speed_mps
        self.current_direction = "forward"
        
    def reverse(self, speed_mps):
        """Move backward"""
        pwm = self.set_motor_speed(speed_mps)
        self.send_command(f"B:{pwm}")
        self.current_speed = speed_mps
        self.current_direction = "reverse"
        
    def turn_left(self):
        """Turn left"""
        self.send_command("L:128")
        self.current_direction = "left"
        
    def turn_right(self):
        """Turn right"""
        self.send_command("R:128")
        self.current_direction = "right"
        
    def set_speed(self, speed_mps):
        """Adjust speed maintaining direction"""
        if self.current_direction == "forward":
            self.forward(speed_mps)
        elif self.current_direction == "reverse":
            self.reverse(speed_mps)
            
    # LED control methods
    def set_led_color(self, color):
        """Set LED color"""
        color_map = {
            'red': 'R',
            'green': 'G',
            'blue': 'B',
            'yellow': 'Y',
            'off': 'OFF'
        }
        
        if color in color_map:
            self.send_command(f"LED:{color_map[color]}")
            self.current_led_color = color
            
    def led_off(self):
        """Turn off LED"""
        self.set_led_color('off')
        
    # Color sensor methods
    def get_traffic_light(self):
        """Get current traffic light reading"""
        self.send_command("COLOR:GET")
        time.sleep(0.1)
        return self.current_traffic_light
        
    def enable_auto_detection(self, callback=None):
        """Enable automatic traffic light detection"""
        self.traffic_light_callback = callback
        self.send_command("COLOR:AUTO")
        self.auto_color_detection = True
        
    def disable_auto_detection(self):
        """Disable automatic traffic light detection"""
        self.send_command("COLOR:STOP")
        self.auto_color_detection = False
        
    # System methods
    def test_hardware(self):
        """Run hardware test"""
        self.send_command("TEST:0")
        
    def get_status(self):
        """Get system status"""
        self.send_command("STATUS:0")
        
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        self.stop()
        self.led_off()
        
        if self.comm_thread:
            self.comm_thread.join(timeout=1)
            
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            
        print("Arduino controller cleaned up")
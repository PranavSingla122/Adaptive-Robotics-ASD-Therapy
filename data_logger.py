import json
import csv
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

class DataLogger:
    def __init__(self):
        self.log_dir = "logs/session_logs"
        os.makedirs(self.log_dir, exist_ok=True)
        
    def log_attempt(self, session_id, attempt_data):
        """Log individual gesture attempt"""
        log_file = os.path.join(self.log_dir, f"{session_id}_attempts.csv")
        
        file_exists = os.path.exists(log_file)
        
        with open(log_file, 'a', newline='') as f:
            fieldnames = [
                'timestamp', 'gesture_attempted', 'correct_gesture', 
                'accuracy', 'confidence', 'response_time', 'current_phase',
                'autonomy_level', 'anticipation', 'traffic_light_state'
            ]
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
                
            writer.writerow(attempt_data)
            
    def save_session_summary(self, session_id, total_attempts, correct_attempts,
                           phase_times, final_autonomy):
        """Save session summary"""
        summary_file = os.path.join(self.log_dir, f"{session_id}_summary.json")
        
        attempts_df = self.load_attempts(session_id)
        
        summary_data = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'total_attempts': total_attempts,
            'correct_attempts': correct_attempts,
            'overall_accuracy': correct_attempts / max(total_attempts, 1),
            'average_response_time': attempts_df['response_time'].mean() if len(attempts_df) > 0 else 0,
            'phase_times': phase_times,
            'anticipation_rate': attempts_df['anticipation'].mean() if len(attempts_df) > 0 else 0,
            'final_autonomy_level': final_autonomy,
            'gestures_summary': self.get_gesture_summary(attempts_df)
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary_data, f, indent=2)
            
        self.generate_session_plots(session_id, attempts_df)
        
    def load_attempts(self, session_id):
        """Load attempt data"""
        log_file = os.path.join(self.log_dir, f"{session_id}_attempts.csv")
        
        if os.path.exists(log_file):
            return pd.read_csv(log_file)
        else:
            return pd.DataFrame()
            
    def get_gesture_summary(self, df):
        """Get summary statistics for each gesture"""
        if len(df) == 0:
            return {}
            
        summary = {}
        gestures = ['stop', 'forward', 'reverse', 'left', 'right']
        
        for gesture in gestures:
            gesture_df = df[df['gesture_attempted'] == gesture]
            if len(gesture_df) > 0:
                summary[gesture] = {
                    'attempts': len(gesture_df),
                    'correct': len(gesture_df[gesture_df['accuracy'] == True]),
                    'accuracy': len(gesture_df[gesture_df['accuracy'] == True]) / len(gesture_df),
                    'avg_confidence': gesture_df['confidence'].mean(),
                    'avg_response_time': gesture_df['response_time'].mean()
                }
                
        return summary
        
    def generate_session_plots(self, session_id, df):
        """Generate visualization plots"""
        if len(df) == 0:
            return
            
        plot_dir = os.path.join(self.log_dir, f"{session_id}_plots")
        os.makedirs(plot_dir, exist_ok=True)
        
        # 1. Learning curve
        plt.figure(figsize=(10, 6))
        df['cumulative_accuracy'] = df['accuracy'].expanding().mean()
        plt.plot(df.index, df['cumulative_accuracy'], 'b-', linewidth=2)
        plt.xlabel('Attempt Number')
        plt.ylabel('Cumulative Accuracy')
        plt.title('Learning Curve')
        plt.grid(True, alpha=0.3)
        plt.savefig(os.path.join(plot_dir, 'learning_curve.png'))
        plt.close()
        
        # 2. Response time trend
        plt.figure(figsize=(10, 6))
        plt.scatter(df.index, df['response_time'], alpha=0.6)
        if len(df) > 10:
            plt.plot(df.index, df['response_time'].rolling(10).mean(), 'r-', linewidth=2)
        plt.xlabel('Attempt Number')
        plt.ylabel('Response Time (seconds)')
        plt.title('Response Time Trend')
        plt.grid(True, alpha=0.3)
        plt.savefig(os.path.join(plot_dir, 'response_time.png'))
        plt.close()
        
        print(f"Session plots saved to: {plot_dir}")
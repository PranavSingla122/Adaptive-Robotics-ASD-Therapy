import numpy as np
import json
import os
import config

class RLAgent:
    def __init__(self):
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        self.exploration_rate = 0.1
        
        # State representation
        self.state_size = 5
        self.action_size = 10  # Discretized autonomy levels
        
        # Q-table
        self.q_table = self.load_q_table()
        
        # Current state
        self.current_state = None
        self.last_action = None
        
    def load_q_table(self):
        """Load or initialize Q-table"""
        q_table_path = 'models/q_table.npy'
        if os.path.exists(q_table_path):
            return np.load(q_table_path)
        else:
            os.makedirs('models', exist_ok=True)
            return np.random.uniform(low=0, high=0.01, size=(100, self.action_size))
            
    def save_q_table(self):
        """Save Q-table"""
        np.save('models/q_table.npy', self.q_table)
        
    def get_state_index(self, phase, accuracy, anticipation, response_time):
        """Convert continuous state to discrete index"""
        phase_idx = phase - 1
        accuracy_idx = min(int(accuracy * 10), 9)
        anticipation_idx = min(int(anticipation * 10), 9)
        response_idx = min(int(response_time / 0.5), 4)
        
        state_idx = (phase_idx * 1000 + accuracy_idx * 100 + 
                    anticipation_idx * 10 + response_idx)
        
        return min(state_idx, 99)
        
    def calculate_reward(self, accuracy, anticipation, response_time, novelty):
        """Calculate reward based on performance"""
        reward = (config.ACCURACY_WEIGHT * accuracy +
                 config.ANTICIPATION_WEIGHT * anticipation +
                 config.RESPONSE_TIME_WEIGHT * (1.0 / (1.0 + response_time)) -
                 config.NOVELTY_PENALTY * novelty)
        return reward
        
    def select_action(self, state_idx):
        """Select action using epsilon-greedy policy"""
        if np.random.rand() < self.exploration_rate:
            return np.random.randint(self.action_size)
        else:
            return np.argmax(self.q_table[state_idx])
            
    def update_autonomy(self, reward, phase):
        """Update autonomy level based on RL policy"""
        if phase == 1:
            return 0.0
        elif phase == 3:
            return 1.0
        else:
            # Phase 2: Adaptive autonomy
            if self.current_state is not None and self.last_action is not None:
                # Update Q-table
                next_state = self.get_state_index(
                    phase,
                    reward * config.ACCURACY_WEIGHT,
                    reward * config.ANTICIPATION_WEIGHT,
                    1.0
                )
                
                best_next_action = np.argmax(self.q_table[next_state])
                td_target = reward + self.discount_factor * self.q_table[next_state][best_next_action]
                td_error = td_target - self.q_table[self.current_state][self.last_action]
                
                self.q_table[self.current_state][self.last_action] += self.learning_rate * td_error
                
                # Save periodically
                if np.random.rand() < 0.01:
                    self.save_q_table()
                    
            # Select new action
            state_idx = self.get_state_index(phase, reward, 0, 1.0)
            action = self.select_action(state_idx)
            
            self.current_state = state_idx
            self.last_action = action
            
            # Convert action to autonomy level
            autonomy = action / (self.action_size - 1)
            return autonomy
            
    def decay_exploration(self):
        """Decay exploration rate"""
        self.exploration_rate = max(0.01, self.exploration_rate * 0.995)
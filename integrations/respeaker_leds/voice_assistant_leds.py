"""
LED patterns for voice assistant interactions with ReSpeaker
"""

import time
import threading
import sys
import os

# Flag to track if LED functionality is available
LEDS_AVAILABLE = False

try:
    # Try to import the pixels module
    from .pixels import pixels
    LEDS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: LED functionality not available: {e}")
    print("Voice assistant will run without LED feedback.")

class VoiceAssistantLEDs:
    """
    Manages LED patterns for voice assistant interactions
    """
    def __init__(self):
        self.is_initialized = False
        self.current_state = "off"
        self._initialize()
        
    def _initialize(self):
        """Initialize the LED controller"""
        if not LEDS_AVAILABLE:
            print("LED controller not available - running in LED-less mode")
            return
            
        try:
            # Turn off LEDs initially
            pixels.off()
            self.is_initialized = True
            print("LED controller initialized successfully")
        except Exception as e:
            print(f"Error initializing LED controller: {e}")
            self.is_initialized = False
    
    def recording_on(self):
        """Turn on recording mode LEDs - red pattern"""
        if not self.is_initialized or not LEDS_AVAILABLE:
            return
            
        try:
            self.current_state = "recording"
            pixels.listen()  # Use the built-in listen pattern (red)
            print("Recording LEDs activated")
        except Exception as e:
            print(f"Error activating recording LEDs: {e}")
    
    def recording_off(self):
        """Turn off recording LEDs"""
        if not self.is_initialized or not LEDS_AVAILABLE:
            return
            
        try:
            self.current_state = "off"
            pixels.off()
            print("Recording LEDs deactivated")
        except Exception as e:
            print(f"Error deactivating recording LEDs: {e}")
    
    def thinking(self):
        """Show thinking pattern while processing"""
        if not self.is_initialized or not LEDS_AVAILABLE:
            return
            
        try:
            self.current_state = "thinking"
            pixels.think()  # Use the built-in think pattern (spinning blue)
            print("Thinking LEDs activated")
        except Exception as e:
            print(f"Error activating thinking LEDs: {e}")
    
    def speaking(self):
        """Show speaking pattern while AI is responding"""
        if not self.is_initialized or not LEDS_AVAILABLE:
            return
            
        try:
            self.current_state = "speaking"
            pixels.speak()  # Use the built-in speak pattern (pulsing green)
            print("Speaking LEDs activated")
        except Exception as e:
            print(f"Error activating speaking LEDs: {e}")
    
    def error(self):
        """Show error pattern"""
        if not self.is_initialized or not LEDS_AVAILABLE:
            return
            
        try:
            # Flash red 3 times to indicate error
            self.current_state = "error"
            for _ in range(3):
                pixels.listen()  # Red
                time.sleep(0.2)
                pixels.off()
                time.sleep(0.2)
            print("Error LEDs activated")
        except Exception as e:
            print(f"Error activating error LEDs: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        if not self.is_initialized or not LEDS_AVAILABLE:
            return
            
        try:
            pixels.off()
            print("LED controller cleaned up")
        except Exception as e:
            print(f"Error cleaning up LED controller: {e}")

# Create a singleton instance
voice_leds = VoiceAssistantLEDs()

if __name__ == "__main__":
    # Test LED patterns
    try:
        print("Testing LED patterns...")
        voice_leds.recording_on()
        time.sleep(3)
        voice_leds.recording_off()
        time.sleep(1)
        voice_leds.thinking()
        time.sleep(3)
        voice_leds.speaking()
        time.sleep(3)
        voice_leds.error()
        time.sleep(1)
        voice_leds.cleanup()
    except KeyboardInterrupt:
        voice_leds.cleanup()
        print("LED test interrupted")

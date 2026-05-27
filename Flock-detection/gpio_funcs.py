#NOT YET IMPLEMENTED INTO RPI
# PHYSICAL ALERTS (GPIO)
import os
import sys
import time
import argparse
import threading
import subprocess
import json
import csv
from datetime import datetime
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

def setup_gpio(state, GPIO_AVAILABLE):
    if not GPIO_AVAILABLE:
        return
    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(state["buzzer_pin"], GPIO.OUT)
        GPIO.setup(state["led_pin"], GPIO.OUT)
        GPIO.output(state["buzzer_pin"], GPIO.LOW)
        GPIO.output(state["led_pin"], GPIO.LOW)
    except Exception as e:
        print(f"[*] GPIO Initialization failed (Are you running on non-Pi device?): {e}")

def trigger_alert(state, GPIO_AVAILABLE, duration=0.15, frequency=2):
    """Flashes LED and chirps buzzer when a target is detected."""
    if not GPIO_AVAILABLE:
        # Fallback terminal beep
        sys.stdout.write("\a")
        sys.stdout.flush()
        return

    def alert_thread():
        try:
            for _ in range(frequency):
                GPIO.output(state["led_pin"], GPIO.HIGH)
                GPIO.output(state["buzzer_pin"], GPIO.HIGH)
                time.sleep(duration)
                GPIO.output(state["led_pin"], GPIO.LOW)
                GPIO.output(state["buzzer_pin"], GPIO.LOW)
                time.sleep(0.08)
        except Exception:
            pass

    threading.Thread(target=alert_thread, daemon=True).start()
import json
import sys
import time
import pigpio

# Load configuration
with open('config.json', 'r') as f:
    CONFIG = json.load(f)

RX_GPIO = CONFIG['gpio']['ir_receive']
GLITCH = 100
POST_MS = CONFIG['ir']['gap_ms']

pi = pigpio.pi()
if not pi.connected:
    print("Could not connect to pigpiod. Is it running?")
    exit(1)

pi.set_mode(RX_GPIO, pigpio.INPUT)
pi.set_glitch_filter(RX_GPIO, GLITCH)

last_tick = None
pulses = []

def callback(gpio, level, tick):
    global last_tick, pulses
    if last_tick is not None:
        diff = pigpio.tickDiff(last_tick, tick)
        pulses.append(diff)
    last_tick = tick

def record_code(name):
    global pulses, last_tick
    print(f"Recording code for '{name}'...")
    print("Press the button on your remote now.")
    
    pulses = []
    last_tick = None
    cb = pi.callback(RX_GPIO, pigpio.EITHER_EDGE, callback)
    
    start_time = time.time()
    while True:
        if last_tick is not None:
            # Check if we haven't seen a pulse for a while
            if pigpio.tickDiff(last_tick, pi.get_current_tick()) > POST_MS * 1000:
                if len(pulses) > 10:  # Minimum pulses to consider it a valid signal
                    break
        
        if time.time() - start_time > 10:  # 10s timeout
            print("Timeout waiting for signal.")
            cb.cancel()
            return None
        
        time.sleep(0.1)
    
    cb.cancel()
    print(f"Captured {len(pulses)} pulses.")
    return pulses

def save_code(name, data):
    try:
        with open('codes.json', 'r') as f:
            codes = json.load(f)
    except:
        codes = {}
    
    codes[name] = data
    with open('codes.json', 'w') as f:
        json.dump(codes, f, indent=4)
    print(f"Saved '{name}' to codes.json")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ir_recorder.py <button_name>")
        sys.exit(1)
    
    name = sys.argv[1]
    data = record_code(name)
    if data:
        save_code(name, data)
    
    pi.stop()

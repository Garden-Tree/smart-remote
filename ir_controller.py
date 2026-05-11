import json
import time
import paho.mqtt.client as mqtt
import pigpio

# Load configuration
with open('config.json', 'r') as f:
    CONFIG = json.load(f)

# Load IR codes
def load_codes():
    try:
        with open('codes.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading codes.json: {e}")
        return {}

CODES = load_codes()

# GPIO setup
TX_GPIO = CONFIG['gpio']['ir_send']
FREQ = CONFIG['ir']['frequency']
pi = pigpio.pi()

if not pi.connected:
    print("Could not connect to pigpiod. Is it running?")
    exit(1)

pi.set_mode(TX_GPIO, pigpio.OUTPUT)

def carrier(gpio, frequency, micros):
    """
    Generate carrier pulses for the IR LED.
    """
    wf = []
    cycle = 1000000.0 / frequency
    cycles = int(round(micros / cycle))
    on = int(round(cycle / 2.0))
    off = int(round(cycle - on))
    for r in range(cycles):
        wf.append(pigpio.pulse(1 << gpio, 0, on))
        wf.append(pigpio.pulse(0, 1 << gpio, off))
    return wf

def send_code(code_name):
    global CODES
    if code_name not in CODES:
        print(f"Code '{code_name}' not found in codes.json")
        # Reload codes in case it was updated
        CODES = load_codes()
        if code_name not in CODES:
            return

    print(f"Sending IR code: {code_name}")
    pulses = CODES[code_name]
    
    # Generate the wave
    wf = []
    for i in range(len(pulses)):
        micros = pulses[i]
        if i % 2 == 0:  # Mark
            wf.extend(carrier(TX_GPIO, FREQ, micros))
        else:  # Space
            wf.append(pigpio.pulse(0, 1 << TX_GPIO, micros))
    
    pi.wave_clear()
    pi.wave_add_generic(wf)
    wid = pi.wave_create()
    
    if wid >= 0:
        pi.wave_send_once(wid)
        while pi.wave_tx_at():
            time.sleep(0.01)
        pi.wave_delete(wid)
    else:
        print(f"Failed to create wave (error {wid})")

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.subscribe(CONFIG['mqtt']['topic'])
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode('utf-8')
        print(f"Received message: {payload} on topic {msg.topic}")
        send_code(payload)
    except Exception as e:
        print(f"Error handling message: {e}")

# Main loop
client = mqtt.Client(client_id=CONFIG['mqtt']['client_id'])
client.on_connect = on_connect
client.on_message = on_message

try:
    print(f"Connecting to broker {CONFIG['mqtt']['broker']}...")
    client.connect(CONFIG['mqtt']['broker'], CONFIG['mqtt']['port'], 60)
    client.loop_forever()
except KeyboardInterrupt:
    print("Exiting...")
finally:
    client.disconnect()
    pi.stop()

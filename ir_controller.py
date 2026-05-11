import json
import subprocess
import sys
import paho.mqtt.client as mqtt

# Load configuration
with open('config.json', 'r') as f:
    CONFIG = json.load(f)

def run_irrp(mode, name):
    if mode == 'record':
        gpio = CONFIG['gpio']['ir_receive']
        cmd = [
            sys.executable, 'irrp.py',
            '-r',
            '-g', str(gpio),
            '-f', 'codes.json',
            '--glitch', str(CONFIG['ir'].get('glitch', 100)),
            '--post', str(CONFIG['ir'].get('gap_ms', 100)),
            '--tolerance', str(CONFIG['ir'].get('tolerance', 15)),
            name
        ]
    else: # play
        gpio = CONFIG['gpio']['ir_send']
        freq = CONFIG['ir'].get('frequency', 38000) / 1000.0
        cmd = [
            sys.executable, 'irrp.py',
            '-p',
            '-g', str(gpio),
            '-f', 'codes.json',
            '--freq', str(freq),
            name
        ]
    
    print(f"Running IR command: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running irrp.py: {e}")

# MQTT Callbacks
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to MQTT Broker!")
        client.subscribe(CONFIG['mqtt']['topic'])
        client.subscribe(CONFIG['mqtt']['topic'] + "/record")
    else:
        print(f"Failed to connect, return code {reason_code}")

def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        print(f"Received message: {payload} on topic {topic}")
        
        if topic.endswith("/record"):
            run_irrp('record', payload)
        else:
            run_irrp('play', payload)
            
    except Exception as e:
        print(f"Error handling message: {e}")

# Main loop
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CONFIG['mqtt']['client_id'])
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

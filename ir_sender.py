import sys
import json
import subprocess

def main():
    if len(sys.argv) < 2:
        print("Usage: python ir_sender.py <button_name>")
        sys.exit(1)
    
    name = sys.argv[1]
    
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    gpio = config['gpio']['ir_send']
    filename = 'codes.json'
    freq = config['ir'].get('frequency', 38000) / 1000.0
    
    cmd = [
        sys.executable, 'irrp.py',
        '-p',
        '-g', str(gpio),
        '-f', filename,
        '--freq', str(freq),
        name
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    subprocess.run(cmd)

if __name__ == "__main__":
    main()

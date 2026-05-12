import json
import sys
import time
import paho.mqtt.client as mqtt
from pigpio_dht import DHT22

# 設定の読み込み
try:
    with open('config.json', 'r') as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    print("config.json が見つかりません。config.json.example をコピーして作成してください。")
    sys.exit(1)

# GPIOピンの設定
sensor_pin = CONFIG['gpio'].get('sensor', 4)

# センサーの初期化 (pigpio-dht を使用)
# 稼働中の pigpiod デーモンと通信し、ハードウェアDMAによる正確なサンプリングを行います
sensor = DHT22(sensor_pin)

# MQTTの設定
mqtt_config = CONFIG['mqtt']
broker = mqtt_config['broker']
port = mqtt_config.get('port', 1883)
topic = mqtt_config.get('sensor_topic', 'smart-remote/sensor')

client_id = mqtt_config.get('client_id', 'raspberry-pi-ir-remote') + "-sensor"
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)

username = mqtt_config.get('username')
password = mqtt_config.get('password')
if username:
    client.username_pw_set(username, password)

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"MQTTブローカーに接続しました ({client_id})")
    else:
        print(f"接続に失敗しました。コード: {reason_code}")

client.on_connect = on_connect

print(f"ブローカー {broker} に接続中...")
client.connect(broker, port, 60)
client.loop_start()

interval = CONFIG.get('sensor', {}).get('interval', 60)
print(f"計測を開始します。{interval}秒ごとに '{topic}' へパブリッシュします。")

try:
    while True:
        try:
            # read(retries=5) により、内部で自動的に数回リトライを行い確実な値を取得します
            result = sensor.read(retries=5)
            
            if result.get('valid'):
                payload = {
                    "temperature": round(result['temp_c'], 1),
                    "humidity": round(result['humidity'], 1),
                    "timestamp": int(time.time())
                }
                payload_json = json.dumps(payload)
                client.publish(topic, payload_json)
                print(f"送信完了: {payload_json}")
            else:
                print(f"データの取得に失敗しました: {result}")
                
        except Exception as error:
            print(f"読み取りエラー: {error}")

        time.sleep(interval)

except KeyboardInterrupt:
    print("終了します...")
finally:
    client.loop_stop()
    client.disconnect()

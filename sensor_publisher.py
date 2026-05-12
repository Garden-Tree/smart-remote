import json
import sys
import time
import adafruit_dht
import board
import paho.mqtt.client as mqtt

# 設定の読み込み
try:
    with open('config.json', 'r') as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    print("config.json が見つかりません。config.json.example をコピーして作成してください。")
    sys.exit(1)

# GPIOピンの設定 (AM2302はDHT22と同じインターフェース)
sensor_pin_num = CONFIG['gpio'].get('sensor', 4)
try:
    pin = getattr(board, f'D{sensor_pin_num}')
except AttributeError:
    print(f"無効なGPIOピン番号です: {sensor_pin_num}")
    sys.exit(1)

# センサーの初期化
dht_device = adafruit_dht.DHT22(pin)

# MQTTの設定
mqtt_config = CONFIG['mqtt']
broker = mqtt_config['broker']
port = mqtt_config.get('port', 1883)
topic = mqtt_config.get('sensor_topic', 'smart-remote/sensor')

# ir_controller.py との Client ID 重複を避けるためにサフィックスを追加
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
            # センサーから値を読み取る
            temperature = dht_device.temperature
            humidity = dht_device.humidity
            
            if temperature is not None and humidity is not None:
                payload = {
                    "temperature": round(temperature, 1),
                    "humidity": round(humidity, 1),
                    "timestamp": int(time.time())
                }
                payload_json = json.dumps(payload)
                client.publish(topic, payload_json)
                print(f"送信完了: {payload_json}")
            else:
                print("データの取得に失敗しました (値が None です)")

        except RuntimeError as error:
            # 温湿度センサー(DHT系)はタイミングにシビアなため、頻繁に読み取りエラーが発生します。
            # エラー時は少し待ってからリトライするのが一般的です。
            print(f"読み取りエラー (自動リトライします): {error.args[0]}")
            time.sleep(2.0)
            continue
        except Exception as error:
            dht_device.exit()
            raise error

        time.sleep(interval)

except KeyboardInterrupt:
    print("終了します...")
finally:
    client.loop_stop()
    client.disconnect()
    dht_device.exit()

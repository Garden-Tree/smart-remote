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

# GPIOピンの設定
sensor_pin_num = CONFIG['gpio'].get('sensor', 4)
try:
    pin = getattr(board, f'D{sensor_pin_num}')
except AttributeError:
    print(f"無効なGPIOピン番号です: {sensor_pin_num}")
    sys.exit(1)

# 【永続インスタンス方式】
# 初回のみ計測に成功していた事実に基づき、インスタンスは起動時に1回だけ生成して維持します。
# 毎回の生成・破棄によるOS側のGPIOリソース確保の遅延・オーバーヘッドを排除します。
dht_device = adafruit_dht.DHT22(pin)

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


def read_sensor_with_retry(device, max_retries=10):
    """
    センサーからの読み取りを試行し、失敗した場合は規定回数しつこくリトライする関数。
    Linux環境でのDHT系センサーはスケジューラの都合でパルスを逃しやすいため、
    複数回アクセスを繰り返すことで成功率を大幅に高めます。
    """
    for attempt in range(1, max_retries + 1):
        try:
            temperature = device.temperature
            humidity = device.humidity
            if temperature is not None and humidity is not None:
                return temperature, humidity
        except RuntimeError as error:
            print(f"  [試行 {attempt}/{max_retries}] 読み取り一時エラー: {error.args[0]}")
            # 温湿度センサーマイコンの復帰に必要な時間(2.5秒以上)を確保して再試行
            time.sleep(2.5)
            continue
        except Exception as error:
            raise error
            
    return None, None


try:
    while True:
        print("\nセンサーデータを取得中...")
        temperature, humidity = read_sensor_with_retry(dht_device)
        
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
            print("規定回数リトライしましたが、データの取得に失敗しました。")

        # インターバル待機 (リトライにかかった時間を考慮せずシンプルに待機)
        time.sleep(interval)

except KeyboardInterrupt:
    print("終了します...")
finally:
    client.loop_stop()
    client.disconnect()
    dht_device.exit()

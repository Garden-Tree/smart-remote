# Raspberry Pi Smart IR Remote & Sensor (MQTT)

MQTT経由で赤外線リモコン信号を送信・学習するシステム、およびAM2302（DHT22）センサーを用いた温湿度計測システムです。
赤外線処理のコアには信頼性の高い `irrp.py` を使用しています。


## セットアップ

### 1. 依存関係のインストール (Raspberry Pi上)

```bash
sudo apt update
sudo apt install pigpio python3-pigpio
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

### 2. Python仮想環境の作成とライブラリのインストール

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 使い方

### 1. 直接実行（テスト用）

`irrp.py` を直接叩くか、簡易的なラッパースクリプトを使用できます。

**学習する:**
```bash
python ir_recorder.py tv_power
# または直接
python irrp.py -r -g 18 -f codes.json tv_power
```

**送信する:**
```bash
python ir_sender.py tv_power
# または直接
python irrp.py -p -g 17 -f codes.json tv_power
```

### 2. MQTT経由での実行

MQTTブローカーからの指示を待ち受けるブリッジプログラムを起動します。

```bash
python ir_controller.py
```

**MQTTで送信:**
トピック `smart-remote/command` にボタン名を送信します。
```bash
mosquitto_pub -t smart-remote/command -m "tv_power"
```

**MQTTで学習:**
トピック `smart-remote/command/record` にボタン名を送信すると、Pi側で学習モード（LED待機状態）に入ります。
```bash
mosquitto_pub -t smart-remote/command/record -m "new_button"
```

### 3. 温湿度センサーの実行

AM2302センサーから定期的に温度と湿度を読み取り、MQTTへ送信するプログラムを起動します。

```bash
python sensor_publisher.py
```

指定した間隔（デフォルトは60秒）で、トピック `smart-remote/sensor` へ以下のようなJSONデータがパブリッシュされます。
```json
{
  "temperature": 25.4,
  "humidity": 60.1,
  "timestamp": 1715520000
}
```


## プログラム構成

- `irrp.py`: 赤外線制御のメインスクリプト（pigpio公式例）。
- `ir_recorder.py`: `irrp.py` を呼び出す学習用ラッパー。
- `ir_sender.py`: `irrp.py` を呼び出す送信用ラッパー。
- `ir_controller.py`: MQTTメッセージを解釈して `irrp.py` を実行するブリッジ。
- `sensor_publisher.py`: AM2302センサーから温湿度を取得してMQTTへ送信するパブリッシャー。
- `config.json`: GPIOピンやMQTTの接続設定。
- `codes.json`: 学習した赤外線パルスのデータ。


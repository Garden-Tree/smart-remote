# Raspberry Pi Smart IR Remote (MQTT + pigpio)

MQTT経由で赤外線リモコン信号を送信するシステムです。

## セットアップ

### 1. 依存関係のインストール (Raspberry Pi上)

まず、`pigpio` デーモンをインストールして起動します。

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

### 3. 設定の確認

`config.json` を開き、以下の項目を環境に合わせて変更してください。
- `mqtt.broker`: MQTTブローカーのIPアドレス
- `gpio.ir_send`: 赤外線LEDを接続したGPIOピン
- `gpio.ir_receive`: 赤外線受信モジュールを接続したGPIOピン

## 使い方

### 1. リモコン信号を学習する

リモコンのボタン信号を `codes.json` に保存します。

```bash
# 例: "tv_power" という名前で学習
python ir_recorder.py tv_power
```

画面の指示に従い、受信モジュールに向けてリモコンのボタンを押してください。

### 2. コントローラーを起動する

MQTTブローカーからの指示を待ち受けます。

```bash
python ir_controller.py
```

### 3. 赤外線信号を送信する

他のデバイスやPCからMQTTメッセージを送信して操作します。

```bash
# 例: mosquitto_pub を使用して tv_power を送信
mosquitto_pub -h localhost -t smart-remote/command -m "tv_power"
```

## 注意点

- **ハードウェア**: 赤外線LEDはGPIOピンから直接駆動せず、トランジスタ（2N2222等）を介して接続することを推奨します。
- **搬送波**: `ir_controller.py` はソフトウェアで38kHzの搬送波を生成しています。

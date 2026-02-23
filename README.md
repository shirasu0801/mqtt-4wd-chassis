# mqtt-4wd-chassis

Raspberry Pi と MQTT を使って、ミニ四駆の走行を無線制御する Python モジュールです。  
本リポジトリは、制御コマンド送信側（Publisher）と車両側受信制御（Subscriber）を分離し、安全停止を含む最小構成を提供します。

## 1. プロジェクト概要

本プロジェクトの目的は、以下を満たす車両制御基盤を作ることです。

- 前進、後進、停止、緊急停止を MQTT コマンドで制御できる
- PWM による速度制御（0-100%）を行える
- 通信断に備えたフェイルセーフ停止を備える
- Raspberry Pi Zero 系を想定した小型構成で運用できる

想定構成:

- 制御側（Publisher）: PC / スマホ等からコマンド送信
- MQTT Broker: Mosquitto など
- 車両側（Subscriber）: Raspberry Pi + DRV8833（モータードライバ）

## 2. 要件（実装反映済み）

要件の補完 QA は `docs/qa_requirements.md` に記載しています。  
ここでは運用に必要な要点のみ抜粋します。

- 制御トピック: `mini4wd/control`
- 状態通知トピック: `mini4wd/status`
- QoS: `1`
- Payload: JSON
- action: `forward | reverse | stop | estop`
- speed: `0-100`
- stop_mode: `coast | brake`
- フェイルセーフタイムアウト: `1.0秒`（既定）
- 緊急停止: `estop` 受信で即時停止

## 3. 事前準備

### 3.1 ハードウェア

- Raspberry Pi Zero 2 W（推奨）
- DRV8833 デュアルモータードライバ
- ミニ四駆車体（搭載スペースを確保）
- LiPo バッテリー + 5V 昇圧回路（Pi 用）
- モーター用電源（Pi と分離推奨）

### 3.2 ソフトウェア

- Raspberry Pi OS Lite
- Python 3.10 以上
- MQTT Broker（Mosquitto 推奨）

### 3.3 ネットワーク

- Raspberry Pi と制御端末が同一ネットワークで MQTT Broker に到達できること
- Broker のポート（通常 1883）が疎通していること

## 4. インストール手順

プロジェクトルートで実行:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

Raspberry Pi 実機で GPIO 制御する場合:

```bash
pip install -e .[pi]
```

## 5. 設定手順

環境変数で設定します（未指定時は既定値）。

- `MQTT_HOST`（既定: `localhost`）
- `MQTT_PORT`（既定: `1883`）
- `MQTT_USERNAME`（任意）
- `MQTT_PASSWORD`（任意）
- `MQTT_CONTROL_TOPIC`（既定: `mini4wd/control`）
- `MQTT_STATUS_TOPIC`（既定: `mini4wd/status`）
- `MQTT_QOS`（既定: `1`）
- `MQTT_KEEPALIVE`（既定: `30`）
- `FAILSAFE_TIMEOUT_S`（既定: `1.0`）
- `MOTOR_AIN1_PIN`（既定: `17`）
- `MOTOR_AIN2_PIN`（既定: `27`）
- `MOTOR_PWM_FREQ_HZ`（既定: `1000`）
- `MINI4WD_SIMULATION=1` でモックモード

PowerShell 設定例:

```powershell
$env:MQTT_HOST="192.168.1.20"
$env:MQTT_PORT="1883"
$env:FAILSAFE_TIMEOUT_S="1.0"
$env:MOTOR_AIN1_PIN="17"
$env:MOTOR_AIN2_PIN="27"
```

## 6. 実行方法

### 6.1 車両側（Subscriber）起動

モック（開発PCで動作確認）:

```bash
mini4wd-vehicle --simulation
```

実機 GPIO:

```bash
mini4wd-vehicle
```

### 6.2 制御側（Publisher）からコマンド送信

```bash
mini4wd-controller forward --speed 60
mini4wd-controller reverse --speed 45
mini4wd-controller stop --stop-mode coast
mini4wd-controller estop --stop-mode brake
```

### 6.3 メッセージ仕様

```json
{
  "action": "forward",
  "speed": 60,
  "stop_mode": "coast",
  "request_id": "optional-id",
  "timestamp": "auto-generated"
}
```

## 7. フォルダ構造と各ファイルの説明

```text
mqtt-4wd-chassis/
├─ docs/
│  └─ qa_requirements.md
├─ src/
│  └─ mini4wd/
│     ├─ __init__.py
│     ├─ config.py
│     ├─ protocol.py
│     ├─ motor.py
│     ├─ vehicle.py
│     ├─ controller.py
│     ├─ main_vehicle.py
│     └─ main_controller.py
├─ tests/
│  ├─ conftest.py
│  └─ test_protocol.py
├─ pyproject.toml
└─ README.md
```

ファイル説明:

- `docs/qa_requirements.md`  
  要件定義で未確定だった仕様を QA で確定したドキュメント
- `src/mini4wd/config.py`  
  環境変数から MQTT、GPIO、フェイルセーフ設定を読み込む
- `src/mini4wd/protocol.py`  
  制御メッセージ JSON の生成とバリデーション
- `src/mini4wd/motor.py`  
  DRV8833 実機ドライバとモックドライバ
- `src/mini4wd/vehicle.py`  
  MQTT 受信処理、モーター反映、フェイルセーフ、状態通知
- `src/mini4wd/controller.py`  
  MQTT への制御メッセージ送信
- `src/mini4wd/main_vehicle.py`  
  車両側 CLI エントリポイント
- `src/mini4wd/main_controller.py`  
  制御側 CLI エントリポイント
- `tests/test_protocol.py`  
  メッセージ検証ロジックの単体テスト
- `tests/conftest.py`  
  テスト時の import パス調整
- `pyproject.toml`  
  依存関係と CLI コマンド定義

## 8. 次回に向けた改善ポイント

- TLS 対応（MQTT over TLS）と証明書運用
- `estop` のラッチ仕様（解除コマンド必須化）
- 通信再接続時の状態同期戦略
- デッドゾーン補正（低速で回らない個体差対応）
- 旋回制御（左右独立駆動）への拡張
- ログ保存先の永続化とローテーション
- システムサービス化（`systemd`）で自動起動

## 9. 運用面でのネクストアクション

1. 実機配線表と GPIO 番号を確定して README に反映  
2. テストコースで停止距離と応答遅延を測定（要件: 200ms 以内）  
3. バッテリー連続稼働テスト（15 分以上）を実施  
4. 異常系試験（Wi-Fi 切断、Broker 停止、ノイズ環境）を実施  
5. 運用手順書に「緊急停止前提の始業点検」を追加

## 10. 操作マニュアル

### 10.1 起動前チェック

1. モーター配線と電源極性に誤りがないことを確認
2. 車体が空転できる状態で初回電源投入する
3. MQTT Broker が稼働し、`MQTT_HOST` が正しいことを確認
4. 緊急停止コマンド送信端末をすぐ操作できる状態にする

### 10.2 基本操作フロー

1. 車両側を起動  
   `mini4wd-vehicle`（または `mini4wd-vehicle --simulation`）
2. 制御側から前進コマンド  
   `mini4wd-controller forward --speed 40`
3. 必要に応じて速度変更（再送）  
   `mini4wd-controller forward --speed 70`
4. 停止  
   `mini4wd-controller stop --stop-mode coast`
5. 危険時は緊急停止  
   `mini4wd-controller estop --stop-mode brake`

### 10.3 推奨運用ルール

- 試走開始時は `speed=30` 程度から段階的に上げる
- 人の近くでは `estop --stop-mode brake` を常時使えるようにする
- 走行終了時は必ず `stop` を送信してから車体電源を切る
- 設定変更時は 1 項目ずつ変更して再試験する

### 10.4 トラブルシュート

- 症状: 反応しない  
  確認: `MQTT_HOST/PORT`、トピック名、Broker 稼働状態
- 症状: 逆回転する  
  確認: モーター配線（AIN1/AIN2）を入れ替え
- 症状: すぐ停止する  
  確認: `FAILSAFE_TIMEOUT_S` が短すぎないか
- 症状: 低速で動かない  
  確認: 実機特性によるデッドゾーン（最低 duty の再調整が必要）

## 11. 安全上の注意

- LiPo バッテリーは過充電・過放電・短絡対策を必ず実施
- モーター電源と Raspberry Pi 電源は分離推奨
- 初期試験は必ず車体を浮かせた状態で実施
- 子どもの近くや狭い室内では低速運用と緊急停止を徹底


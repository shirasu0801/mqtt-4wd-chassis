# MQTT Mini 4WD 要件QA（不足要件の補完）

この文書は、提示された要件定義の不足項目を QA で補完し、実装に落とし込むための確定仕様です。

## 1. 通信プロトコル仕様

- 制御トピック: `mini4wd/control`
- 状態通知トピック: `mini4wd/status`
- MQTT QoS: `1`（最低1回配信）
- Retain: `false`（古い走行コマンド再適用を防ぐ）
- Payload形式: UTF-8 JSON

制御メッセージ例:

```json
{
  "action": "forward",
  "speed": 65,
  "stop_mode": "coast",
  "request_id": "cmd-20260221-001",
  "timestamp": "2026-02-21T14:00:00Z"
}
```

- `action`: `forward | reverse | stop | estop`
- `speed`: 0-100（`stop`/`estop`時は省略可）
- `stop_mode`: `coast | brake`（`stop`/`estop`で使用、省略時 `coast`）
- `request_id`: 任意。追跡用ID
- `timestamp`: 任意。ISO 8601 UTC

## 2. 安全仕様

- フェイルセーフタイムアウト: **1.0秒**
- タイムアウト時挙動: 即時 `stop`（デフォルト `coast`）
- 緊急停止 `estop`: 受信即時停止。`stop_mode` があれば優先、なければ `brake`
- プロセス終了時: 必ず停止命令をモータードライバへ送る

## 3. モーター制御仕様（DRV8833想定）

- 単一DCモーター制御（Aチャネル）を初期実装対象
- GPIO出力方式: 2ピンPWM（AIN1/AIN2）
- 推奨PWM周波数: **1000Hz**
- 速度マッピング: `speed(0-100)` を `duty(0.0-1.0)` に線形変換

方向制御:

- 前進: `AIN1=duty`, `AIN2=0`
- 後進: `AIN1=0`, `AIN2=duty`
- 停止（coast）: `AIN1=0`, `AIN2=0`
- 停止（brake）: `AIN1=1`, `AIN2=1`

## 4. 接続/認証仕様

- Broker接続先: 環境変数またはCLI引数で指定
- 認証: ユーザー名/パスワード対応（任意）
- Client ID:
  - 車両側: `mini4wd-vehicle-<hostname>`
  - 制御側: `mini4wd-controller-<hostname>`

## 5. 応答性要件への実装方針

- MQTT keepalive: 30秒
- メッセージ受信処理は同期処理を最小化し、受信コールバック内で即時反映
- Python処理遅延の目標: 通常時 50ms 以下（ネットワーク条件除く）

## 6. 未確定事項（次フェーズで要確認）

- 実機のギア比・重量に応じた最低駆動デューティ（デッドゾーン補正）
- `estop` をラッチ動作（解除コマンド必須）にするか
- TLS有効化の有無（屋外利用や共有ネットワーク時は推奨）


# Google Calendar Desktop Widget

Windowsデスクトップ上に常駐する、Googleカレンダーの予定表示ウィジェットです。

![Python](https://img.shields.io/badge/Python-3.12+-blue) ![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

![スクリーンショット](image/スクリーンショット%202026-02-14%20185915.png)

## 機能

- **予定一覧表示** - 時刻・タイトル・場所を表示
- **日付ナビゲーション** - 前日・翌日の予定を確認可能
- **現在進行中の予定ハイライト** - 今の時間帯の予定を強調表示
- **アラート通知** - 予定の5分前にポップアップ＋サウンドで通知（ON/OFF切替）
- **Google Calendarリンク** - ワンクリックでブラウザのGoogle Calendarを開く
- **ドラッグ移動** - ヘッダーをドラッグしてデスクトップ上の好きな位置に配置
- **システムトレイ常駐** - 閉じるボタンでトレイに格納、ダブルクリックで復元
- **右クリックメニュー** - 更新 / 今日に戻る / 最前面切替 / 終了

## セットアップ

### 1. Google Cloud Console の設定

初回のみ必要です。詳細は [SETUP.md](SETUP.md) を参照してください。

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクト作成
2. Google Calendar API を有効化
3. OAuth 同意画面を設定（テストユーザーに自分を追加）
4. OAuth クライアントID を作成（**デスクトップアプリ**）
5. `credentials.json` をダウンロードしてプロジェクトルートに配置

### 2. 依存パッケージのインストール

```bash
git clone https://github.com/tsubasagit/ToDayGoogleCalender.git
cd ToDayGoogleCalender
python -m venv venv
.\venv\Scripts\pip.exe install -r requirements.txt
```

### 3. 起動

```bash
.\venv\Scripts\python.exe main.py
```

初回起動時にブラウザが開き、Googleアカウントの認証を求められます。認証後は `token.json` が保存され、次回以降は自動ログインします。

## 操作方法

| 操作 | 説明 |
|---|---|
| ◀ 前日 / 翌日 ▶ | 表示日を切り替え |
| 今日 | 今日の予定に戻る |
| ↻ | 予定を再取得 |
| 🔔 | アラート通知の ON/OFF |
| ✕ | トレイに格納 |
| 右クリック | コンテキストメニュー |
| ヘッダードラッグ | ウィンドウ移動 |
| Google Calendar ↗ | ブラウザで Google Calendar を開く |

## ファイル構成

```
Claude-TodayGoogleCalentder/
├── main.py              # エントリーポイント
├── calendar_api.py      # Google Calendar API 連携
├── widget.py            # tkinter ウィジェット UI
├── requirements.txt     # 依存パッケージ
├── SETUP.md             # Google Cloud Console セットアップガイド
├── credentials.json     # OAuth認証情報（要手動配置）
└── token.json           # 認証トークン（自動生成）
```

## 技術スタック

- **Python 3.12+**
- **tkinter** - GUI
- **Google Calendar API** - 予定取得
- **pystray** - システムトレイ
- **Pillow** - トレイアイコン生成

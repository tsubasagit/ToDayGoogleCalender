# Google Calendar Desktop Widget

Windowsデスクトップ上に常駐する、Googleカレンダーの予定表示ウィジェットです。

![Python](https://img.shields.io/badge/Python-3.12+-blue) ![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

![スクリーンショット](image/スクリーンショット%202026-02-14%20185915.png)

## 注意事項

> **exe版は現在 Windows ARM64 版のみ提供しています。**
> 通常の x86_64 PC をお使いの場合は、exe版は動作しません。「[ソースから実行](#ソースから実行開発者向け)」の手順をご利用ください。

> **初回セットアップに Google Cloud Console での設定が必要です。**
> このアプリは Google Calendar API を使用しているため、各ユーザーが自分の Google Cloud Console で OAuth 認証情報（`credentials.json`）を作成する必要があります。手順は [SETUP.md](SETUP.md) を参照してください。所要時間は約5〜10分です。

## 機能

- **予定一覧表示** - 時刻・タイトル・場所を表示
- **日付ナビゲーション** - 前日・翌日の予定を確認可能
- **現在進行中の予定ハイライト** - 今の時間帯の予定を強調表示
- **過ぎた予定の自動非表示** - 今日の終了済み予定を自動で非表示
- **アラート通知** - 予定の5分前にポップアップ＋サウンドで通知（ON/OFF切替）
- **Google Calendarリンク** - ワンクリックでブラウザのGoogle Calendarを開く
- **ドラッグ移動** - ヘッダーをドラッグしてデスクトップ上の好きな位置に配置
- **システムトレイ常駐** - 閉じるボタンでトレイに格納、ダブルクリックで復元
- **右クリックメニュー** - 更新 / 今日に戻る / 最前面切替 / 終了

## ダウンロード（exe版）

Python不要ですぐに使えます。

1. [Releases](https://github.com/tsubasagit/ToDayGoogleCalender/releases) から最新の ZIP をダウンロード
2. ZIP を解凍
3. [SETUP.md](SETUP.md) を参考に Google Cloud Console で `credentials.json` を取得
4. `credentials.json` を `CalendarWidget.exe` と同じフォルダに配置
5. `CalendarWidget.exe` をダブルクリックで起動

> **注意**: 現在 Windows ARM64 版のみ提供しています。x86_64 PC をお使いの場合は、下記の「ソースから実行」をご利用ください。

## ソースから実行（開発者向け）

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

初回起動時にウィジェット上に「ログイン」ボタンが表示されます。クリックするとブラウザでGoogle認証が開始され、認証後は自動で予定が表示されます。

## 操作方法

| 操作 | 説明 |
|---|---|
| ◀ 前日 / 翌日 ▶ | 表示日を切り替え |
| 今日 | 今日の予定に戻る |
| ↻ | 予定を再取得 |
| 🔔 | アラート通知の ON/OFF（5分前通知） |
| ✕ | トレイに格納 |
| 右クリック | コンテキストメニュー |
| ヘッダードラッグ | ウィンドウ移動 |
| Google Calendar ↗ | ブラウザで Google Calendar を開く |

## 技術スタック

- **Python 3.12+**
- **tkinter** - GUI
- **Google Calendar API** - 予定取得
- **pystray** - システムトレイ
- **Pillow** - トレイアイコン生成

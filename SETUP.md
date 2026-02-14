# Google Calendar Widget セットアップガイド

## 1. Google Cloud Console でプロジェクト作成

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 上部の「プロジェクトを選択」→「新しいプロジェクト」をクリック
3. プロジェクト名を入力（例: `calendar-widget`）→「作成」

## 2. Google Calendar API を有効化

1. 左メニュー「APIとサービス」→「ライブラリ」
2. 検索バーで `Google Calendar API` を検索
3. 「Google Calendar API」をクリック →「有効にする」

## 3. OAuth 同意画面の設定

1. 左メニュー「APIとサービス」→「OAuth 同意画面」
2. 「始める」をクリック
3. アプリ名: `Calendar Widget`（任意）
4. ユーザーサポートメール: 自分のメールアドレス
5. 対象: 「外部」を選択
6. デベロッパーの連絡先メールアドレス: 自分のメールアドレス
7. 「作成」をクリック

### テストユーザーの追加
1. 「対象ユーザー」タブへ移動
2. 「テストユーザー」セクションで「Add Users」をクリック
3. 自分の Google メールアドレスを追加 →「保存」

## 4. OAuth 2.0 クライアントID の作成

1. 左メニュー「APIとサービス」→「認証情報」
2. 上部「＋認証情報を作成」→「OAuth クライアント ID」
3. アプリケーションの種類: **デスクトップ アプリ**
4. 名前: `Calendar Widget`（任意）
5. 「作成」をクリック

## 5. credentials.json のダウンロード

1. 作成したクライアントIDの右にある「⬇（ダウンロード）」アイコンをクリック
2. ダウンロードした JSON ファイルを `credentials.json` にリネーム
3. このプロジェクトのルートディレクトリに配置:
   ```
   Claude-TodayGoogleCalentder/
   ├── credentials.json  ← ここに配置
   ├── main.py
   ├── ...
   ```

## 6. アプリの起動

```bash
cd <プロジェクトディレクトリ>
.\venv\Scripts\python.exe main.py
```

初回起動時にブラウザが開き、Google アカウントの認証を求められます。
認証後、`token.json` が自動生成され、次回以降はブラウザ認証なしで起動できます。

> **注意**: 「このアプリは確認されていません」という警告が表示されます。
> 「詳細」→「Calendar Widget（安全ではないページ）に移動」をクリックして続行してください。

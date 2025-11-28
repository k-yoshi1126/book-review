# Book Review Notifier

Lifehackerの書評記事を自動で監視し、新しい記事が公開された際にSlackへ通知するシステムです。

## 概要

このプロジェクトは、[Lifehackerの書評コーナー](https://www.lifehacker.jp/regular/regular_book_to_read/)を定期的にチェックし、新しく公開された記事を検出してSlackに通知します。GitHub Actionsを使用して自動実行されるため、手動での操作は不要です。

## 主な機能

- 🔍 **自動監視**: 平日の日本時間10時に自動で記事一覧をチェック
- 📢 **Slack通知**: 新しい記事が公開された際に自動でSlackへ通知
- 🚫 **広告除外**: スポンサー記事や広告リンクを自動で除外
- 💾 **状態管理**: 既知の記事URLを保存し、重複通知を防止

## セットアップ

### 前提条件

- Python 3.11以上
- Slack Webhook URL

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd book_review
```

### 2. 依存関係のインストール

```bash
pip install requests beautifulsoup4
```

または、`requirements.txt`を作成して使用する場合：

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

`.env.example`を参考に、`.env`ファイルを作成してSlack Webhook URLを設定します：

```bash
cp env.example .env
```

`.env`ファイルを編集し、Slack Webhook URLを設定してください：

```
SLACK_BOOKREVIEW_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

#### Slack Webhook URLの取得方法

1. [Slack API](https://api.slack.com/apps)にアクセス
2. 新しいアプリを作成、または既存のアプリを選択
3. 「Incoming Webhooks」機能を有効化
4. 「Add New Webhook to Workspace」をクリック
5. 通知を送信したいチャンネルを選択
6. Webhook URLをコピーして`.env`ファイルに貼り付け

### 4. GitHub Actionsの設定（自動実行を使用する場合）

このプロジェクトはGitHub Actionsで自動実行するように設定されています。以下の手順でセットアップしてください：

1. GitHubリポジトリの「Settings」→「Secrets and variables」→「Actions」に移動
2. 「New repository secret」をクリック
3. 以下のシークレットを追加：
   - **Name**: `SLACK_BOOKREVIEW_WEBHOOK_URL`
   - **Value**: あなたのSlack Webhook URL

設定後、ワークフローは平日の日本時間10時（UTC+1時）に自動実行されます。

## 使用方法

### ローカルでの手動実行

ローカル環境でスクリプトを手動実行する場合：

```bash
python scripts/check_articles.py
```

スクリプトは以下の処理を実行します：

1. Lifehackerの書評一覧ページから記事URLを取得
2. 既知のURL（`data/known_urls.json`）と比較
3. 新しいURLを検出
4. 新しいURLごとにSlackへ通知
5. 既知のURLリストを更新

### GitHub Actionsでの自動実行

ワークフローは以下のスケジュールで自動実行されます：

- **実行頻度**: 平日（月曜日～金曜日）
- **実行時刻**: 日本時間10時（UTC+1時）
- **手動実行**: GitHubリポジトリの「Actions」タブから「Notify New Articles」ワークフローを選択し、「Run workflow」ボタンで手動実行も可能

## プロジェクト構造

```
book_review/
├── .github/
│   └── workflows/
│       └── notify-new-articles.yml  # GitHub Actionsワークフロー定義
├── data/
│   └── known_urls.json              # 既知の記事URL一覧（自動生成）
├── scripts/
│   └── check_articles.py            # メインスクリプト
├── .env                             # 環境変数（.gitignoreに含まれる）
├── env.example                      # 環境変数のテンプレート
├── .gitignore                       # Git除外設定
└── README.md                        # このファイル
```

## 動作の仕組み

1. **記事一覧の取得**: `check_articles.py`がLifehackerの書評一覧ページにアクセス
2. **HTML解析**: BeautifulSoupを使用して記事リンクを抽出
3. **フィルタリング**: 
   - 書評記事のURLパターンに一致するリンクのみを抽出
   - スポンサー記事や広告リンクを除外
4. **新規記事の検出**: 既知のURLリストと比較して新しい記事を特定
5. **通知**: 新しい記事ごとにSlackへ通知を送信
6. **状態の保存**: 既知のURLリストを更新して次回実行時に使用

## 設定のカスタマイズ

### チェック頻度の変更

`.github/workflows/notify-new-articles.yml`の`cron`設定を変更することで、チェック頻度を調整できます：

```yaml
schedule:
  - cron: "0 1 * * 1-5"  # 平日 / 日本時間10時
```

Cron構文について詳しくは、[GitHub Actionsのドキュメント](https://docs.github.com/ja/actions/using-workflows/events-that-trigger-workflows#schedule)を参照してください。

### 監視対象URLの変更

`scripts/check_articles.py`の`TARGET_URL`を変更することで、監視対象のページを変更できます：

```python
TARGET_URL = "https://www.lifehacker.jp/regular/regular_book_to_read/"
```

## トラブルシューティング

### 記事リンクが取得できない

以下の場合にエラーが発生する可能性があります：

- Lifehackerのページ構造が変更された
- ネットワークエラーが発生した
- タイムアウトが発生した

この場合、Slackにエラー通知が送信されます。スクリプトの`CARD_CONTAINER_SELECTOR`が最新のHTML構造に一致しているか確認してください。

### Slack通知が届かない

以下の点を確認してください：

1. `.env`ファイルに正しいSlack Webhook URLが設定されているか
2. GitHub Actionsのシークレットに`SLACK_BOOKREVIEW_WEBHOOK_URL`が設定されているか
3. SlackアプリのIncoming Webhooksが有効になっているか
4. ワークフローの実行ログでエラーが発生していないか

### 重複通知が発生する

`data/known_urls.json`が正しく更新されていない可能性があります。GitHub Actionsを使用している場合、Artifactが正しく保存・読み込まれているか確認してください。

## ライセンス

このプロジェクトのライセンスについては、リポジトリのLICENSEファイルを参照してください。

## 貢献

バグ報告や機能要望は、IssueやPull Requestでお知らせください。

## 注意事項

- このツールは個人利用を目的としており、Lifehackerの利用規約を遵守してください
- 過度なリクエストを避けるため、実行頻度は適切に設定してください
- ページ構造が変更された場合、スクリプトの修正が必要になる可能性があります


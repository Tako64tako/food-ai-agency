# 食事処提案AI

AIがユーザーの自然言語入力を理解し、Google Places APIを使用して最適な飲食店を提案するWebアプリケーションです

## 技術スタック

- **フロントエンド**: Next.js 14, React, TypeScript, Tailwind CSS
- **バックエンド**: Python Flask, OpenAI API, Google Places API
- **API**: OpenAI GPT-4, Google Places API

## セットアップ

### 前提条件
- Python 3.8+
- Node.js 18+
- OpenAI API キー
- Google Places API キー

### 1. 依存関係のインストール

#### バックエンド
```bash
pip install -r requirements.txt
```

#### フロントエンド
```bash
cd frontend
npm install
```

### 2. 環境変数の設定

環境変数を設定するために、以下の方法のいずれかを選択してください：

#### 方法A: config.pyで直接設定
`config.py` ファイルを編集して、APIキーを設定：

```python
class Config:
    OPENAI_API_KEY = 'your_openai_api_key_here'
    GOOGLE_PLACES_API_KEY = 'your_google_places_api_key_here'
```

#### 方法B: 環境変数ファイルを使用
1. `env.example` を参考に、環境変数ファイルを作成：
   ```bash
   # .env.local ファイルを作成
   OPENAI_API_KEY=your_openai_api_key_here
   GOOGLE_PLACES_API_KEY=your_google_places_api_key_here
   ```

2. または、システム環境変数として設定：
   ```bash
   export OPENAI_API_KEY="your_openai_api_key_here"
   export GOOGLE_PLACES_API_KEY="your_google_places_api_key_here"
   ```

### 3. アプリケーションの起動

#### バックエンドサーバー（ターミナル1）
```bash
# 方法A: 起動スクリプトを使用（推奨）
python start_backend.py

# 方法B: 直接起動
cd backend
python app.py
```

#### フロントエンドサーバー（ターミナル2）
```bash
cd frontend
npm run dev
```

アプリケーションは http://localhost:3000 で利用可能になります。

## 使用方法

1. Webアプリケーションにアクセス
2. チャット画面で自然言語で要望を入力
   - 例: "中華料理を食べたい"
   - 例: "渋谷で夜7時から静かなお店で3人でお酒を飲みたい"
3. AIが条件を理解し、最適な飲食店を提案

## API仕様

### POST /api/search
飲食店検索API

**リクエスト:**
```json
{
  "query": "渋谷で夜7時から静かなお店で3人でお酒を飲みたい"
}
```

**レスポンス:**
```json
{
  "message": "候補が3件見つかりました",
  "conditions": {
    "cuisine_type": "居酒屋",
    "location": "渋谷",
    "time": "19:00",
    "party_size": 3,
    "atmosphere": "静か"
  },
  "restaurants": [
    {
      "name": "食幹 渋谷",
      "score": 85,
      "reason": "静かな雰囲気で3人での飲み会に最適",
      "address": "東京都渋谷区...",
      "rating": 4.2
    }
  ]
}
```

## プロジェクト構造

```
reskilling/
├── backend/
│   ├── app.py                      # Flask APIサーバー（メイン）
│   └── services/
│       ├── __init__.py             # サービス層初期化
│       ├── restaurant_service.py   # レストラン推薦統合サービス
│       ├── openai_service.py      # OpenAI API サービス
│       └── places_service.py      # Google Places API サービス
├── frontend/
│   ├── app/
│   │   ├── globals.css     # グローバルスタイル
│   │   ├── layout.tsx      # レイアウトコンポーネント
│   │   └── page.tsx        # メインページ
│   ├── package.json        # フロントエンド依存関係
│   ├── next.config.js      # Next.js設定
│   ├── tailwind.config.js  # Tailwind CSS設定
│   └── postcss.config.js   # PostCSS設定
├── config.py               # 設定ファイル
├── requirements.txt        # Python依存関係
├── start_backend.py        # バックエンド起動スクリプト
├── env.example            # 環境変数テンプレート
└── README.md              # このファイル
```

## 今後の拡張予定

### Level 2機能
- ユーザーの過去の選択履歴の学習
- 個人の好みに基づいたパーソナライズ
- 予算感の自動学習

### Level 3機能
- 自動予約システム
- ブラウザ操作による予約代行
- 空席状況の確認と代替案提案

## トラブルシューティング

### よくある問題

1. **APIキーエラー**
   - `config.py`でAPIキーが正しく設定されているか確認

2. **Google Places APIで結果が返らない**
   - Google Places APIキーが有効か確認
   - APIの利用制限に達していないか確認

3. **フロントエンドでAPIが呼べない**
   - バックエンドサーバーが起動しているか確認（localhost:5000）
   - CORS設定が正しく動作しているか確認

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

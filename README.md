# French Flashcard Study

フラッシュカード式フランス語学習アプリ（Streamlit + FastAPI + ChatGPT API）

## 機能
- CSV データから難易度別（初級/中級/上級）の単語を表示
- ChatGPT API で日本語訳を自動生成
- 間隔反復アルゴリズム（忘却曲線）による学習管理

## 技術スタック
- Frontend: Streamlit
- Backend: FastAPI × 2（レベル判定・翻訳API）
- Data: Pandas + CSV
- Translation: OpenAI GPT-4

## セットアップ

```bash
# 1. クローン・環境構築
git clone https://github.com/Yumiuse/french_flashcard_study.git
cd french_flashcard_study
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. 環境変数設定（.envファイル作成）
echo "OPENAI_API_KEY=your_api_key_here" > .env

# 3. API起動（別ターミナルで実行）
uvicorn backend_level_FastAPI:app --port 8014 &
uvicorn chatGPTAPI:app --port 8000 &

# 4. アプリ起動
streamlit run frontend_streamlit.py
```

ブラウザで `http://localhost:8501` を開く

## ファイル構成
- `frontend_streamlit.py` - メインアプリ
- `backend_level_FastAPI.py` - レベル判定API
- `chatGPTAPI.py` - 翻訳API  
- `data/` - CSV データ・フィードバック記録

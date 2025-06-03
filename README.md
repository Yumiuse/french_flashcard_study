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


## セットアップ方法

```bash
# リポジトリをクローン・仮想環境作成
git clone https://github.com/Yumiuse/french_flashcard_study.git
cd french_flashcard_study
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 環境変数（OpenAI APIキー設定）
echo "OPENAI_API_KEY=your_api_key_here" > .env

# 以下の順番で起動してください

# 1) レベル判定 & フィードバック用 FastAPI (ポート8014)
uvicorn backend_level_FastAPI:app --port 8014

# 2) 翻訳用 FastAPI (ポート8000)
uvicorn chatGPTAPI:app --port 8000

# 3) Streamlit アプリ (ポート8501)
streamlit run frontend_streamlit.py

ブラウザで `http://localhost:8501` にアクセス

## ファイル構成
- `frontend_streamlit.py` - メインアプリ
- `backend_level_FastAPI.py` - レベル判定API
- `chatGPTAPI.py` - 翻訳API  
- `data/` - CSV データ・フィードバック記録

# フランス語単語レベルチェッカー 内容はREADME.MDに記載
# 要件クリアのためのフランス語難易度チェックアプリ

##from fastapi import FastAPI, Form, HTTPException
##from fastapi.responses import HTMLResponse
##import pandas as pd
##import numpy as np
##from pydantic import BaseModel
##import spacy
##from KIKAGAKU_last_api import extract_grammar_info
##
##
##app = FastAPI()
##
### 仮のモデル処理（ここでは単に入力をそのまま返すだけの例）
##def predict_level(lemme: str):
##    # ここで実際のモデルを使って予測を行うことができます。
##    # 今回は単に入力単語の長さによってレベルを決める仮のロジックです。
##    length = len(lemme)
##    if length <= 4:
##        return "初級 (Débutant)"
##    elif length <= 7:
##        return "中級 (Intermédiaire)"
##    else:
##        return "上級 (Avancé)"
##
### ルートページのフォーム (GET /)
##@app.get("/", response_class=HTMLResponse)
##async def read_form():
##    return """
##   <html>
##    <head>
##        <title>French Word Level Checker</title>
##    </head>
##    <body>
##        <h1>Enter a French word to check its level</h1>
##        <form id="wordForm">
##            <input name="lemme" type="text" placeholder="Enter a French word" required/>
##            <button type="submit">Submit</button>
##        </form>
##        <div id="result"></div>
##
##        <script>
##            document.getElementById('wordForm').onsubmit = async (e) => {
##                e.preventDefault();  // フォームの送信を防ぎます
##                const form = e.target;
##                const lemme = form.elements['lemme'].value; // フォームから単語を取得
##
##                const response = await fetch('/predict/', {
##                    method: 'POST',
##                    headers: {
##                        'Content-Type': 'application/json',  // JSON形式でデータを送信することを指定
##                    },
##                    body: JSON.stringify({ lemme: lemme })  // フォームのデータをJSONに変換
##                });
##
##                if (!response.ok) {
##                    document.getElementById('result').innerText = 'Error fetching data from server';
##                    return;
##                }
##
##                const result = await response.json();  // JSONレスポンスを解析
##                document.getElementById('result').innerText = `単語 '${result.word}' のレベルは→ ${result.level}`;
##            };
##        </script>
##    </body>
##</html>
##
##    """
##
##from pydantic import BaseModel
##
##class PredictionRequest(BaseModel):
##    lemme: str
##
### 予測API (POST /predict/)
##@app.post("/predict/")
##async def predict(request: PredictionRequest):
##    lemme = request.lemme
##    try:
##        print(f"Received input: lemme={lemme}")
##
##        # 仮の予測関数を使ってレベルを予測
##        level_name = predict_level(lemme)
##
##        print(f"Predicted level: {level_name}")
##
##        # レスポンスとして返す
##        return {"word": lemme, "level": level_name}
##    
##    except Exception as e:
##        print(f"Error during prediction: {str(e)}")
##        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
##
##class TranslationRequest(BaseModel):
##    word: str
##
###翻訳関数の呼び出し   
##from KIKAGAKU_last_api import translate_word_with_chatgpt
##
##@app.post("/translate/")
##async def translate(request: TranslationRequest):
##    word = request.word
##    try:
##        translation = await translate_word_with_chatgpt(word)
##        return {"translation": translation}
##    except Exception as e:
##        raise HTTPException(status_code=500, detail=str(e))
##
##
##def get_grammar_from_csv(word: str):
##    # CSV ファイルを読み込む（必要ならキャッシュすることも検討）
##    df = pd.read_csv('input/mettre_fin_Lexique_translated_v6w (4).csv')
##    # 'ortho' 列が入力単語と一致する行を抽出
##    row = df.loc[df['ortho'] == word]
##    if row.empty:
##        return ""
##    # 複数該当する場合は先頭の行を使用
##    row = row.iloc[0]
##    fields = []
##    for col in ['cgram_jp', 'infover_full_translation', 'genre_jp']:
##        value = str(row.get(col, "")).strip()
##        if value:
##            fields.append(value)
##    return " / ".join(fields)
##
##class GrammarRequest(BaseModel):
##    word: str
##
##class GrammarResponse(BaseModel):
##    grammar: str
##
##@app.post("/grammar/", response_model=GrammarResponse)
##def get_grammar_info(request: GrammarRequest):
##    grammar = get_grammar_from_csv(request.word)
##    return GrammarResponse(grammar=grammar)
##
##
##
### アプリケーションの実行
##if __name__ == "__main__":
##    import uvicorn
##    uvicorn.run(app, host="127.0.0.1", port=8014, reload=True)


#  uvicorn level_checker:app --reload --port 8014
#

"""以下の変更を加えました：

predict_level関数: この関数は単純に単語の長さに基づいて難易度レベルを返します。
Webページ: 単語のレベルをチェックするためのフォームを含む単純なHTMLページを提供します。
/predict/エンドポイント: 予測を行い、結果をJSONで返します。
文法情報の取得: CSVから文法情報を取得する関数を実装し、それをAPIで公開します。"""
##
##from fastapi import FastAPI, HTTPException
##from fastapi.responses import HTMLResponse
##import pandas as pd
##from pydantic import BaseModel
##
##app = FastAPI()
##
##def predict_level(lemme: str):
##    length = len(lemme)
##    if length <= 4:
##        return "初級 (Débutant)"
##    elif length <= 7:
##        return "中級 (Intermédiaire)"
##    else:
##        return "上級 (Avancé)"
##
##@app.get("/", response_class=HTMLResponse)
##async def read_form():
##    return """
##    <html>
##        <head>
##            <title>French Word Level Checker</title>
##        </head>
##        <body>
##            <h1>Enter a French word to check its level</h1>
##            <form id="wordForm">
##                <input name="lemme" type="text" placeholder="Enter a French word" required/>
##                <button type="submit">Submit</button>
##            </form>
##            <div id="result"></div>
##            <script>
##                document.getElementById('wordForm').onsubmit = async (e) => {
##                    e.preventDefault();
##                    const form = e.target;
##                    const lemme = form.elements['lemme'].value;
##                    const response = await fetch('/predict/', {
##                        method: 'POST',
##                        headers: { 'Content-Type': 'application/json' },
##                        body: JSON.stringify({ lemme: lemme })
##                    });
##                    if (!response.ok) {
##                        document.getElementById('result').innerText = 'Error fetching data from server';
##                        return;
##                    }
##                    const result = await response.json();
##                    document.getElementById('result').innerText = `単語 '${result.word}' のレベルは→ ${result.level}`;
##                };
##            </script>
##        </body>
##    </html>
##    """
##
##class PredictionRequest(BaseModel):
##    lemme: str
##
##@app.post("/predict/")
##async def predict(request: PredictionRequest):
##    lemme = request.lemme
##    level_name = predict_level(lemme)
##    return {"word": lemme, "level": level_name}
##
##def get_grammar_from_csv(word: str):
##    df = pd.read_csv('input/mettre_fin_Lexique_translated_v6w (4).csv')
##    row = df.loc[df['ortho'] == word]
##    if row.empty:
##        return ""
##    row = row.iloc[0]
##    fields = []
##    for col in ['cgram_jp', 'infover_full_translation', 'genre_jp']:
##        value = str(row.get(col, "")).strip()
##        if value:
##            fields.append(value)
##    return " / ".join(fields)
##
##class GrammarRequest(BaseModel):
##    word: str
##
##class GrammarResponse(BaseModel):
##    grammar: str
##
##@app.post("/grammar/", response_model=GrammarResponse)
##def get_grammar_info(request: GrammarRequest):
##    grammar = get_grammar_from_csv(request.word)
##    return GrammarResponse(grammar=grammar)
##
##if __name__ == "__main__":
##    import uvicorn
##    uvicorn.run(app, host="127.0.0.1", port=8014, reload=True)
    
"""このコードでは、APIの動作に必要な基本的な構造を持っており、単語の難易度レベルを予測する機能、
単語のレベルをウェブページでチェックする機能、そして文法情報をCSVから抽出して返す機能が含まれています。
次に、KIKAGAKU_last_api.pyの修正を行います。"""


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import httpx
import os
from dotenv import load_dotenv
#追記
from fastapi.encoders import jsonable_encoder
import csv

from pydantic import BaseModel

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

INTERVALS = {
    "覚えた！🟢":    [timedelta(days=1), timedelta(days=3), timedelta(days=7)],
    "うる覚え🟡":  [timedelta(minutes=10), timedelta(hours=1), timedelta(days=1)],
    "覚えていない！🔴":[timedelta(minutes=1), timedelta(minutes=5), timedelta(minutes=15)],
}

def compute_next_times(feedback_key: str):
    # Tokyo ローカルタイムで「今」を取得
    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    deltas = INTERVALS.get(feedback_key, INTERVALS["うる覚え🟡"])
    return [now + d for d in deltas]





# .envファイルから環境変数をロード
load_dotenv('/Volumes/SP PC60/ChatGPT_API/.env')

# OpenAI APIキーの取得
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY が見つかりません！")

# CSVファイルの読み込み（例として1度だけグローバルにロード）
df = pd.read_csv('input/mettre_fin_Lexique_translated_v6w_修正済み.csv')
if df.empty:
    raise HTTPException(status_code=500, detail="CSV file is empty or could not be loaded")

app = FastAPI()
#追記
# レベル情報のマッピング辞書
level_mapping = {
    1: "初級",
    2: "中級",
    3: "上級"
}


# リクエスト用モデル
class TranslationRequest(BaseModel):
    word: str
#追記
class PredictionRequest(BaseModel):
    lemme: str
    card_id: int


# ChatGPT APIを利用して翻訳する非同期関数
async def translate_word_with_chatgpt(word: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a concise translator."},
            {"role": "user", "content": f"Translate the French word '{word}' to Japanese, focusing on conveying its meaning."}
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        # ChatGPT APIがエラーを返した場合の処理
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"OpenAI API error: {response.text}")
        
        data = response.json()
        # デバッグ用
        print("API Response Data:", data)
        
        if 'error' in data:
            raise HTTPException(status_code=500, detail=f"API Error: {data['error'].get('message', 'Unknown error')}")
        if 'choices' not in data or not data['choices']:
            raise HTTPException(status_code=500, detail="No translation choices found in the API response.")
        
        return data['choices'][0]['message']['content'].strip()

# 翻訳結果の整形関数（例として、CSVから品詞情報を参照して整形）
def format_translation(selected_word, translation):
    part_of_speech = selected_word.get('cgram', "")
    if part_of_speech == 'NOM':
        return f"{translation}（名詞）"
    elif part_of_speech == 'VER':
        return f"{translation}（動詞）"
    elif part_of_speech == 'ADV':
        return f"{translation}（副詞）"
    elif part_of_speech == 'ADJ':
        return f"{translation}（形容詞）"
    return translation

# /translate/ エンドポイント
@app.post("/translate/")
async def translate(request: TranslationRequest):
    word = request.word
    # 入力された単語がCSV内に存在するか確認
    if word not in df['ortho'].values:
        raise HTTPException(status_code=404, detail="Word not found in CSV")
    selected_word = df[df['ortho'] == word].iloc[0]
    # ChatGPT APIを使って翻訳を取得
    translation = await translate_word_with_chatgpt(word)
    # 必要に応じて整形する
    translation_info = format_translation(selected_word, translation)
    return {"translation": translation_info}

#@app.post("/predict/")
#async def predict(data: dict):
    # ここでデータを処理してレベルを判定
    #return {"level": "calculated_level"}

@app.post("/predict/")
async def predict(request: PredictionRequest): # 引数を Pydantic モデルに変更
    # データフレームからレベル情報を検索
    # Streamlitから送られるキー 'lemme' を使って、CSVの 'ortho' 列を検索？
    # CSVの 'id' 列と Streamlitから送られる 'card_id' も比較
    word_data = df[(df['ortho'] == request.lemme) & (df['id']   ==request.card_id)]
    if word_data.empty:
        raise HTTPException(status_code=404, detail="Word not found")

    # レベル数値を取得し、マッピング辞書で変換
    # CSVのレベル列が 'level' であることを確認
    level_num = int(word_data.iloc[0]['level'])
    level_text = level_mapping.get(level_num, "未定義のレベル") # マッピングを使う
    print(f"Level Number: {level_num}, Level Text: {level_text}") # デバッグ用print

    # レベルテキストを返す
    response_data = {"level": level_text}
    return jsonable_encoder(response_data) # 元のコードに合わせて jsonable_encoder を使用
    # または return response_data でも通常は動作します

# ② 追記：FeedbackRequest モデル定義
class FeedbackRequest(BaseModel):
    user_id: str
    card_id: int
    feedback: str
    feedback_time: datetime
    review_count: int
    next_review_time_1: datetime
    next_review_time_2: datetime
    next_review_time_3: datetime
    next_review1: bool
    next_review2: bool
    next_review3: bool

# ③ 追記：CSV 追記用エンドポイント
FEEDBACK_CSV = os.path.join(os.path.dirname(__file__), "feedback.csv")

@app.post("/feedback/")
async def record_feedback(req: FeedbackRequest):
    # ログ出力（そのまま）
    print("DEBUG /feedback/ called with:", req.dict())

    # フィードバック時刻はクライアントから来るのでそのまま ISO 文字列化
    # CSV 最終列の「recorded_at」はサーバー側のローカル時間に
    recorded_at = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat()

    row = [
        req.user_id,
        req.card_id,
        req.feedback,
        req.feedback_time.isoformat(),         # 送られてきた feedback_time
        req.review_count,
        req.next_review_time_1.isoformat(),
        req.next_review_time_2.isoformat(),
        req.next_review_time_3.isoformat(),
        int(req.next_review1),
        int(req.next_review2),
        int(req.next_review3),
        recorded_at,
    ]
    print("DEBUG writing row:", row)

    try:
        with open(FEEDBACK_CSV, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)
        print("DEBUG write successful")
    except Exception as e:
        print("ERROR in record_feedback:", e)
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "ok"}

# ──────────────────────────────────────────

# ④ 既存の if __name__ == "__main__": 以下はそのまま残す

if __name__ == "__main__":
    import uvicorn
    # ポートは必要に応じて変更してください。ここでは8014で起動
    uvicorn.run(app, host="127.0.0.1", port=8014)
    #uvicorn.run(app, host="127.0.0.1", port=8014, reload=True)



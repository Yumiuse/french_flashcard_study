# # from fastapi import FastAPI, HTTPException
# # from pydantic import BaseModel
# # import requests
# # import os
# # import uvicorn

# #        raise HTTPException(status_code=response.status_code, detail=f"Error in translation API: {error_detail}")
# app = FastAPI()

# # class TranslationRequest(BaseModel):  # Defines the structure of the request data
# #     word: str

# # # Root endpoint for testing
# # @app.post("/translate-api/")
# # async def translate_api(request: TranslationRequest):
# #     url = "https://api.openai.com/v1/chat/completions"  # Correct endpoint for chat models
# #     headers = {
# #         "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
# #     }
# #     data = {
# #         "model": "gpt-3.5-turbo",  # Provide the required model parameter
# #         "messages": [
# #             {"role": "system", "content": "You are a translator."},
# #             {"role": "user", "content": f"Translate the French word '{request.word}' to Japanese and use it in a sentence."}
# #         ],
# #         "max_tokens": 100
# #     }
    
# #     response = requests.post(url, headers=headers, json=data)
    
# #     if response.status_code == 200:
# #         return response.json()['choices'][0]['message']['content']  # Adjust response to match the chat API structure
# #     else:
# #         error_detail = response.json() if response.text else "No additional error info"
# #         print(f"Error from Translation API (status {response.status_code}): {error_detail}")
# #  
# # # Second translation endpoint (from api_endpoint.py)
# # @app.post("/translate-endpoint/")
# # async def translate_endpoint(request: TranslationRequest):  # Accepting JSON request body
# #     url = "https://api.openai.com/v1/chat/completions"
# #     headers = {
# #         "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
# #     }
# #     data = {
# #         "model": "gpt-3.5-turbo",
# #         "messages": [
# #             {"role": "system", "content": "You are a translator."},
# #             {"role": "user", "content": f"Translate the French word '{request.word}' to Japanese and use it in a sentence."}
# #         ],
# #         "max_tokens": 100
# #     }
    
# #     response = requests.post(url, headers=headers, json=data)
    
# #     if response.status_code == 200:
# #         return response.json()['choices'][0]['message']['content']
# #     else:
# #         error_detail = response.json() if response.text else "No additional error info"
# #         print(f"Error from Translation API (status {response.status_code}): {error_detail}")

# #         raise HTTPException(status_code=response.status_code, detail=f"Error in translation API: {error_detail}")
# #-----------------------------
##import pandas as pd
##from fastapi import FastAPI, HTTPException
##from pydantic import BaseModel
##import httpx
##import os
##
##app = FastAPI(debug=True)
##
### CSVファイルを読み込み
##df = pd.read_csv('input/mettre_fin_Lexique_translated_v6w (4).csv')
##if df.empty:
##    raise HTTPException(status_code=500, detail="CSV file is empty or could not be loaded")
##
##class TranslationRequest(BaseModel):
##    word: str
##
##class GrammarRequest(BaseModel):
##    word: str
##
##class GrammarResponse(BaseModel):
##    grammar: str
##
##@app.get("/")  # ルートエンドポイント
##async def read_root():
##    return {"message": "Hello World"}
##
##def select_balanced_words(df, num_cards=50):
##    # 各レベルから単語を選択
##    beginner_words = df[df['level'] == '初級']
##    intermediate_words = df[df['level'] == '中級']
##    advanced_words = df[df['level'] == '上級']
##    num_per_level = num_cards // 3
##    remainder = num_cards % 3
##    level_counts = [num_per_level + (1 if i < remainder else 0) for i in range(3)]
##    selected_words = pd.concat([
##        beginner_words.sample(n=level_counts[0], replace=True, random_state=42),
##        intermediate_words.sample(n=level_counts[1], replace=True, random_state=42),
##        advanced_words.sample(n=level_counts[2], replace=True, random_state=42)
##    ])
##    return selected_words.sample(frac=1).reset_index(drop=True)
##
##@app.post("/select_balanced_words/")
##async def get_balanced_words(num_cards: int = 50):
##    selected_words = select_balanced_words(df, num_cards)
##    if selected_words.empty:
##        raise HTTPException(status_code=404, detail="No words found for the requested number of cards")
##    return {"words": selected_words['ortho'].tolist()}
##
##@app.post("/translate/")
##async def translate(request: TranslationRequest):
##    if request.word not in df['ortho'].values:
##        raise HTTPException(status_code=404, detail="Word not found in CSV")
##    selected_word = df[df['ortho'] == request.word].iloc[0]
##    translation = await translate_word_with_chatgpt(request.word)
##    translation_info = format_translation(selected_word, translation)
##    return {"translation": translation_info}
##
##async def translate_word_with_chatgpt(word: str) -> str:
##    url = "https://api.openai.com/v1/chat/completions"
##    headers = {
##        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
##        "Content-Type": "application/json"
##    }
##    payload = {
##        "model": "gpt-4",
##        "messages": [{"role": "system", "content": "You are a concise translator."},
##                     {"role": "user", "content": f"Translate the French word '{word}' to Japanese, focusing on conveying its meaning."}]
##    }
##    async with httpx.AsyncClient() as client:
##        response = await client.post(url, headers=headers, json=payload)
##        if response.status_code == 200 and 'choices' in response.json() and response.json()['choices']:
##            return response.json()['choices'][0]['message']['content']
##        raise HTTPException(status_code=response.status_code, detail="Translation API error")
##
##def format_translation(selected_word, translation):
##    # 品詞に応じた追加情報を付加
##    part_of_speech = selected_word['cgram']
##    if part_of_speech == 'NOM':
##        return f"{translation}（名詞）"
##    elif part_of_speech == 'VER':
##        return f"{translation}（動詞）"
##    elif part_of_speech == 'ADV':
##        return f"{translation}（副詞）"
##    elif part_of_speech == 'ADJ':
##        return f"{translation}（形容詞）"
##    return translation  # 他の品詞については単純な翻訳のみを返す
##
##@app.post("/grammar/", response_model=GrammarResponse)
##def get_/Users/yumikosawa/Downloads/tryのコピー2.pygrammar_info(request: GrammarRequest):
##    # 文法情報をCSVファイルから取得
##    row = df[df['ortho'] == request.word]  # 'request.word' を使って適切な行を検索
##    if row.empty:
##        return GrammarResponse(grammar="文法情報なし")
##    # 複数該当する場合は先頭の行を採用
##    row = row.iloc[0]
##    
##    fields = []
##    # cgram_jp, infover_full_translation, genre_jp の順で取得、空欄はスキップ
##    for col in ['cgram_jp', 'infover_full_translation', 'genre_jp']:
##        value = str(row.get(col, "")).strip()
##        if value:
##            fields.append(value)
##    grammar = " / ".join(fields)
##    return GrammarResponse(grammar=grammar)
##
##if __name__ == "__main__":
##    import uvicorn
##    uvicorn.run(app, host="0.0.0.0", port=8000)
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv

# .env ファイルを読み込む
load_dotenv('/Volumes/SP PC60/ChatGPT_API/.env')

# 環境変数の取得
api_key = os.getenv("OPENAI_API_KEY")

print("APIキー:", api_key)  # 確認用

if not api_key:
    raise ValueError("OPENAI_API_KEY が見つかりません！環境変数または .env ファイルを確認してください。")

app = FastAPI(debug=True)

import os

BASE_DIR = os.path.dirname(__file__)
csv_path = os.path.join(BASE_DIR, 'data', 'mettre_fin_Lexique_translated_v6w_修正済み.csv')
df = pd.read_csv(csv_path, dtype={"level": int})


df = pd.read_csv('data/mettre_fin_Lexique_translated_v6w_修正済み.csv', dtype={"level": int})

if df.empty:
    raise HTTPException(status_code=500, detail="CSV file is empty or could not be loaded")

class TranslationRequest(BaseModel):
    word: str
    
class GrammarRequest(BaseModel):
    word: str

class GrammarResponse(BaseModel):
    grammar: str

@app.get("/")  # ルートエンドポイント
async def read_root():
    return {"message": "Hello World"}

def select_balanced_words(df, num_cards=50):
    beginner_words = df[df['level'] == '初級']
    intermediate_words = df[df['level'] == '中級']
    advanced_words = df[df['level'] == '上級']
    num_per_level = num_cards // 3
    remainder = num_cards % 3
    level_counts = [num_per_level + (1 if i < remainder else 0) for i in range(3)]
    selected_words = pd.concat([
        beginner_words.sample(n=level_counts[0], replace=True, random_state=42),
        intermediate_words.sample(n=level_counts[1], replace=True, random_state=42),
        advanced_words.sample(n=level_counts[2], replace=True, random_state=42)
    ])
    return selected_words.sample(frac=1).reset_index(drop=True)

@app.post("/select_balanced_words/")
async def get_balanced_words(num_cards: int = 50):
    selected_words = select_balanced_words(df, num_cards)
    if selected_words.empty:
        raise HTTPException(status_code=404, detail="No words found for the requested number of cards")
    return {"words": selected_words['ortho'].tolist()}

import re

def clean_japanese_translation(translation):
    # “、” と “,” も残す
    translation = re.sub(r'[^\u3040-\u30FF\u3400-\u9FFF\s/、,]', '', translation).strip()
    # 以下はおなじ
    translation = re.sub(r'\(.*?\)', '', translation).strip()
    translation = re.sub(r'\s+', ' ', translation).strip()
    translation = re.sub(r'[^\w\s/、,]', '', translation).strip()
    translation = re.sub(r'[\s/、,]+$', '', translation).strip()
    translation = re.sub(
        r'(動詞|形容詞|名詞|副詞|助動詞|連体詞|接続詞|感動詞|形状詞|過去分詞)$',
        '', translation
    ).strip()
    return translation

@app.post("/translate/")
async def translate(request: TranslationRequest): # 引数を TranslationRequest (wordのみ) に戻すか確認
    word = request.word # word キーで ortho を受け取る想定

    # CSVから品詞情報を取得 (ortho で検索)
    # df と HTTPException は関数の外で定義されている前提
    row_data = df[df['ortho'] == word]
    if row_data.empty:
        # CSVに単語が見つからない場合
        # raise HTTPException(status_code=404, detail=f"Word '{word}' not found in CSV")
        part_of_speech_jp = '不明' # 不明として処理を続ける場合
    else:
        # 'cgram_jp' 列から日本語の品詞を取得 (列名が違う場合は要修正)
        part_of_speech_jp = row_data.iloc[0].get('cgram_jp', '不明')

    # 修正したChatGPT呼び出し関数に word(ortho) と pos_jp を渡す
    translation_result = await translate_word_with_chatgpt(word, part_of_speech_jp)

    # clean_japanese_translation の呼び出しは削除したまま
    # ChatGPTからの結果をそのまま返す
    return {"translation": translation_result}

# KIKAGAKU_last_apiのコピー2.py 内の関数を修正

async def translate_word_with_chatgpt(word: str, cgram: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json"
    }

    # システムプロンプト（改行禁止・JSON/Japanese only などの厳格指示）
    system_prompt = """
あなたはフランス語–日本語辞書です。
以下のルールに**厳格**に従って出力してください。
1. 出力は**必ず1行**だけ。
2. **改行文字を一切含めない**。
3. 必ず「訳1, 訳2, 訳3」のように**半角コンマ＋スペース**で区切って返し、それ以外の区切り文字は使わないでください。
4. それ以外の文字（説明文、品詞、活用情報、読み仮名など）は一切含めない。
5. カタカナ表記も絶対に生成しない。
"""

    user_prompt = (
        f"French word: “{word}”  Part of speech: {cgram}\n"
        "Translate its meaning into Japanese; output up to three base‐form meanings "
        "separated by commas, with no extra text."
    )

    payload = {
        "model": "gpt-4-0613",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ],
        "temperature": 0.0,
        "max_tokens": 60
    }

    async with httpx.AsyncClient() as client:
        try:
            print(f"DEBUG: Sending to OpenAI: {word=} {cgram=}")
            response = await client.post(url, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()
        except httpx.RequestError as e:
            print(f"ERROR: Connection error: {e}")
            raise HTTPException(status_code=503, detail=str(e))
        except httpx.HTTPStatusError as e:
            print(f"ERROR: Status {e.response.status_code}: {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)

        data = response.json()
        print(f"DEBUG: Raw response: {data}")

        if not data.get("choices"):
            raise HTTPException(status_code=500, detail="No choices in OpenAI response")

        # モデルの出力を取り出す
        text = data["choices"][0]["message"]["content"].strip()
        print(f"DEBUG: Raw text: {text}")

    # --- ここから後処理 ---
    # ① 一行目だけ
    first_line = text.split("\n", 1)[0].strip()
    print(f"DEBUG: First line: {first_line}")

    # ② カンマ or 全角コンマ がなければ「ていた」「した」「る」で分割
    if '、' in first_line or ',' in first_line:
        parts = re.split(r'[、,]', first_line)
    else:
        # 動詞の過去進行形「ていた」、過去形「した」、辞書形「る」などで区切る
        parts = re.findall(r'.+?(?:ていた|した|る)', first_line)
        print(f"DEBUG: Fallback parts via regex: {parts}")

    # 余分な要素を除き、最大３つ
    parts = [p.strip() for p in parts if p.strip()][:3]
    print(f"DEBUG: Final parts to join: {parts}")

    # ③ “、” で再結合して返す
    result = "、".join(parts)
    print(f"DEBUG: Final result: {result}")
    return result

@app.post("/grammar/", response_model=GrammarResponse)
def get_grammar_info(request: GrammarRequest):
    row = df[df['ortho'] == request.word]
    if row.empty:
        return GrammarResponse(grammar="文法情報なし")
    row = row.iloc[0]
    fields = []
    for col in ['cgram_jp', 'infover_full_translation', 'genre_jp']:
        value = str(row.get(col, "")).strip()
        if value:
            fields.append(value)
    grammar = " / ".join(fields)
    return GrammarResponse(grammar=grammar)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



@app.get("/debug/routes")
async def get_routes():
    return [{"path": route.path, "methods": list(route.methods)} for route in app.routes]


# python api.py
# uvicorn api:app --reload
# uvicorn api:app --host 0.0.0.0 --port 8000
#lsof -i:8000

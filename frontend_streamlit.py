# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os

# --- セッション状態の初期化 ---
if 'index' not in st.session_state:
    st.session_state.index = 0
if 'flip' not in st.session_state:
    st.session_state.flip = True
if 'active_feedback' not in st.session_state:
    st.session_state.active_feedback = None
if 'feedback_message' not in st.session_state:
    st.session_state.feedback_message = ""
if 'review_count' not in st.session_state: # ユーザーの元コードに存在
    st.session_state.review_count = 0
# next_review_time_X はセッション状態では直接管理しない

# ── Ebbinghaus モデルの定数定義 ──
RECALL_THRESHOLD = 0.8
DEFAULT_STABILITY = 2.0
STABILITY_FACTORS = {
    "覚えた！🟢": 1.3,
    "うる覚え🟡": 1.0,
    "覚えていない！🔴": 0.7
}

def compute_next_times(feedback_key: str,
                       last_review: datetime = None,
                       initial_stability: float = None):
    # last_review がNoneなら現在のJST時刻、指定されていればそれをJSTに変換 (またはJSTと仮定)
    now_for_calc = datetime.now(ZoneInfo("Asia/Tokyo"))
    if last_review is not None:
        if last_review.tzinfo is None: # ナイーブならJSTと仮定
            now_for_calc = ZoneInfo("Asia/Tokyo").localize(last_review)
        else: # awareならJSTに変換
            now_for_calc = last_review.astimezone(ZoneInfo("Asia/Tokyo"))
    
    S = initial_stability if initial_stability is not None else DEFAULT_STABILITY
    times = []
    # now_for_calc をループ内で更新するために、別の変数にコピー
    current_review_time = now_for_calc 
    for _ in range(3):
        t_days = -S * math.log(RECALL_THRESHOLD)
        next_time = current_review_time + timedelta(days=t_days)
        times.append(next_time)
        current_review_time = next_time # 次の計算のために更新
        factor = STABILITY_FACTORS.get(feedback_key, STABILITY_FACTORS["うる覚え🟡"])
        S *= factor
    return times

# --- CSS/タイトル ---
st.markdown("""
<style>
/* h1 の上マージンを小さくする */
h1 {
  margin-top: 0.4rem !important;
  margin-bottom: 0.5rem !important;
}
/* もしさらに細かく調整したいなら .block-container にも */
.block-container {
  padding-top: 1rem !important;
}
 .custom-font {
     font-size: 15px;
 }
 .custom-card {
     position: relative;
     height: 50vh;
     width: 60vw;
     background-color: rgba(255, 250, 205, 0.8);
     display: flex;
     justify-content: center;
     align-items: center;
     margin: auto;
     border-radius: 10px;
     padding: 20px;
     font-size: 24px;
     color: black;
     font-family: 'Arial', sans-serif;
     font-weight: bold;
     letter-spacing: 2px;
     overflow: auto;
 }
  .level-text {
       color: #808080;
 }
 div.stButton > button {
     position: absolute;
     top: -30px;
     right: 10px;
     height: 50px;
     width: 200px;
     font-size: 24px;
     background-color: #40e0d0;
     color: white;
     border-radius: 10px;
     border: none;
     cursor: pointer;
     z-index: 10;
 }
 div.stButton > button:hover {
     background-color: #20b2aa;
 }
 </style>
 <div class='custom-font'>スペースドレペティション</div>
 """, unsafe_allow_html=True)

st.markdown("""
<h1 style="font-size:1.7rem; font-weight:bold; margin-bottom:0.5rem;">
  フランス語フラッシュカード学習
</h1>
""", unsafe_allow_html=True)

# --- データロード ---
@st.cache_data
def load_data():
    try:
        return pd.read_csv('data/mettre_fin_Lexique_translated_v6w_修正済み.csv').sample(frac=1).reset_index(drop=True)
    except FileNotFoundError:
        st.error("語彙ファイル 'data/mettre_fin_Lexique_translated_v6w_修正済み.csv' が見つかりません。")
        return pd.DataFrame() # 空のDataFrameを返す

df = load_data() # df_all_cards のこと

# --- feedback.csv 読み込み ---
try:
    df_fb = pd.read_csv("data/feedback.csv")
except FileNotFoundError: # ファイルが存在しない場合も考慮
    df_fb = pd.DataFrame(columns=['card_id', 'next_review_time_1', 'next_review_time_2', 'next_review_time_3']) # 必要な列を持つ空DF
except Exception as e: # その他の読み込みエラー
    st.error(f"feedback.csvの読み込みに失敗しました: {e}")
    df_fb = pd.DataFrame()

# --- 次回復習タイミングが来たカード抽出 ---
def get_due_cards(df_vocab, df_fb_local):
    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    due_card_ids = []

    if df_fb_local.empty or df_vocab.empty:
        return pd.DataFrame(columns=df_vocab.columns if not df_vocab.empty else None)

    for _, row in df_fb_local.iterrows():
        card_id_val = row.get("card_id") # card_id が存在しない行はスキップ
        if pd.isna(card_id_val):
            continue

        for t_col in ["next_review_time_1", "next_review_time_2", "next_review_time_3"]:
            t_str = str(row.get(t_col, "")) # 文字列に変換して安全に処理
            try:
                if t_str and t_str.lower() != "nan" and t_str.lower() != "nat" and t_str.strip() != "":
                    t_dt = datetime.fromisoformat(t_str)
                    # タイムゾーン処理: fromisoformatがawareなオブジェクトを返せばそれを使い、naiveならJSTを付与
                    if t_dt.tzinfo is None:
                        t_dt_aware = ZoneInfo("Asia/Tokyo").localize(t_dt)
                    else:
                        t_dt_aware = t_dt.astimezone(ZoneInfo("Asia/Tokyo"))
                    
                    if t_dt_aware <= now:
                        due_card_ids.append(card_id_val)
                        break 
            except ValueError: # fromisoformatがパースできない場合など
                pass # 無視またはログ記録
            except Exception: # その他の予期せぬエラー（例：localizeやastimezoneでのエラー）
                pass 
                
    due_card_ids = list(set(due_card_ids))
    if due_card_ids:
        cards_due_df = df_vocab[df_vocab["id"].isin(due_card_ids)].copy() # .copy()でワーニング回避
        return cards_due_df
    else:
        return pd.DataFrame(columns=df_vocab.columns if not df_vocab.empty else None)

# --- 出題候補決定 ---
candidate_df = pd.DataFrame() # candidate_dfを初期化

if df.empty: # 全カードデータ (df) が空の場合
    st.error("語彙データが空です。CSVファイルを確認してください。")
    st.stop() # 処理を停止

# df_fbが空でない場合のみcards_dueを計算
if not df_fb.empty:
    cards_due = get_due_cards(df, df_fb)
else:
    cards_due = pd.DataFrame(columns=df.columns if not df.empty else None) # df_fbが空ならcards_dueも空(カラムはdfに合わせる)

if not cards_due.empty:
    candidate_df = cards_due
else:
    reviewed_ids = df_fb["card_id"].unique() if not df_fb.empty and "card_id" in df_fb.columns else []
    # df['id']が存在するか確認してからisinを使う
    if "id" in df.columns:
        unreviewed_df = df[~df["id"].isin(reviewed_ids)]
    else: # dfにid列がない場合、unreviewed_dfは空とするか、df全体とするか（ここでは空とする）
        unreviewed_df = pd.DataFrame(columns=df.columns)

    if not unreviewed_df.empty:
        candidate_df = unreviewed_df
    else:
        candidate_df = df # フォールバックとして全カードリスト

# candidate_df が最終的に空の場合の処理
if candidate_df.empty:
    if not df.empty: # 元のdfが空でなければ、それを最終候補とする
        candidate_df = df
        st.info("表示可能なカード候補が見つかりませんでした。全カードリストから表示します。")
    else: # ここに来ることはないはずだが念のため
        st.error("表示するカードがありません。")
        st.stop()


# --- index調整 ---
if 'id' not in candidate_df.columns and not candidate_df.empty:
    st.error("候補カードリストに'id'列が含まれていません。処理を中断します。")
    st.stop()

if st.session_state.index >= len(candidate_df):
    st.session_state.index = 0

# candidate_dfが空でないことを確実にしてからilocを実行
if candidate_df.empty:
    st.error("エラー: 表示するカード候補がありません。") # このエラーは上記のフォールバックで回避されるはず
    st.stop()

card = candidate_df.iloc[st.session_state.index]
st.session_state.card_id = card['id']

# --- API呼び出し ---
def translate_word(ortho, lemme):
    url = "http://127.0.0.1:8000/translate/"
    try:
        payload_data = {'word': ortho}
        response = requests.post(url, json=payload_data)
        response.raise_for_status()
        data = response.json()
        translation = data.get('translation', '翻訳APIエラー')
        return translation
    except requests.RequestException as e:
        return f"翻訳APIリクエスト失敗: {e}"
    except Exception as e:
        return f"翻訳中に予期せぬエラー: {e}"

def get_level(ortho, card_id):
    url = "http://127.0.0.1:8014/predict/"
    try:
        card_id_int = int(card_id)
        response = requests.post(url, json={'lemme': ortho, 'card_id': card_id_int})
        response.raise_for_status()
        level_text = response.json().get('level', "未定義")
        return level_text
    except requests.RequestException as e:
        return f"レベルAPIエラー: {e}"
    except ValueError: # card_idがintに変換できない場合
        return "カードID形式エラー"
    except Exception as e:
        return f"レベル取得中予期せぬエラー: {e}"


def record_feedback_api_call(payload): # 関数名を変更して区別
    url = "http://127.0.0.1:8014/feedback/"
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"フィードバック記録失敗: {e}")
        return {"error": str(e)}
    except Exception as e:
        st.error(f"フィードバック記録中予期せぬエラー: {e}")
        return {"error": str(e)}

# --- Flipボタン処理 ---
if st.button("Flip", key="main_flip_button"):
    if st.session_state.active_feedback is not None: # フィードバックが既に行われていたら次のカードへ
        if not candidate_df.empty: # candidate_dfが空でないことを確認
             st.session_state.index = (st.session_state.index + 1) % len(candidate_df)
        else: # 通常起こらないはずだが、万が一candidate_dfが空ならindexを0に
             st.session_state.index = 0
        st.session_state.active_feedback = None
        st.session_state.feedback_message = ""
        st.session_state.flip = True
    else: # フィードバック前なら現在のカードを表裏反転
        st.session_state.flip = not st.session_state.flip
    st.rerun()

# --- カード表示内容 ---
# (この部分は元のコードから変更なし)
if st.session_state.flip:
    word_surface  = card['ortho']
    lemma_surface = card.get('lemme', '')
    phon_surface  = card.get('phon', '')
    level_surface = get_level(card['ortho'], st.session_state.card_id)
    content_html = f"""
    <div style='text-align: center;'>
      <div style="font-size: 28px; font-weight: bold; margin-bottom: 4px;">
        {word_surface}
      </div>
      <div style="color: gray; font-style: italic; font-size: smaller; margin-bottom: 2px;">
        {("/" + phon_surface + "/") if phon_surface else ""}
      </div>
      <div style="color: gray; font-size: smaller; margin-bottom: 6px;">
        ({lemma_surface})
      </div>
      <span class='level-text' style="font-size: smaller;">
        {level_surface}
      </span>
    </div>
    """
else:
    translation = translate_word(card['ortho'], card.get('lemme', card['ortho']))
    pos = str(card.get('cgram_jp', '')).strip()
    inflection = str(card.get('infover_translated', '')).strip() # ここで活用情報を取得
    gender = str(card.get('genre_jp', '')).strip()
    
    display_parts = []
    if translation and not translation.startswith("翻訳API"): # APIエラーでない場合
        translations_list = [t.strip() for t in translation.split(',')]
        formatted_translations = "<br>".join([f"<b>{t}</b>" for t in translations_list])
        display_parts.append(formatted_translations)
    elif translation: # APIエラーの場合もそれを表示
        display_parts.append(f"<i>{translation}</i>")

    if pos:
        display_parts.append(f"【品詞】 {pos}")
    
    # 「【活用など】」の表示ロジック
    if inflection and inflection.lower() != 'nan':
        display_parts.append(f"【活用など】 {inflection}") # ここで追加
        
    if gender and gender.lower() != 'nan' and gender.lower() != 'nun':
        display_parts.append(f"【性】 {gender}")
        
    inner_html  = "<br><br>".join(display_parts) # パーツ間の間隔を調整
    content_html = f"<div style='text-align: left;'>{inner_html}</div>"

card_content_html = f"<div class='custom-card'>{content_html}</div>"
st.markdown(card_content_html, unsafe_allow_html=True)


# --- フィードバックボタン ---
feedback_options = {
    "覚えた！🟢": {"label": "覚えた！🟢", "message": "かんぺきみたいだね！"},
    "うる覚え🟡": {"label": "うる覚え🟡", "message": "もう一度！あと少し！"},
    "覚えていない！🔴": {"label": "覚えていない！🔴", "message": "頑張ろう！少し練習が必要だね。"}
}

cols = st.columns(len(feedback_options))
button_pressed_this_run = None

for i, (key, option) in enumerate(feedback_options.items()):
    disabled = (
        st.session_state.active_feedback is not None
        and st.session_state.active_feedback != key
    )
    if cols[i].button(option["label"], key=f"fb_{key}", disabled=disabled):
        button_pressed_this_run = key

if button_pressed_this_run is not None:
    if st.session_state.active_feedback is None: # ボタンが押されたのが最初のフィードバックの場合のみ処理
        st.session_state.active_feedback = button_pressed_this_run
        st.session_state.feedback_message = feedback_options[button_pressed_this_run]["message"]
        st.session_state.review_count += 1 # このカウントが適切かは要検討

        next1, next2, next3 = compute_next_times(button_pressed_this_run)
        
        payload = {
            "user_id": "user1", # 固定値または動的に設定
            "card_id": int(st.session_state.card_id),
            "feedback": str(button_pressed_this_run),
            "feedback_time": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
            "review_count": int(st.session_state.review_count),
            "next_review_time_1": next1.isoformat(),
            "next_review_time_2": next2.isoformat(),
            "next_review_time_3": next3.isoformat(),
            "next_review1": True,
            "next_review2": True,
            "next_review3": True
        }
        
        # record_feedback関数は存在しないため、API呼び出し関数を使用
        response_data = record_feedback_api_call(payload) 
        
        if "error" not in response_data: # API呼び出しが成功した場合
            st.success("フィードバックを記録しました！")
        # エラーの場合はrecord_feedback_api_call内でst.errorが表示される
            
    # フィードバックボタンが押されたら、現在のカードの裏面を表示したままにするか、次のカードに進むか
    # 現在のコードでは、フィードバック後に次のカードの表を表示するようになっている
    if not candidate_df.empty:
        st.session_state.index = (st.session_state.index + 1) % len(candidate_df)
    else:
        st.session_state.index = 0
        
    st.session_state.active_feedback = None # 次のカードのためにリセット
    st.session_state.feedback_message = ""  # 次のカードのためにリセット
    st.session_state.flip = True # 次のカードは表から
    st.rerun()

# --- フィードバック履歴 ---
for _ in range(2):
    st.write("") # UI上のスペース

# df_lexique は df (全カードデータ) を使用できる
# df_fb_hist は df_fb (スクリプト冒頭でロード) を使用できる
with st.expander("▶️ 最新フィードバック履歴を表示"):
    try:
        if not df_fb.empty: # df_fbが空でないことを確認
            # df(全カードデータ)に必要な列があるか確認
            if not df.empty and "id" in df.columns and "ortho" in df.columns and "card_id" in df_fb.columns:
                merged_df = pd.merge(
                    df_fb, # feedback.csv のデータ
                    df[["id", "ortho"]], # 全カードデータから id と ortho を選択
                    left_on="card_id",
                    right_on="id",
                    how="left",
                )
                # 'id' 列が重複して作られる場合があるので、df_all_cards由来の'id'を削除 (通常は'id_x', 'id_y'になるのを避けるため)
                # しかし、もしdf_fbに元々'id'列がないなら、このdropは不要か、エラーになる可能性
                # merged_df = merged_df.drop(columns=["id_x", "id_y"]) # これは状況による
                # より安全なのは、マージ後の列名を確認して適切に処理すること
                # ここでは、もし'id_right'のような列ができたらそれを削除する、または必要な列だけを選択する
                if 'id_y' in merged_df.columns: # pandas version >= 1. suffixes default to _x, _y
                    merged_df = merged_df.drop(columns=['id_y'])
                if 'id_x' in merged_df.columns: # if only one 'id' was present in one df
                     merged_df = merged_df.rename(columns={'id_x': 'original_id_from_df_fb_if_present'})


                cols = merged_df.columns.tolist()
                if "ortho" in cols: # ortho列が存在すれば先頭に
                    cols = ["ortho"] + [col for col in cols if col != "ortho"]
                    st.dataframe(merged_df[cols].tail(10))
                else: # ortho列がマージでできなかった場合
                    st.dataframe(df_fb.tail(10))
            else: # マージに必要な列が足りない場合
                st.warning("フィードバック履歴または語彙データに必要な列が存在しません。")
                st.dataframe(df_fb.tail(10)) 
        else:
            st.info("フィードバック履歴はまだありません。")
    except Exception as e:
        st.error(f"フィードバック CSV の読み込みまたは表示に失敗しました: {e}")
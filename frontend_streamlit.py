# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
import re
import math
from datetime import datetime, timedelta 
from zoneinfo import ZoneInfo
import os
# --- セッション状態の初期化 ---
if 'index' not in st.session_state:
    st.session_state.index = 0
    st.session_state.flip = True
    st.session_state.active_feedback = None
    st.session_state.feedback_message = ""
    st.session_state.review_count = 0
    st.session_state.next_review_time_1 = None
    st.session_state.next_review_time_2 = None
    st.session_state.next_review_time_3 = None



# ── Ebbinghaus モデルの定数定義 ──

RECALL_THRESHOLD = 0.8     # 忘却曲線の閾値（80%保持率で再レビュー）
DEFAULT_STABILITY = 2.0    # 初期安定度 S（日）
STABILITY_FACTORS = {
    "覚えた！🟢":    1.3,   # 完全正答なら安定度を 1.3 倍
    "うる覚え🟡":    1.0,   # やや曖昧ならそのまま
    "覚えていない！🔴": 0.7  # 不正解なら安定度を 0.7 倍
}

def compute_next_times(feedback_key: str,
                       last_review: datetime = None,
                       initial_stability: float = None):
    """
    Ebbinghaus の忘却曲線 R(t)=e^{-t/S} から次回レビュー３回分を計算。
    - feedback_key         : ボタンラベル（絵文字付き）
    - last_review          : 前回レビュー日時（None なら今＝JST）
    - initial_stability    : カード固有の安定度 S（None なら DEFAULT_STABILITY）
    """
    # 「今」を JST で取得
    now = datetime.now(ZoneInfo("Asia/Tokyo")) if last_review is None else last_review
    # S を決定
    S = initial_stability if initial_stability is not None else DEFAULT_STABILITY

    times = []
    for _ in range(3):
        # 次回レビューまでの日数 t_days
        t_days = -S * math.log(RECALL_THRESHOLD)
        next_time = now + timedelta(days=t_days)
        times.append(next_time)

        # 次ループ用に now=S の更新
        now = next_time
        # フィードバックに応じて S を伸縮
        factor = STABILITY_FACTORS.get(feedback_key, STABILITY_FACTORS["うる覚え🟡"])
        S *= factor

    return times

#---------------------
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
</style>
""", unsafe_allow_html=True)



# st.title('フランス語フラッシュカード学習')
st.markdown("""
<h1 style="font-size:1.7rem; font-weight:bold; margin-bottom:0.5rem;">
  フランス語フラッシュカード学習
</h1>
""", unsafe_allow_html=True)


# スタイルとカスタムフォントの定義
st.markdown("""
<style>
 .custom-font {
     font-size: 15px;
 }
 .custom-card {
     position: relative;
     height: 50vh; /* カードの高さ */
     width: 60vw;  /* カードの幅 */
     background-color: rgba(255, 250, 205, 0.8);
     display: flex;             /* ★ Flexbox を再度有効化: 中身を中央揃えにするため */
     justify-content: center;   /* ★ Flexbox: 水平方向中央 */
     align-items: center;       /* ★ Flexbox: 垂直方向中央 */
     margin: auto;
     border-radius: 10px;
     padding: 20px;
     /* text-align は内側のdivで制御するのでここでは不要 */
     font-size: 24px;
     color: black;
     font-family: 'Arial', sans-serif;
     font-weight: bold;
     letter-spacing: 2px;
     overflow: auto; /* 内容が多い場合にスクロール */
 }
  .level-text {
        color: #808080; /* レベル表示の色 */
 }
 /* Flipボタンのスタイル */
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

# --- データロード ---
@st.cache_data
def load_data():
    # CSVファイル名が "_修正済み.csv" になっていますが、これが正しいか確認してください
    return pd.read_csv('data/mettre_fin_Lexique_translated_v6w_修正済み.csv').sample(frac=1).reset_index(drop=True)

df = load_data()

# --- ヘルパー関数 ---
def get_card(index):
    return df.iloc[index]

# 翻訳関数 (ポート8000のAPIを呼び出す)
def translate_word(ortho, lemme):
    url = "http://127.0.0.1:8000/translate/" # ★ポート8000に変更
    try:
        # ポート8000のAPIは 'word' (ortho) のみ受け取る想定 (API側の実装による)
        payload_data = {'word': ortho}
        print(f"Streamlit: Sending to {url}: {payload_data}")
        response = requests.post(url, json=payload_data)
        response.raise_for_status()
        data = response.json()
        # API側で整形されたカンマ区切りの翻訳が返ってくることを期待
        translation = data.get('translation', '翻訳APIエラー')
        print(f"Streamlit: Received translation from API: {translation}")
        return translation
    except requests.RequestException as e:
        print(f"Streamlit: Translation API request failed: {e}")
        return f"翻訳APIリクエスト失敗: {e}"
    except Exception as e:
        print(f"Streamlit: Unexpected error in translate_word: {e}")
        return "翻訳中に予期せぬエラー"

# レベルチェッカーAPI呼び出し (ポート8014)
def get_level(ortho, card_id):
    url = "http://127.0.0.1:8014/predict/"
    try:
        card_id_int = int(card_id)
        response = requests.post(url, json={'lemme': ortho, 'card_id': card_id_int})
        response.raise_for_status()
        level_text = response.json().get('level', "未定義") # デフォルト値を変更
        return level_text
    except requests.RequestException as e:
        return f"レベルAPIエラー: {e}"

# ----フィードバック記録API呼び出し (ユーザーからのレポンスをポート8014へ投げる→level_checkè_copy.py)

def record_feedback(
    user_id: str,
    card_id: int,
    feedback: str,
    feedback_time: str,
    review_count: int,
    next_review_time_1: str,
    next_review_time_2: str,
    next_review_time_3: str,
    next_review1: bool,
    next_review2: bool,
    next_review3: bool,
):
    url = "http://127.0.0.1:8014/feedback/"
    payload = {
        "user_id": user_id,
        "card_id": card_id,
        "feedback": feedback,
        "feedback_time": feedback_time,
        "review_count": review_count,
        "next_review_time_1": next_review_time_1,
        "next_review_time_2": next_review_time_2,
        "next_review_time_3": next_review_time_3,
        "next_review1": next_review1,
        "next_review2": next_review2,
        "next_review3": next_review3,
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"フィードバック記録失敗: {e}")
        return {"error": str(e)}

# --- セッション状態の初期化 ---
if 'index' not in st.session_state:
    st.session_state.index = 0
if 'flip' not in st.session_state: # True=表, False=裏
    st.session_state.flip = True
if 'active_feedback' not in st.session_state: # 押されたフィードバック (None, '覚えた！🟢', 'うる覚え🟡', '覚えていない！🔴')
    st.session_state.active_feedback = None
if 'feedback_message' not in st.session_state:
    st.session_state.feedback_message = ""
# ------------------------------

# --- Flipボタンの処理 ---
if st.button("Flip", key="main_flip_button"):
    if st.session_state.active_feedback is not None:  # フィードバックが既に行われていたら
        st.session_state.index = (st.session_state.index + 1) % len(df) # 次のカードへ
        st.session_state.active_feedback = None  # 新しいカードなのでフィードバック状態をリセット
        st.session_state.feedback_message = ""   # フィードバックメッセージもリセット
        st.session_state.flip = True             # 新しいカードは必ず表から
    else: # フィードバック前なら、現在のカードを表裏反転
        st.session_state.flip = not st.session_state.flip
    st.rerun() # UIを即時更新
# ---------------------

# --- 現在のカードデータを取得 ---
card = get_card(st.session_state.index)
st.session_state.card_id = card['id'] # record_feedbackで使うためにセット
# ---------------------------

# --- カード表示内容の生成 ---
if st.session_state.flip:
    # --- カード表面 ---
    word_surface  = card['ortho']
    lemma_surface = card.get('lemme', '')
    phon_surface  = card.get('phon', '') # CSVに 'phon' 列があるか確認
    level_surface = get_level(card['ortho'], st.session_state.card_id)

    # 表面は中央揃えのdivで囲む
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
    # --- カード裏面 ---
    # translate_word はポート8000を呼び出し、整形済みのカンマ区切り文字列を期待
    translation = translate_word(card['ortho'], card.get('lemme', card['ortho']))

    # 各文法情報を取得
    pos = str(card.get('cgram_jp', '')).strip()
    inflection = str(card.get('infover_translated', '')).strip()
    gender = str(card.get('genre_jp', '')).strip()

    display_parts = []
    if translation:
         # カンマ区切りの翻訳を <br> 区切りに変換して表示（各訳が縦に並ぶ）
         translations_list = [t.strip() for t in translation.split(',')]
         formatted_translations = "<br>".join([f"<b>{t}</b>" for t in translations_list])
         display_parts.append(formatted_translations)

    if pos:
        display_parts.append(f"【品詞】 {pos}")
    if inflection and inflection.lower() != 'nan':
        display_parts.append(f"【活用など】 {inflection}")
    if gender and gender.lower() != 'nan' and gender.lower() != 'nun':
        display_parts.append(f"【性】 {gender}")

    # HTMLの改行タグ <br> で結合 (翻訳と文法情報の間にも改行が入る)
    inner_html  = "<br>".join(display_parts)
    # 裏面は左寄せのdivで囲む
    content_html = f"<div style='text-align: left;'>{inner_html}</div>"


# --- カード表示内容ここまで ---

# --- 最終的なカード表示 ---
card_content_html = f"<div class='custom-card'>{content_html}</div>"
st.markdown(card_content_html, unsafe_allow_html=True)
# ------------------------

# --- フィードバックボタンとメッセージ表示 ---
feedback_options = {
    "覚えた！🟢": {"label": "覚えた！🟢",    "message": "かんぺきみたいだね！"},
    "うる覚え🟡": {"label": "うる覚え🟡",  "message": "もう一度！あと少し！"},
    "覚えていない！🔴":  {"label": "覚えていない！🔴", "message": "頑張ろう！少し練習が必要だね。"}
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

# ─── 押されたときだけ実行 ─────────────────────
if button_pressed_this_run is not None:
    # 初回フィードバックのときだけ
    if st.session_state.active_feedback is None:
        st.session_state.active_feedback = button_pressed_this_run
        st.session_state.feedback_message = feedback_options[button_pressed_this_run]["message"]

        # review_count 初期化済み前提
        st.session_state.review_count += 1

        #↓次回レビュー時刻を計算（「フィードバックを受け取ったので、Ebbinghaus に従って次回３回分のタイミングを計算しますよ」という
           #呼び出しの部分。削除すると、次回レビュー時#刻がまったく生成されなくなってしまう
        next1, next2, next3 = compute_next_times(button_pressed_this_run)

        # Payload 組み立て（必ず文字列／真偽値になるようキャスト）
        payload = {
            "user_id":      "user1",
            "card_id":      int(st.session_state.card_id),
            "feedback":     str(button_pressed_this_run),
            "feedback_time": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
            "review_count": int(st.session_state.review_count),
            "next_review_time_1": next1.isoformat(),
            "next_review_time_2": next2.isoformat(),
            "next_review_time_3": next3.isoformat(),
            "next_review1": True,
            "next_review2": True,
            "next_review3": True
        }

        #st.write("DEBUG payload:", payload)

        # バックエンドに送信
        response = requests.post("http://127.0.0.1:8014/feedback/", json=payload)
        try:
            response.raise_for_status()
            st.success("フィードバックを記録しました！")
        except requests.HTTPError:
            st.error(f"フィードバック記録失敗: {response.status_code} {response.text}")

    # ボタン後は裏面へ
    st.session_state.flip = False
    st.rerun()


# --- 画面に最新フィードバックを表示するセクション ---
for _ in range(2):
    st.write("")

BASE_DIR = os.path.dirname(__file__)
csv_path_lexique = 'data/mettre_fin_Lexique_translated_v6w_修正済み.csv'
try:
    df_lexique = pd.read_csv(csv_path_lexique, dtype={"level": int})
except Exception as e:
    st.error(f"語彙 CSV の読み込みに失敗しました: {e}")
    df_lexique = pd.DataFrame()

with st.expander("▶️ 最新フィードバック履歴を表示"):
    try:
        df_fb = pd.read_csv("data/feedback.csv")
        if (
            not df_lexique.empty
            and "card_id" in df_fb.columns
            and "id" in df_lexique.columns
            and "ortho" in df_lexique.columns
        ):
            # feedback.csv の card_id と 語彙CSV の id をキーとして結合
            merged_df = pd.merge(
                df_fb,
                df_lexique[["id", "ortho"]],
                left_on="card_id",
                right_on="id",
                how="left",
            )
            # 不要になった 'id' 列を削除
            merged_df = merged_df.drop(columns=["id"])
            # 新しい 'ortho' 列を先頭に移動
            cols = merged_df.columns.tolist()
            cols = ["ortho"] + [col for col in cols if col != "ortho"]
            merged_df = merged_df[cols]

            st.dataframe(merged_df.tail(10))
        else:
            st.warning("フィードバック履歴または語彙データに必要な列が存在しません。")
            st.dataframe(df_fb.tail(10))  # ortho を表示できない場合は、元のフィードバック履歴のみ表示
    except Exception as e:
        st.error(f"フィードバック CSV の読み込みに失敗しました: {e}")




# --- フィードバックここまで ---

# 以前の main() 関数や if __name__ == "__main__": は不要になります
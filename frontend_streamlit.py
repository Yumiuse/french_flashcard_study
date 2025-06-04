# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os, sys

# フォルダ移動時にモジュールの参照を正しくするため
sys.path.insert(0, os.path.dirname(__file__))

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
    """
    now = datetime.now(ZoneInfo("Asia/Tokyo")) if last_review is None else last_review
    S = initial_stability if initial_stability is not None else DEFAULT_STABILITY

    times = []
    for _ in range(3):
        t_days = -S * math.log(RECALL_THRESHOLD)
        next_time = now + timedelta(days=t_days)
        times.append(next_time)
        now = next_time
        factor = STABILITY_FACTORS.get(feedback_key, STABILITY_FACTORS["うる覚え🟡"])
        S *= factor

    return times

# カードデータ（シャッフル済み）をロード
@st.cache_data
def load_data():
    return pd.read_csv('data/mettre_fin_Lexique_translated_v6w_修正済み.csv') \
             .sample(frac=1).reset_index(drop=True)

df = load_data()

# フィードバック履歴をロードし、日時列を datetime 型に変換
@st.cache_data
def load_feedback():
    try:
        fb = pd.read_csv('data/feedback.csv', parse_dates=[
            "next_review_time_1",
            "next_review_time_2",
            "next_review_time_3"
        ])
        return fb
    except FileNotFoundError:
        # feedback.csv が存在しない場合は空の DataFrame を返す
        cols = [
            "user_id", "card_id", "feedback", "feedback_time", "review_count",
            "next_review_time_1", "next_review_time_2", "next_review_time_3",
            "next_review1", "next_review2", "next_review3", "recorded_at"
        ]
        return pd.DataFrame(columns=cols)

# 期限が到来しているカード ID の集合を返す
def get_due_card_ids():
    fb = load_feedback()
    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    due_ids = set()
    for _, row in fb.iterrows():
        for n in (1, 2, 3):
            col_time = f"next_review_time_{n}"
            col_flag = f"next_review{n}"
            if pd.notnull(row.get(col_time)) and row[col_time] <= now and row.get(col_flag, 0) == 1:
                due_ids.add(row["card_id"])
                break
    return due_ids

# 新規カード（未レビュー）のカード ID の集合を返す
def get_new_card_ids():
    fb = load_feedback()
    reviewed = set(fb["card_id"].tolist())
    all_ids = set(df["id"].tolist())
    return all_ids - reviewed

# カードを選択する関数（期限カード > 新規カード > シャッフル順）
def select_card(index: int):
    due_ids = get_due_card_ids()
    new_ids = get_new_card_ids()

    if due_ids:
        df_due = df[df["id"].isin(due_ids)].reset_index(drop=True)
        return df_due.iloc[index % len(df_due)]
    elif new_ids:
        df_new = df[df["id"].isin(new_ids)].reset_index(drop=True)
        return df_new.iloc[index % len(df_new)]
    else:
        # すべてレビュー済みかつ期限カードがない場合は、シャッフル済み df から順番に回す
        return df.iloc[index % len(df)]

# Streamlit 用 CSS
st.markdown("""
<style>
h1 {
  margin-top: 0.4rem !important;
  margin-bottom: 0.5rem !important;
}
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

# ヘッダー
st.markdown("""
<h1 style="font-size:1.7rem; font-weight:bold; margin-bottom:0.5rem;">
  フランス語フラッシュカード学習
</h1>
""", unsafe_allow_html=True)

# --- カードの取得 ---
card = select_card(st.session_state.index)
st.session_state.card_id = card["id"]

# --- カード表面・裏面の表示 ---
if st.session_state.flip:
    # 表面：単語・読み・レベル
    word_surface  = card["ortho"]
    lemma_surface = card.get("lemme", "")
    phon_surface  = card.get("phon", "")
    # レベル判定API を呼び出す（ポート 8014）
    try:
        resp = requests.post(
            "http://127.0.0.1:8014/predict/",
            json={"lemme": word_surface, "card_id": int(st.session_state.card_id)}
        )
        resp.raise_for_status()
        level_surface = resp.json().get("level", "未定義")
    except requests.RequestException as e:
        level_surface = f"レベルAPIエラー: {e}"

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
    # 裏面：翻訳・文法情報
    try:
        resp = requests.post(
            "http://127.0.0.1:8000/translate/",
            json={"word": card["ortho"]}
        )
        resp.raise_for_status()
        translation = resp.json().get("translation", "翻訳APIエラー")
    except requests.RequestException as e:
        translation = f"翻訳APIリクエスト失敗: {e}"

    pos = str(card.get("cgram_jp", "")).strip()
    inflection = str(card.get("infover_full_translation", "")).strip()
    gender = str(card.get("genre_jp", "")).strip()

    display_parts = []
    if translation:
        parts = [t.strip() for t in translation.split(",")]
        formatted = "<br>".join([f"<b>{t}</b>" for t in parts])
        display_parts.append(formatted)

    if pos:
        display_parts.append(f"【品詞】 {pos}")
    if inflection and inflection.lower() != "nan":
        display_parts.append(f"【活用など】 {inflection}")
    if gender and gender.lower() not in ("nan", "nun"):
        display_parts.append(f"【性】 {gender}")

    inner_html = "<br>".join(display_parts)
    content_html = f"<div style='text-align: left;'>{inner_html}</div>"

# カード全体を表示
st.markdown(f"<div class='custom-card'>{content_html}</div>", unsafe_allow_html=True)

# --- Flipボタンの処理 ---
feedback_options = {
    "覚えた！🟢":    {"label": "覚えた！🟢",    "message": "かんぺきみたいだね！"},
    "うる覚え🟡":    {"label": "うる覚え🟡",  "message": "もう一度！あと少し！"},
    "覚えていない！🔴": {"label": "覚えていない！🔴", "message": "頑張ろう！少し練習が必要だね。"}
}

cols = st.columns(len(feedback_options))
button_pressed = None

for i, (key, opt) in enumerate(feedback_options.items()):
    disabled = (
        st.session_state.active_feedback is not None
        and st.session_state.active_feedback != key
    )
    if cols[i].button(opt["label"], key=f"fb_{key}", disabled=disabled):
        button_pressed = key

if button_pressed is not None:
    if st.session_state.active_feedback is None:
        st.session_state.active_feedback = button_pressed
        st.session_state.feedback_message = feedback_options[button_pressed]["message"]
        st.session_state.review_count += 1

        next1, next2, next3 = compute_next_times(button_pressed)
        payload = {
            "user_id":      "user1",
            "card_id":      int(st.session_state.card_id),
            "feedback":     str(button_pressed),
            "feedback_time": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
            "review_count": int(st.session_state.review_count),
            "next_review_time_1": next1.isoformat(),
            "next_review_time_2": next2.isoformat(),
            "next_review_time_3": next3.isoformat(),
            "next_review1": True,
            "next_review2": True,
            "next_review3": True
        }
        try:
            resp = requests.post("http://127.0.0.1:8014/feedback/", json=payload)
            resp.raise_for_status()
            st.success("フィードバックを記録しました！")
        except requests.HTTPError:
            st.error(f"フィードバック記録失敗: {resp.status_code} {resp.text}")

    st.session_state.flip = False
    st.rerun()

# --- 最新フィードバック履歴を表示 ---
st.write("\n")
st.write("\n")

try:
    df_lexique = pd.read_csv('data/mettre_fin_Lexique_translated_v6w_修正済み.csv', dtype={"level": int})
except Exception as e:
    st.error(f"語彙 CSV の読み込みに失敗しました: {e}")
    df_lexique = pd.DataFrame()

with st.expander("▶️ 最新フィードバック履歴を表示"):
    try:
        df_fb = load_feedback()
        if (
            not df_lexique.empty
            and "card_id" in df_fb.columns
            and "id" in df_lexique.columns
            and "ortho" in df_lexique.columns
        ):
            merged = pd.merge(
                df_fb,
                df_lexique[["id", "ortho"]],
                left_on="card_id",
                right_on="id",
                how="left"
            )
            merged = merged.drop(columns=["id"])
            cols = merged.columns.tolist()
            cols = ["ortho"] + [c for c in cols if c != "ortho"]
            merged = merged[cols]
            st.dataframe(merged.tail(10))
        else:
            st.warning("フィードバック履歴または語彙データに必要な列が存在しません。")
            st.dataframe(df_fb.tail(10))
    except Exception as e:
        st.error(f"フィードバック CSV の読み込みに失敗しました: {e}")

import pandas as pd
import re

# ===================== 1. SAMPA→IPA 変換辞書 =====================
replace_dict = {
    # Vowels
    'E': 'ɛ', 'e': 'e', '@': 'ə', 'a': 'a', 'o': 'o', 'O': 'ɔ',
    'i': 'i', 'u': 'u', 'y': 'y', '2': 'ø', '9': 'œ',
    # Nasal vowels
    '1': 'ɑ̃', '5': 'ɛ̃', '4': 'ɔ̃', '6': 'œ̃',
    # Semi-vowels
    'j': 'j', 'w': 'w', 'H': 'ɥ', '8': 'ɥ',
    # Consonants
    'p': 'p', 't': 't', 'k': 'k', 'b': 'b', 'd': 'd', 'g': 'g',
    'f': 'f', 's': 's', 'S': 'ʃ', 'v': 'v', 'z': 'z', 'Z': 'ʒ',
    'm': 'm', 'n': 'n', 'J': 'ɲ', 'l': 'l', 'R': 'ʁ',
    # Others
    '°': 'ə', '§': 'ɔ̃',
}

# ===================== 2. 綴りルールによる o/ɔ 判別 =====================
def should_o_be_open(ortho, phon):
    ortho = ortho.lower()
    if "ô" in ortho or "eau" in ortho or "au" in ortho:
        return False  # 例: hôtel, beau, auto
    if ortho.endswith("ot") or ortho.endswith("os") or ortho.endswith("eau"):
        return False
    if ortho.endswith("o") and len(ortho) > 2:
        return False
    if ortho.endswith("ose"):
        return False
    for c in ["rt", "r", "l", "m", "n", "gn", "ch", "st", "sp", "ct"]:
        if ortho.endswith("o"+c):
            return True
    if len(ortho) >= 3 and ortho[-2] == "o" and ortho[-1] not in "aeiouy":
        return True
    if phon and (isinstance(phon, str) and (phon.endswith("t") or phon.endswith("r") or phon.endswith("l") or phon.endswith("m") or phon.endswith("n"))):
        return True
    return False

# ===================== 3. 変換メイン関数 =====================
def convert_lexique_to_ipa(phon, ortho=None):
    if pd.isnull(phon):
        return phon
    phon = str(phon).strip()
    # ---- 綴りでo→ɔ自動変換 ----
    if ortho and isinstance(ortho, str) and "o" in ortho:
        if should_o_be_open(ortho, phon):
            phon = phon.replace("o", "ɔ")
    # ---- 複数文字の特殊ルール ----
    phon = re.sub(r'^@t$', 'ɑ̃t', phon)
    phon = re.sub(r'tS', 'tʃ', phon)
    phon = re.sub(r'ə$', 'ɑ̃', phon)
    phon = re.sub(r'mə$', 'mɑ̃', phon)
    phon = re.sub(r'əmɑ̃$', 'mɑ̃', phon)
    phon = re.sub(r'ə(s)?$', 'ɑ̃', phon)
    # ---- 通常の辞書置換 ----
    for sam_char, ipa_char in replace_dict.items():
        phon = phon.replace(sam_char, ipa_char)
    return phon

# ===================== 4. ファイル入出力 =====================
input_csv = "/Volumes/SP PC60/french_flashcard_study/data/mettre_fin_Lexique_translated_v6w_修正済み.csv"
output_csv = "/Volumes/SP PC60/french_flashcard_study/data/mettre_fin_Lexique_translated_v6w_修正済み.csv"

try:
    df = pd.read_csv(input_csv)
    # まずNaNやstrでないortho列を事前にチェック
    print("★ 列名一覧:", df.columns.tolist())
    print("★ 1行目:", df.iloc[0].tolist())
    # ortho列でstr型でないものを抽出して表示
    non_str_rows = df[~df["ortho"].apply(lambda x: isinstance(x, str))]
    if len(non_str_rows) > 0:
        print("【ortho列がstr型でない行】")
        print(non_str_rows[["ortho", "phon"]])
        print(f"↑該当件数: {len(non_str_rows)}")
    else:
        print("ortho列は全てstr型です！")
    # NaN行は削除
    df = df[~df["ortho"].isnull()]

    # "phon"列・"ortho"列の2つを渡して変換！（ポイント！）
    df["phon"] = df.apply(lambda row: convert_lexique_to_ipa(row["phon"], row["ortho"]), axis=1)


    # csv文法事項の修正追加
    df["infover_full"] = df["infover_full"].str.replace(
    r"Indicatif:Passé:", 
    "Indicatif:Passé simple:", 
    regex=True
    )
    df["infover_full_translation"] = df["infover_full_translation"].str.replace(
    r"直説法:過去:", 
    "直説法:単純過去:", 
    regex=True
    )

    df["infover_translated"] = df["infover_translated"].str.replace(
    r"直説法:過去:", 
    "直説法:単純過去:", 
    regex=True
    )

    df.to_csv(output_csv, index=False)
    print(f"IPA変換完了！新しいファイル: {output_csv}")

except FileNotFoundError:
    print(f"エラー: 入力ファイルが見つかりません: {input_csv}")
except Exception as e:
    print(f"予期せぬエラーが発生しました: {e}")



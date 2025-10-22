import streamlit as st
import pandas as pd

# --- 기본 설정 ---
st.set_page_config(page_title="상담 일정 조회", page_icon="📅")
st.title("📚 학생 상담 일정 조회")
st.caption("학생 이름과 번호 4자리를 모두 입력하면 상담 일시를 확인할 수 있습니다.")

# --- Google Sheets URL (Secrets에서 불러오기) ---
SHEET_URL = st.secrets.get("SHEET_URL", "")

if not SHEET_URL:
    st.warning("⚠️ 구글 시트 링크 등록하세요. ")
    st.stop()

@st.cache_data(ttl=300)
def load_csv(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    if df.columns[0].strip().lower() != "time":
        df = df.rename(columns={df.columns[0]: "time"})
    df.columns = [str(c).strip() for c in df.columns]
    # '점심' 행 제거
    df = df[~df["time"].astype(str).str.contains("점심")]
    return df.reset_index(drop=True)

try:
    df = load_csv(SHEET_URL)
except Exception as e:
    st.error(f"❌ 데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# --- 사용자 입력 ---
col1, col2 = st.columns(2)
with col1:
    name_input = st.text_input("👤 학생 이름", placeholder="예: 김하나(알파벳 제외)").strip()
with col2:
    num_input = st.text_input("🔢 휴대폰 번호 (뒤 4자리)", placeholder="예: 1234").strip()

def find_match(df: pd.DataFrame, name: str, num: str):
    """이름과 번호가 모두 일치하는 셀을 찾음."""
    if not name or not num:
        return []

    hits = []
    target = f"{name} {num}".strip()
    date_cols = df.columns[1:]

    for date_col in date_cols:
        col_series = df[date_col].astype(str).fillna("").str.strip()

        for idx, cell in col_series.items():
            cell_str = str(cell).strip()

            if not cell_str or cell_str.lower() in ["nan", "none"]:
                continue

            # 여러 명이 있을 수 있으므로 쉼표나 슬래시로 분리
            tokens = [t.strip() for t in
                      pd.Series(cell_str.replace("／", "/").replace("，", ","))
                      .astype(str)
                      .str.split(r"[,/]").explode().tolist()]

            # 정확히 "이름 번호" 가 일치하는 항목 찾기
            if target in tokens:
                hits.append((str(date_col).strip(), str(df.loc[idx, "time"]).strip(), target))
    return hits

if name_input and num_input:
    matches = find_match(df, name_input, num_input)

    if matches:
        st.success(f"✅ {name_input} ({num_input}) 학생의 상담 일정 입니다.")
        for (date, time_, who) in matches:
            st.markdown(
                f"""
                ---
                👤 **학생:** {name_input}  
                🗓 **상담 일시:** {date} {time_}  
                📍 **상담 장소:** 컴퓨터실2  
                ☎️ *시간 및 장소는 변동될 수 있으니 당일 전화 꼭! 확인하세요.*
                """
            )
    else:
        st.info("🔍 입력한 이름과 번호가 정확히 일치하는 일정이 없습니다.")
elif name_input or num_input:
    st.warning("⚠️ 이름과 번호를 모두 입력해야 검색할 수 있습니다.")

import streamlit as st
import pandas as pd

# --- 기본 설정 ---
st.set_page_config(page_title="상담 일정 조회", page_icon="📅")
st.title("📚 학생 및 학부모 상담 일정 조회")
st.caption("이름과 휴대폰 번호 뒤 4자리를 입력하면 상담 일시를 확인할 수 있습니다.")

# --- Google Sheets URL ---
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
    name_input = st.text_input("👤 이름 (학생 또는 학부모)", placeholder="예: 김하나").strip()
with col2:
    num_input = st.text_input("🔢 휴대폰 번호 (뒤 4자리)", placeholder="예: 1234").strip()


def find_match(df: pd.DataFrame, name: str, num: str):
    """이름과 번호가 일치하는 셀(학생 또는 학부모)을 찾음."""
    if not name or not num:
        return []

    hits = []
    # 두 가지 형태 (학생, 학부모) 모두 찾기
    targets = [f"{name} {num}", f"#{name} {num}"]
    date_cols = df.columns[1:]

    for date_col in date_cols:
        col_series = df[date_col].astype(str).fillna("").str.strip()

        for idx, cell in col_series.items():
            cell_str = str(cell).strip()
            if not cell_str or cell_str.lower() in ["nan", "none"]:
                continue

            tokens = [t.strip() for t in
                      pd.Series(cell_str.replace("／", "/").replace("，", ","))
                      .astype(str)
                      .str.split(r"[,/]").explode().tolist()]

            for token in tokens:
                clean_token = token.replace("*", "").strip()

                for target in targets:
                    if clean_token == target:
                        has_star = "*" in token
                        is_parent = target.startswith("#")
                        hits.append((
                            str(date_col).strip(),
                            str(df.loc[idx, "time"]).strip(),
                            target,
                            has_star,
                            is_parent
                        ))
    return hits


# --- 결과 표시 ---
if name_input and num_input:
    matches = find_match(df, name_input, num_input)

    if matches:
        st.success(f"✅ {name_input} ({num_input})님의 상담 일정입니다.")
        for (date, time_, who, has_star, is_parent) in matches:
            location = "전화 상담" if has_star else "컴퓨터실2"
            role = "학부모" if is_parent else "학생"
            st.markdown(
                f"""
                ---
                👤 **구분:** {role}  
                🗓 **상담 일시:** {date} {time_}  
                📍 **상담 장소:** {location}  
                ☎️ *시간 및 장소는 변동될 수 있으니 당일 전화 꼭! 확인하세요.*
                """
            )
    else:
        st.info("🔍 입력한 이름과 번호가 정확히 일치하는 일정이 없습니다.")
elif name_input or num_input:
    st.warning("⚠️ 이름과 번호를 모두 입력해야 검색할 수 있습니다.")

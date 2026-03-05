import streamlit as st
import pandas as pd
import requests
from io import BytesIO

st.set_page_config(page_title="白沙屯媽進香資料記錄", layout="wide")

#放置圖片(浮水效果)
import base64
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()
img_base64 = get_base64_image("mazu_logo.png")
st.markdown(
    f"""
    <style>

    /* 🔥 暗紅漸層背景 */
    .stApp {{
        background: linear-gradient(
            135deg,
            #2b0000 0%,
            #4b0000 40%,
            #1a0000 100%
        );
        color: #ffffff;
    }}

    /* 🔥 浮水印 */
    .watermark {{
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        opacity: 0.08;
        z-index: 0;
        pointer-events: none;
        filter: drop-shadow(0 0 60px gold);
    }}

    /* 讓內容浮在上層 */
    section[data-testid="stMain"] {{
        position: relative;
        z-index: 1;
    }}

    </style>

    <img src="data:image/png;base64,{img_base64}" class="watermark" width="700">
    """,
    unsafe_allow_html=True
)

st.title("🔥白沙屯媽進香資料記錄🔥                            βŁãÇķ™ 製")

file_url = "https://raw.githubusercontent.com/suptuchstop/mazu--cloud/main/BaishatunMAZU_Data.xlsx"

# ==============================
# 快取讀取 + 統計優化
# ==============================

@st.cache_data
def load_data():

    response = requests.get(file_url)
    response.raise_for_status()

    excel_data = BytesIO(response.content)
    xls = pd.ExcelFile(excel_data, engine="openpyxl")

    all_data = {}
    summary = []

    # 🔥 時間計算函式（優化版）
    def calculate_hours(time_list):
        total = 0
        for i in range(1, len(time_list)):
            diff = (time_list[i] - time_list[i - 1]).total_seconds()
            if 0 < diff <= 86400:
                total += diff / 3600
        return total

    for sheet in xls.sheet_names:

        df = pd.read_excel(xls, sheet_name=sheet)
        df.columns = df.columns.str.strip()

        df['去回程'] = (
            df['去回程']
            .astype(str)
            .str.strip()
            .replace({'去程': '去', '回程': '回'})
        )

        df['完整時間'] = pd.to_datetime(
            df['月'].astype(str) + '-' +
            df['日'].astype(str) + ' ' +
            df['時間'].astype(str),
            format='%m-%d %H:%M',
            errors='coerce'
        )

        df = df.sort_values('完整時間')

        all_data[sheet] = df

        # ===== 時間統計 =====
        go_df = df[df['去回程'] == '去'].dropna(subset=['完整時間'])
        back_df = df[df['去回程'] == '回'].dropna(subset=['完整時間'])

        go_time = calculate_hours(go_df['完整時間'].tolist())
        back_time = calculate_hours(back_df['完整時間'].tolist())

        # ===== 天數統計 =====
        total_days = df[['月', '日']].drop_duplicates().shape[0]
        go_days = go_df[['月', '日']].drop_duplicates().shape[0]
        back_days = back_df[['月', '日']].drop_duplicates().shape[0]

        summary.append({
            "年份": sheet,
            "總天數": total_days,
            "去程天數": go_days,
            "回程天數": back_days,
            "總時間": round(go_time + back_time, 2),
            "去程時間": round(go_time, 2),
            "回程時間": round(back_time, 2)
        })

    summary_df = pd.DataFrame(summary).sort_values("年份", ascending=False)

    return all_data, summary_df


all_data, summary_df = load_data()

# ==============================
# 1️⃣ 年度統計（選年份,卡片顯示）
# ==============================

st.subheader("1️⃣年度統計")

selected_year_stat = st.selectbox(
    "選擇統計年份",
    summary_df["年份"],
    key="year_stat"
)

year_stat = summary_df[summary_df["年份"] == selected_year_stat].iloc[0]

col1, col2, col3 = st.columns(3)
col1.metric("總天數", year_stat["總天數"])
col2.metric("去程天數", year_stat["去程天數"])
col3.metric("回程天數", year_stat["回程天數"])

col4, col5, col6 = st.columns(3)
col4.metric("總時間(小時)", year_stat["總時間"])
col5.metric("去程時間(小時)", year_stat["去程時間"])
col6.metric("回程時間(小時)", year_stat["回程時間"])

st.markdown("---")

# ==============================
# 2️⃣ 每日行程（分日顯示）
# ==============================

st.subheader("2️⃣每日行程")

selected_year = st.selectbox("選擇年份", summary_df["年份"])

year_df = all_data[selected_year]

grouped = year_df.groupby(['月', '日'])

for (m, d), g in grouped:

    st.markdown(f"###   📍{m}月{d}日")

    display_df = g[['時間', '地點', '去回程']].copy()

    st.dataframe(display_df, use_container_width=True)

# ==============================
# 3️⃣ 地點關鍵字搜尋
# ==============================

st.subheader("3️⃣地點查詢")

keyword = st.text_input("輸入地點關鍵字")

if keyword:

    results = []

    for year, df in all_data.items():

        match_df = df[df['地點'].astype(str).str.contains(keyword, na=False)]

        for _, row in match_df.iterrows():
            results.append({
                "年份": year,
                "月": row['月'],
                "日": row['日'],
                "時間": row['時間'],
                "地點": row['地點']
            })

    if results:
        result_df = pd.DataFrame(results)
        result_df = result_df.sort_values(
            ["年份", "月", "日"],
            ascending=[False, True, True]
        )
        st.dataframe(result_df, use_container_width=True)
    else:
        st.warning("沒有找到相關地點")
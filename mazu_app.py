import streamlit as st
import pandas as pd
import requests
from io import BytesIO

st.set_page_config(page_title="白沙屯媽進香資料記錄", layout="wide")

st.title("🔴 白沙屯媽進香資料記錄🔴 ")

file_url = "https://raw.githubusercontent.com/suptuchstop/mazu--cloud/main/BaishatunMAZU_Data.xlsx"

# ==============================
# 讀取 Excel
# ==============================

response = requests.get(file_url)
response.raise_for_status()

excel_data = BytesIO(response.content)
xls = pd.ExcelFile(excel_data, engine="openpyxl")

all_data = {}
summary = []

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
    go_time = 0
    back_time = 0

    go_df = df[df['去回程'] == '去'].dropna(subset=['完整時間'])
    back_df = df[df['去回程'] == '回'].dropna(subset=['完整時間'])

    go_times = go_df['完整時間'].tolist()
    back_times = back_df['完整時間'].tolist()

    for i in range(1, len(go_times)):
        diff = (go_times[i] - go_times[i - 1]).total_seconds()
        if 0 < diff <= 60 * 60 * 24:
            go_time += diff / 3600

    for i in range(1, len(back_times)):
        diff = (back_times[i] - back_times[i - 1]).total_seconds()
        if 0 < diff <= 60 * 60 * 24:
            back_time += diff / 3600

    # ===== 天數統計 =====
    total_days = df[['月', '日']].drop_duplicates().shape[0]
    go_days = go_df[['月', '日']].drop_duplicates().shape[0]
    back_days = back_df[['月', '日']].drop_duplicates().shape[0]

    summary.append({
        "年份": sheet,
        "總天數": total_days,
        "去程天數": go_days,
        "回程天數": back_days,
        "總時間(時)": round(go_time + back_time, 2),
        "去程時間(時)": round(go_time, 2),
        "回程時間(時)": round(back_time, 2)
    })

summary_df = pd.DataFrame(summary).sort_values("年份", ascending=False)

# ==============================
# 年度總覽
# ==============================

st.subheader("1️⃣年度統計")
st.dataframe(summary_df, use_container_width=True)

# ==============================
# 年度詳細頁
# ==============================

st.subheader("2️⃣年度詳細資料")

selected_year = st.selectbox("選擇年份", summary_df["年份"])

year_df = all_data[selected_year]

st.write(f"{selected_year} 年每日行程")

daily_df = year_df[['月', '日', '時間', '地點', '去回程']].copy()
st.dataframe(daily_df, use_container_width=True)

# ==============================
# 地點關鍵字搜尋
# ==============================

st.subheader("3️⃣地點關鍵字搜尋")

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
        st.dataframe(result_df, use_container_width=True)
    else:
        st.warning("沒有找到相關地點")
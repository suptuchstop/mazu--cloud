import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import base64

# ==============================
# 應用程式配置
# ==============================
st.set_page_config(page_title="白沙屯媽進香資料記錄", layout="wide")

FILE_URL = "https://raw.githubusercontent.com/suptuchstop/mazu--cloud/main/BaishatunMAZU_Data.xlsx"
APP_TITLE = "🔥白沙屯媽進香資料記錄🔥"
WATERMARK_IMAGE_PATH = "mazu_logo.png"

# ==============================
# CSS
# ==============================
@st.cache_data
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return ""

img_base64 = get_base64_image(WATERMARK_IMAGE_PATH)

css = """
<style>
.stApp{
background:linear-gradient(135deg,#2b0000,#4b0000,#1a0000);
color:white;
}
[data-testid="stDataFrame"]{
background:transparent !important;
}
</style>
"""

st.markdown(css, unsafe_allow_html=True)

if img_base64:
    st.markdown(
        f'<img src="data:image/png;base64,{img_base64}" style="position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);opacity:0.15;width:700px;">',
        unsafe_allow_html=True
    )

st.title(APP_TITLE)

# ==============================
# 讀取 Excel
# ==============================
@st.cache_resource
def fetch_excel():

    r = requests.get(FILE_URL)
    r.raise_for_status()

    return pd.ExcelFile(BytesIO(r.content), engine="openpyxl")


@st.cache_data
def process_year_data(_xls, year):

    df = pd.read_excel(_xls, sheet_name=year)
    df.columns = df.columns.str.strip()

    df['去回程'] = df['去回程'].astype(str).str.strip()

    df['完整時間'] = pd.to_datetime(
        df['月'].astype(str) + "-" +
        df['日'].astype(str) + " " +
        df['時間'].astype(str),
        format="%m-%d %H:%M",
        errors="coerce"
    )

    df = df.sort_values("完整時間")
    df = df.dropna(subset=["完整時間"])

    return df


xls = fetch_excel()

years = sorted(xls.sheet_names, reverse=True)

# ==============================
# 年份選擇
# ==============================
st.subheader("1️⃣ 年度統計與每日行程")

year = st.selectbox("選擇年份", years)

df = process_year_data(xls, year)

# ==============================
# 年度統計
# ==============================

go_df = df[df["去回程"] == "去"]
back_df = df[df["去回程"] == "回"]

col1, col2, col3 = st.columns(3)

col1.metric("總天數", df[['月','日']].drop_duplicates().shape[0])
col2.metric("去程天數", go_df[['月','日']].drop_duplicates().shape[0])
col3.metric("回程天數", back_df[['月','日']].drop_duplicates().shape[0])

# ==============================
# 每日摘要
# ==============================

with st.expander(f"{year} 每日摘要"):

    grouped = df.groupby(["月","日"])

    for (m,d), g in grouped:

        g = g.sort_values("完整時間")

        start = g.iloc[0]

        start_text = f"{year}/{m}/{d} {start['時間']} {start['地點']} 起駕"

        summary = [start_text]

        # 午休
        if "停駐駕" in g.columns:
            lunch = g[g["停駐駕"].astype(str).str.contains("午休", na=False)]

            if not lunch.empty:
                r = lunch.iloc[0]
                summary.append(
                    f"{year}/{m}/{d} {r['時間']} {r['地點']} 午休"
                )

        # 駐駕
        if "停駐駕" in g.columns:
            stay = g[g["停駐駕"].astype(str).str.contains("駐駕", na=False)]

            if not stay.empty:
                r = stay.iloc[0]
                summary.append(
                    f"{year}/{m}/{d} {r['時間']} {r['地點']} 駐駕"
                )

        summary_line = f"{m}/{d} | " + " ; ".join(summary)

        # 點日期展開詳細
        with st.expander(summary_line):

            display_df = g[['時間','地點','去回程']].copy()

            st.dataframe(display_df, use_container_width=True)

st.markdown("---")

# ==============================
# 地點搜尋
# ==============================

st.subheader("2️⃣ 地點查詢")

keyword = st.text_input("輸入地點關鍵字")

if keyword:

    results = []

    for y in years:

        d = process_year_data(xls, y)

        match = d[d["地點"].astype(str).str.contains(keyword, na=False)]

        if not match.empty:

            match = match.copy()
            match["年份"] = y

            results.append(match[['年份','時間','地點','去回程']])

    if results:

        final = pd.concat(results)

        st.dataframe(final, use_container_width=True)

    else:

        st.warning("沒有找到資料")
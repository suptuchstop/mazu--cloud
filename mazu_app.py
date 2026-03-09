import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import base64

st.set_page_config(page_title="白沙屯媽進香資料記錄", layout="wide")

FILE_URL = "https://raw.githubusercontent.com/suptuchstop/mazu--cloud/main/BaishatunMAZU_Data.xlsx"
APP_TITLE = "🔥白沙屯媽進香資料記錄🔥"
WATERMARK_IMAGE_PATH = "mazu_logo.png"


# ==============================
# 讀取浮水印
# ==============================

@st.cache_data
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return ""


img_base64 = get_base64_image(WATERMARK_IMAGE_PATH)

# ==============================
# UI
# ==============================

css = """
<style>

.stApp{
background:linear-gradient(135deg,#2b0000,#4b0000,#1a0000);
color:white;
}

.watermark{
position:fixed;
top:50%;
left:50%;
transform:translate(-50%,-50%);
opacity:0.2;
z-index:0;
pointer-events:none;
filter:drop-shadow(0 0 100px gold);
}

section[data-testid="stMain"]{
position:relative;
z-index:1;
}

[data-testid="stDataFrame"]{
background:transparent !important;
}

</style>
"""

st.markdown(css, unsafe_allow_html=True)

if img_base64:
    st.markdown(
        f'<img src="data:image/png;base64,{img_base64}" class="watermark" width="700">',
        unsafe_allow_html=True
    )

st.title(APP_TITLE)

# ==============================
# 讀取 Excel
# ==============================

@st.cache_resource
def fetch_excel():

    response = requests.get(FILE_URL)

    excel_data = BytesIO(response.content)

    return pd.ExcelFile(excel_data, engine="openpyxl")


@st.cache_data
def load_year(_xls, sheet):

    df = pd.read_excel(_xls, sheet_name=sheet)

    df.columns = df.columns.str.strip()

    df["去回程"] = df["去回程"].astype(str).str.strip()

    df["完整時間"] = pd.to_datetime(
        df["月"].astype(str) + "-" +
        df["日"].astype(str) + " " +
        df["時間"].astype(str),
        format="%m-%d %H:%M",
        errors="coerce"
    )

    df = df.sort_values("完整時間")

    return df


xls = fetch_excel()

years = sorted(xls.sheet_names, reverse=True)

# ==============================
# 年份選擇
# ==============================

st.subheader("1️⃣ 年度行程")

year = st.selectbox("選擇年份", years)

df = load_year(xls, year)

# ==============================
# 每日摘要
# ==============================

grouped = df.groupby(["月", "日"])

for (m, d), g in grouped:

    g = g.sort_values("完整時間")

    start = g.iloc[0]

    start_time = start["完整時間"]

    start_place = start["地點"]

    # 午休
    lunch = g[g.iloc[:, 7].astype(str).str.contains("午休", na=False)]

    # 駐駕
    stay = g[g.iloc[:, 7].astype(str).str.contains("駐駕", na=False)]

    summary = []

    summary.append(
        f"起駕:{year}/{m}/{d} {start_time.strftime('%H:%M')} {start_place}"
    )

    if not lunch.empty:

        r = lunch.iloc[0]

        summary.append(
            f"{year}/{m}/{d} {r['完整時間'].strftime('%H:%M')} {r['地點']} 午休"
        )

    if not stay.empty:

        r = stay.iloc[0]

        summary.append(
            f"{year}/{m}/{d} {r['完整時間'].strftime('%H:%M')} {r['地點']} 駐駕"
        )

    # 行軍時間
    hours = (
        g["完整時間"].diff()
        .dt.total_seconds()
        .clip(lower=0, upper=86400)
        .sum()
        / 3600
    )

    rush = ""

    if lunch.empty and stay.empty:
        rush = " ⚡急行軍"

    title = f"{m}/{d}  |  行軍 {round(hours,1)} 小時{rush}  |  " + " ; ".join(summary)

    # ==============================
    # 點日期看詳細
    # ==============================

    with st.expander(title):

        detail = g[["完整時間", "地點", "去回程"]].copy()

        detail["完整時間"] = detail["完整時間"].dt.strftime("%H:%M")

        detail = detail.rename(columns={"完整時間": "時間"})

        st.dataframe(detail, use_container_width=True)


st.markdown("---")

# ==============================
# 地點搜尋
# ==============================

st.subheader("2️⃣ 地點查詢")

keyword = st.text_input("輸入地點")

if keyword:

    results = []

    for y in years:

        d = load_year(xls, y)

        match = d[d["地點"].astype(str).str.contains(keyword, na=False)]

        for _, r in match.iterrows():

            results.append({
                "年份": y,
                "時間": r["完整時間"],
                "地點": r["地點"]
            })

    if results:

        result_df = pd.DataFrame(results)

        result_df["時間"] = result_df["時間"].dt.strftime("%Y-%m-%d %H:%M")

        result_df = result_df.sort_values("時間", ascending=False)

        st.dataframe(result_df, use_container_width=True)

    else:

        st.warning("沒有找到資料")
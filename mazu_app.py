import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="白沙屯媽祖進香記錄", layout="wide")

# ==========================
# 🔴 紅金主題
# ==========================
st.markdown("""
<style>
body { background-color: #5b0000; }
h1, h2, h3 { color: gold; }
section[data-testid="stSidebar"] { background-color: #7a0000; }
</style>
""", unsafe_allow_html=True)

# ==========================
# 📥 讀取資料
# ==========================
@st.cache_data
def load_data():
    file_path = "BaishatunMAZU_Data.xlsx"
    xls = pd.ExcelFile(file_path)

    all_data = []

    for sheet in xls.sheet_names:

        if not sheet.strip().isdigit():
            continue

        sheet_df = pd.read_excel(xls, sheet_name=sheet)
        sheet_df = sheet_df.iloc[:, :8]

        while sheet_df.shape[1] < 8:
            sheet_df[f"extra_{sheet_df.shape[1]}"] = ""

        sheet_df.columns = ["年份","歲次","月","日","時間","地點","去回程","停駐駕"]
        sheet_df["年份"] = sheet.strip()

        # 建立完整時間（用來計算與排序）
        def build_datetime(row):
            try:
                hour, minute = str(row["時間"]).split(":")
                return datetime(
                    int(row["年份"]),
                    int(row["月"]),
                    int(row["日"]),
                    int(hour),
                    int(minute)
                )
            except:
                return pd.NaT

        sheet_df["完整時間"] = sheet_df.apply(build_datetime, axis=1)

        all_data.append(sheet_df)

    df = pd.concat(all_data, ignore_index=True)

    return df


df = load_data()

# ==========================
# 🔥 主畫面
# ==========================
st.title("🔥 白沙屯媽祖進香記錄 🔥")

menu = st.sidebar.radio("功能選單", [
    "年度統計",
    "每日行程",
    "地點查詢"
])

# ==========================
# 1️⃣ 年度統計（年份大 → 小）
# ==========================
if menu == "年度統計":

    st.header("📊 年度統計")

    stats_list = []

    for year in sorted(df["年份"].unique(), reverse=True):

        year_df = df[df["年份"] == year].sort_values("完整時間")

        total_days = year_df["日"].nunique()
        go_days = year_df[year_df["去回程"]=="去程"]["日"].nunique()
        back_days = year_df[year_df["去回程"]=="回程"]["日"].nunique()

        # 總時數
        if year_df["完整時間"].notna().sum() > 1:
            total_hours = (
                year_df["完整時間"].max() -
                year_df["完整時間"].min()
            ).total_seconds() / 3600
        else:
            total_hours = 0

        # 去程時數
        go_df = year_df[year_df["去回程"]=="去程"]
        if go_df["完整時間"].notna().sum() > 1:
            go_hours = (
                go_df["完整時間"].max() -
                go_df["完整時間"].min()
            ).total_seconds() / 3600
        else:
            go_hours = 0

        # 回程時數
        back_df = year_df[year_df["去回程"]=="回程"]
        if back_df["完整時間"].notna().sum() > 1:
            back_hours = (
                back_df["完整時間"].max() -
                back_df["完整時間"].min()
            ).total_seconds() / 3600
        else:
            back_hours = 0

        stats_list.append({
            "年份": year,
            "總天數": total_days,
            "去程天數": go_days,
            "回程天數": back_days,
            "總時數(小時)": round(total_hours,2),
            "去程時數(小時)": round(go_hours,2),
            "回程時數(小時)": round(back_hours,2)
        })

    stats_df = pd.DataFrame(stats_list)

    st.dataframe(stats_df, use_container_width=True)

# ==========================
# 2️⃣ 每日行程（不顯示完整時間）
# ==========================
elif menu == "每日行程":

    st.header("📅 每日行程")

    year = st.selectbox(
        "選擇年份",
        sorted(df["年份"].unique(), reverse=True)
    )

    year_df = df[df["年份"] == year]

    grouped = year_df.groupby(["月", "日"])

    for (month, day), data in grouped:

        st.subheader(f"📍 {month}月{day}日")

        # 排序後刪除「完整時間」欄位再顯示
        display_df = (
            data.sort_values("完整時間")
            .drop(columns=["完整時間"])
        )

        st.dataframe(display_df, use_container_width=True)

# ==========================
# 3️⃣ 地點查詢
# ==========================
elif menu == "地點查詢":

    st.header("🔍 地點查詢")

    keyword = st.text_input("輸入關鍵字")

    if keyword:
        result = df[df["地點"].astype(str).str.contains(keyword, na=False)]

        st.write(f"找到 {len(result)} 筆資料")

        display_df = (
            result.sort_values(["年份","完整時間"], ascending=[False, True])
            .drop(columns=["完整時間"])
        )

        st.dataframe(display_df, use_container_width=True)
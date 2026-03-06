import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import base64
from datetime import timedelta

# ==============================
# 應用程式配置
# ==============================
st.set_page_config(page_title="白沙屯媽進香資料記錄", layout="wide")

# 常數配置
FILE_URL = "https://raw.githubusercontent.com/suptuchstop/mazu--cloud/main/BaishatunMAZU_Data.xlsx"
APP_TITLE = "🔥 白沙屯媽進香資料記錄 🔥"
AUTHOR_TAG = "βŁãÇķ™ 製"
WATERMARK_IMAGE_PATH = "mazu_logo.png"

# ==============================
# UI 介面優化（浮水印與背景）
# ==============================
@st.cache_data
def get_base64_image(image_path):
    """讀取圖片並轉換為 base64 格式，用於 HTML/CSS"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        st.error(f"找不到圖片檔案: {image_path}，浮水印功能將無法顯示。")
        return ""

img_base64 = get_base64_image(WATERMARK_IMAGE_PATH)

if img_base64:
    st.markdown(
        f"""
        <style>
        /* 🔥 暗紅漸層背景 */
        .stApp {{
            background: linear-gradient(
                135deg,
                #2b0000 0%,
                #4b0000 50%,
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
            opacity: 0.28;
            z-index: 0;
            pointer-events: none;
            filter: drop-shadow(0 0 80px gold);
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

st.title(f"{APP_TITLE}   {AUTHOR_TAG}")

# ==============================
# 資料讀取與處理優化 (精細化快取)
# ==============================

@st.cache_resource
def fetch_raw_excel():
    """僅負責遠端下載 Excel 檔案並載入為 ExcelFile 物件，最小化快取"""
    with st.spinner("正在從雲端讀取資料..."):
        try:
            response = requests.get(FILE_URL)
            response.raise_for_status()
            excel_data = BytesIO(response.content)
            # 傳回 pd.ExcelFile，保留多個 Sheet 的讀取能力
            return pd.ExcelFile(excel_data, engine="openpyxl")
        except Exception as e:
            st.error(f"資料讀取失敗，請檢查網路或檔案連結。錯誤資訊: {e}")
            return None

@st.cache_data
def process_year_data(_xls, year_sheet_name):
    """
    處理單一月份的資料並計算統計資訊。
    優點：只處理需要的月份，避免多餘計算。
    """
    # 讀取特定 Sheet
    df = pd.read_excel(_xls, sheet_name=year_sheet_name)
    df.columns = df.columns.str.strip() # 清除欄位首尾空格

    # 資料整理：去回程欄位正規化
    df['去回程'] = (
        df['去回程']
        .astype(str)
        .str.strip()
        .replace({'去程': '去', '回程': '回'})
    )

    # 資料整理：時間欄位組合與排序
    df['完整時間'] = pd.to_datetime(
        df['月'].astype(str) + '-' +
        df['日'].astype(str) + ' ' +
        df['時間'].astype(str),
        format='%m-%d %H:%M',
        errors='coerce'
    )
    df = df.sort_values('完整時間') # 重要：必須先排序

    # 資料整理：僅保留時間有效的行，並確保日期是整數類型
    df = df.dropna(subset=['完整時間'])
    df['月'] = df['月'].astype(int)
    df['日'] = df['日'].astype(int)

    # ----- 統計計算 (向量化優化) -----
    
    # 計算時間差：用 diff() 取代迴圈，單位是秒
    df['time_diff_sec'] = df['完整時間'].diff().dt.total_seconds()
    
    # 篩選有效的行程（過濾過長或負值的时间，同原代碼邏輯）
    valid_diff_mask = (df['time_diff_sec'] > 0) & (df['time_diff_sec'] <= 86400)
    df.loc[valid_diff_mask, 'effective_hours'] = df.loc[valid_diff_mask, 'time_diff_sec'] / 3600
    df['effective_hours'] = df['effective_hours'].fillna(0) # 確保無 NaN

    # 分離去程與回程資料
    go_df = df[df['去回程'] == '去']
    back_df = df[df['去回程'] == '回']

    #===== 天數統計 =====
    total_days = df[['月', '日']].drop_duplicates().shape[0]
    go_days = go_df[['月', '日']].drop_duplicates().shape[0]
    back_days = back_df[['月', '日']].drop_duplicates().shape[0]

    #===== 時間統計 =====
    go_time = go_df['effective_hours'].sum()
    back_time = back_df['effective_hours'].sum()

    # 組合統計摘要資料
    year_summary = {
        "總天數": total_days,
        "去程天數": go_days,
        "回程天數": back_days,
        "總時間": round(go_time + back_time, 2),
        "去程時間": round(go_time, 2),
        "回程時間": round(back_time, 2)
    }

    # 返回處理後的原始 DataFrame 和統計摘要
    return df, year_summary

# 1. 載入原始資料
xls = fetch_raw_excel()

if xls:
    # 取得所有 Sheet 名稱（即年份）
    available_years = sorted(xls.sheet_names, reverse=True)

    # ==============================
    # 1️⃣ 年度統計與細節（選年份）
    # ==============================
    st.subheader("1️⃣ 年度統計與行程細節")

    # 使用下拉選單選擇特定年份
    selected_year = st.selectbox(
        "選擇要查看的年份",
        available_years,
        key="year_selector"
    )

    # 2. 處理所選年份的資料
    year_df, year_stat = process_year_data(xls, selected_year)

    if year_stat:
        # 卡片顯示統計
        col1, col2, col3 = st.columns(3)
        col1.metric("總天數", f"{year_stat['總天數']} 天")
        col2.metric("去程天數", f"{year_stat['去程天數']} 天")
        col3.metric("回程天數", f"{year_stat['回程天數']} 天")

        col4, col5, col6 = st.columns(3)
        col4.metric("總時間", f"{year_stat['總時間']} 小時")
        col5.metric("去程時間", f"{year_stat['去程時間']} 小時")
        col6.metric("回程時間", f"{year_stat['回程時間']} 小時")

        # 進一步細分，顯示該年份的每日行程
        with st.expander(f"點擊展開 / 收合 {selected_year} 每日行程詳情", expanded=False):
            # 分日顯示
            grouped = year_df.groupby(['月', '日'])
            for (m, d), group in grouped:
                st.markdown(f"#### 📍 {m}月{d}日")
                # 重新選擇欄位並格式化
                display_df = group[['完整時間', '地點', '去回程']].copy()
                # 格式化完整時間欄位，使其只顯示時間部分，並改名
                display_df['完整時間'] = display_df['完整時間'].dt.strftime('%H:%M')
                display_df = display_df.rename(columns={'完整時間': '時間'})
                st.dataframe(display_df, use_container_width=True)
    
    st.markdown("---")

    # ==============================
    # 2️⃣ 地點關鍵字搜尋
    # ==============================
    st.subheader("2️⃣ 地點查詢 (跨年份搜尋)")

    keyword = st.text_input("輸入地點關鍵字（例如：白沙屯拱天宮）", placeholder="搜尋地點...")

    if keyword:
        # 地點搜尋函式 (集中在此區域，避免與其他區塊交互作用)
        results_df = []
        for year in available_years:
            # 對每個年份進行處理
            df_for_search, _ = process_year_data(xls, year)
            
            # 使用 contains 進行全模糊匹配
            match_df = df_for_search[df_for_search['地點'].astype(str).str.contains(keyword, na=False)]
            
            if not match_df.empty:
                match_df = match_df.copy()
                match_df['年份'] = year # 加入年份資訊
                match_df = match_df[['年份', '完整時間', '地點', '去回程']]
                results_df.append(match_df)

        if results_df:
            # 整合所有年份結果
            final_result_df = pd.concat(results_df)
            
            # 將完整時間轉換為可讀日期格式（包含年份）
            final_result_df['完整時間'] = final_result_df['完整時間'].dt.strftime('%Y-%m-%d %H:%M')
            final_result_df = final_result_df.rename(columns={'完整時間': '日期時間'})
            
            # 排序：年份降序，時間升序
            final_result_df = final_result_df.sort_values(
                ["日期時間"],
                ascending=[False]
            )
            st.success(f"找到 {len(final_result_df)} 筆結果。")
            st.dataframe(final_result_df, use_container_width=True)
        else:
            st.warning("沒有找到相關地點資訊。")

else:
    st.warning("無法載入資料，請確認遠端檔案連結。")
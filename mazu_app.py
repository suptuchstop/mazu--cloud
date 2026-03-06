import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import base64
from datetime import timedelta
import plotly.express as px 

# ==============================
# 應用程式配置
# ==============================
st.set_page_config(page_title="白沙屯媽進香資料記錄", layout="wide")

# 常數配置
FILE_URL = "https://raw.githubusercontent.com/suptuchstop/mazu--cloud/main/BaishatunMAZU_Data.xlsx"
APP_TITLE = "🔥 白沙屯媽進香資料記錄 🔥"
AUTHOR_TAG = " " 
WATERMARK_IMAGE_PATH = "mazu_logo.png"

# ==============================
# UI 介面優化 Part 1：基礎 CSS (浮水印, 全域字體)
# ==============================
@st.cache_data
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return ""

img_base64 = get_base64_image(WATERMARK_IMAGE_PATH)

# ==============================
# 🚨 修正字體顏色 CSS (確保所有表格文字變白)
# ==============================
ultimate_css = f"""
<style>
    /* 1. 全域背景與基礎文字 */
    .stApp {{
        background: linear-gradient(135deg, #2b0000 0%, #4b0000 50%, #1a0000 100%);
        color: #ffffff !important;
    }}

    /* 強制所有 Streamlit 原生元件文字變白 */
    .stApp label, .stApp p, .stApp span, .stApp div, .stApp h1, .stApp h2, .stApp h3 {{
        color: #ffffff !important;
    }}

    /* 2. 浮水印 */
    .watermark {{
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        opacity: 0.28;
        z-index: 0;
        pointer-events: none;
        filter: drop-shadow(0 0 100px gold);
    }}
    section[data-testid="stMain"] {{ position: relative; z-index: 1; }}

    /* 3. 🚨 核心修正：讓表格 (st.dataframe) 文字變白 */
    /* 針對 Streamlit 新版 Dataframe 的內部元件進行顏色覆蓋 */
    [data-testid="stDataFrame"] {{
        background-color: #220000 !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }}

    /* 這是最關鍵的一段：強制修改 Dataframe 內部的文字渲染顏色 */
    [data-testid="stDataFrame"] div[data-testid="stTable"] {{
        color: #ffffff !important;
    }}

    /* 針對 Canvas 渲染和表格儲存格的顏色 */
    [data-testid="stDataFrame"] * {{
        color: #ffffff !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }}

    /* 表格表頭強化 */
    [data-testid="stDataFrame"] thead th {{
        background-color: #1a0000 !important;
        color: #ffffff !important;
        font-weight: bold !important;
    }}

    /* 4. 輸入框與下拉選單深色化+白字 */
    .stSelectbox div[data-baseweb="select"],
    .stTextInput div[data-baseweb="base-input"],
    input {{
        background-color: #220000 !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
    }}
    
    /* 下拉箭頭與圖示變白 */
    svg {{ fill: #ffffff !important; }}

    /* 5. 修正 Expander 字體 */
    [data-testid="stExpander"] {{
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }}
</style>
"""

st.markdown(ultimate_css, unsafe_allow_html=True)

if img_base64:
    st.markdown(f'<img src="data:image/png;base64,{img_base64}" class="watermark" width="700">', unsafe_allow_html=True)

st.title(f"{APP_TITLE}   {AUTHOR_TAG}")

# ==============================
# 資料處理邏輯 (保持您的分析功能)
# ==============================
@st.cache_resource
def fetch_raw_excel():
    try:
        response = requests.get(FILE_URL)
        response.raise_for_status()
        return pd.ExcelFile(BytesIO(response.content), engine="openpyxl")
    except Exception as e:
        st.error(f"讀取失敗: {e}")
        return None

@st.cache_data
def process_year_data(_xls, year_sheet_name):
    df = pd.read_excel(_xls, sheet_name=year_sheet_name)
    df.columns = df.columns.str.strip()
    df['去回程'] = df['去回程'].astype(str).str.strip().replace({'去程': '去', '回程': '回'})
    df['完整時間'] = pd.to_datetime(df['月'].astype(str) + '-' + df['日'].astype(str) + ' ' + df['時間'].astype(str), format='%m-%d %H:%M', errors='coerce')
    df = df.sort_values('完整時間').dropna(subset=['完整時間'])
    df['time_diff_sec'] = df['完整時間'].diff().dt.total_seconds()
    valid_mask = (df['time_diff_sec'] > 0) & (df['time_diff_sec'] <= 86400)
    df.loc[valid_mask, 'effective_hours'] = df.loc[valid_mask, 'time_diff_sec'] / 3600
    df['effective_hours'] = df['effective_hours'].fillna(0)
    
    year_summary = {
        "總天數": df[['月', '日']].drop_duplicates().shape[0],
        "去程天數": df[df['去回程'] == '去'][['月', '日']].drop_duplicates().shape[0],
        "回程天數": df[df['去回程'] == '回'][['月', '日']].drop_duplicates().shape[0],
        "總時間": round(df['effective_hours'].sum(), 2),
        "去程時間": round(df[df['去回程'] == '去']['effective_hours'].sum(), 2),
        "回程時間": round(df[df['去回程'] == '回']['effective_hours'].sum(), 2)
    }
    df['activity_date'] = df['完整時間'].dt.date
    daily_stats = df.groupby(['去回程', 'activity_date'])['effective_hours'].sum().reset_index()
    daily_stats['day_number'] = daily_stats.groupby('去回程')['activity_date'].rank(method='first').astype(int)
    return df, year_summary, daily_stats

xls = fetch_raw_excel()
if xls:
    available_years = sorted(xls.sheet_names, reverse=True)
    selected_year = st.selectbox("選擇要查看的年份", available_years, key="year_selector")
    year_df, year_stat, daily_stats = process_year_data(xls, selected_year)

    if year_stat:
        c1, c2, c3 = st.columns(3)
        c1.metric("總天數", f"{year_stat['總天數']} 天")
        c2.metric("去程天數", f"{year_stat['去程天數']} 天")
        c3.metric("回程天數", f"{year_stat['回程天數']} 天")
        c4, c5, c6 = st.columns(3)
        c4.metric("總時間", f"{year_stat['總時間']} 小時")
        c5.metric("去程時間", f"{year_stat['去程時間']} 小時")
        c6.metric("回程時間", f"{year_stat['回程時間']} 小時")

        with st.expander(f"📖 點擊展開 {selected_year} 每日詳細行程", expanded=False):
            for (m, d), group in year_df.groupby(['月', '日']):
                st.markdown(f"**📍 {m}月{d}日**")
                disp = group[['完整時間', '地點', '去回程']].copy()
                disp['完整時間'] = disp['完整時間'].dt.strftime('%H:%M')
                st.dataframe(disp.rename(columns={'完整時間': '時間'}), use_container_width=True)

    st.markdown("---")
    st.subheader(f"📊 {selected_year} 去回程每日節奏對比")
    col_a, col_b = st.columns([1, 2])
    with col_a:
        avg_go = round(year_stat["去程時間"] / year_stat["去程天數"], 1) if year_stat["去程天數"] > 0 else 0
        avg_back = round(year_stat["回程時間"] / year_stat["回程天數"], 1) if year_stat["回程天數"] > 0 else 0
        st.metric("去程日均時數", f"{avg_go} hr/d")
        st.metric("回程日均時數", f"{avg_back} hr/d")
    with col_b:
        fig = px.bar(daily_stats, x="day_number", y="effective_hours", color="去回程", barmode="group",
                     color_discrete_map={'去': 'gold', '回': 'deepskyblue'})
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#ffffff')
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🔍 跨年份地點查詢")
    kw = st.text_input("輸入關鍵字搜尋", placeholder="例如：北港朝天宮")
    if kw:
        results = []
        for y in available_years:
            df_y, _, _ = process_year_data(xls, y)
            m = df_y[df_y['地點'].
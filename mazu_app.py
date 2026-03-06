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
AUTHOR_TAG = "βŁãÇķ™" 
WATERMARK_IMAGE_PATH = "mazu_logo.png"

# ==============================
# UI 介面優化 Part 1：基礎 CSS (浮水印, 全域字體)
# ==============================
@st.cache_data
def get_base64_image(image_path):
    """讀取圖片並轉換為 base64 格式，用於 HTML/CSS"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return ""

img_base64 = get_base64_image(WATERMARK_IMAGE_PATH)

# ==============================
# 🚨 視覺調和 CSS 優化 (深色融和 + 終極白字覆蓋)
# ==============================
# 定義主題深色
theme_dark_color = "#220000" # 深暗紅/黑

ultimate_css = f"""
<style>
    /* ----------------------------------------------------------- */
    /* 1. 全域設定：背景與字體 (強大白字) */
    /* ----------------------------------------------------------- */
    .stApp {{
        background: linear-gradient(
            135deg,
            #2b0000 0%,
            #4b0000 50%,
            #1a0000 100%
        );
        /* 🚨 關鍵：全域字體設為白色 */
        color: #ffffff !important;
    }}

    /* 強制所有標籤（Label）、普通文字、跨年份地點查詢等變白 */
    .stApp label, .stApp p, .stApp span, .stApp div, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {{
        color: #ffffff !important;
    }}

    /* ----------------------------------------------------------- */
    /* 2. 浮水印 */
    /* ----------------------------------------------------------- */
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

    /* 讓內容浮在上層 */
    section[data-testid="stMain"] {{
        position: relative;
        z-index: 1;
    }}

    /* ----------------------------------------------------------- */
    /* 🚨 視覺調和與終極修正：表格 (Dataframe) 深色化+強制白字 */
    /* 🚨 解決「字體看不見」的問題 */
    /* ----------------------------------------------------------- */
    [data-testid="stDataFrame"] {{
        background-color: {theme_dark_color} !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 4px;
    }}
    
    /* 🚨 終極修正：針對 Dataframe 內部 Canvas/Shadow DOM 的字體覆蓋 */
    /* 試圖強制修改所有內部子元件的文字顏色 */
    [data-testid="stDataFrame"] div,
    [data-testid="stDataFrame"] table,
    [data-testid="stDataFrame"] thead,
    [data-testid="stDataFrame"] tbody,
    [data-testid="stDataFrame"] tr,
    [data-testid="stDataFrame"] th,
    [data-testid="stDataFrame"] td,
    [data-testid="stDataFrame"] canvas {{
        background-color: {theme_dark_color} !important;
        color: #ffffff !important; /* 儲存格文字強制變白，極其關鍵 */
        border-color: rgba(255, 255, 255, 0.2) !important; /* Clearer white grid */
    }}

    /* 表格頭部 (Header) 文字變白並加粗 */
    [data-testid="stDataFrame"] thead th {{
        color: #ffffff !important;
        font-weight: bold !important;
        background-color: #1a0000 !important;
    }}

    /* 滑鼠懸停 (Hover) 時的行背景色 */
    [data-testid="stDataFrame"] tbody tr:hover td {{
        background-color: rgba(255, 255, 255, 0.08) !important;
    }}

    /* ----------------------------------------------------------- */
    /* 4. 視覺調和：輸入元件 (Selectbox, Text Input) 深色化+白字 */
    /* ----------------------------------------------------------- */
    .stSelectbox div[data-baseweb="select"],
    .stTextInput div[data-baseweb="base-input"],
    input,
    .stTextInput input,
    .stTextInput div[role="searchbox"] input {{
        background-color: {theme_dark_color} !important;
        border-color: rgba(255, 255, 255, 0.5) !important;
        border-radius: 4px;
        color: #ffffff !important; /* 強制打字文字變白 */
    }}

    /* 下拉箭頭變白 */
    .stSelectbox svg, [data-baseweb="select"] svg {{
        fill: #ffffff !important;
    }}

    /* 下拉選單「選項列表」保持深色高透明，確保選項清晰 */
    div[data-baseweb="popover"] ul {{
        background-color: rgba(0, 0, 0, 0.9) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }}
    
    div[data-baseweb="popover"] ul li {{
        color: #ffffff !important;
    }}
    
    div[data-baseweb="popover"] ul li:hover {{
        background-color: rgba(255, 255, 255, 0.1) !important;
    }}

    /* ----------------------------------------------------------- */
    /* 5. 其他 UI 微調 */
    /* ----------------------------------------------------------- */
    
    hr {{
        border-color: rgba(255, 255, 255, 0.2) !important;
    }}

    /* Expander（折疊區塊）樣式調整，確保標題字體白色清晰 */
    div[data-testid="stExpander"] {{
        background-color: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 4px;
    }}
    
    div[data-testid="stExpander"] p,
    .st-emotion-cache-16un4o p, .st-emotion-cache-p4m44u p {{
        color: #ffffff !important;
    }}

    /* 確保統計指標卡 (st.metric) 的字體也是白色 */
    .stMetric label, .stMetric p, .stMetric div {{
        color: #ffffff !important;
    }}

    /* 確保 Plotly 圖表的工具列按鈕也是白色 */
    .modebar-btn svg {{
        fill: #ffffff !important;
    }}
</style>
"""

# 載入 CSS
st.markdown(ultimate_css, unsafe_allow_html=True)

# 顯示浮水印
if img_base64:
    st.markdown(
        f'<img src="data:image/png;base64,{img_base64}" class="watermark" width="700">',
        unsafe_allow_html=True
    )

st.title(f"{APP_TITLE}   {AUTHOR_TAG}")

# ==============================
# 資料讀取與處理 (🚨 保留分析邏輯)
# ==============================

@st.cache_resource
def fetch_raw_excel():
    """僅負責遠端下載 Excel 檔案並載入為 ExcelFile 物件，最小化快取"""
    with st.spinner("正在從雲端讀取資料..."):
        try:
            response = requests.get(FILE_URL)
            response.raise_for_status()
            excel_data = BytesIO(response.content)
            return pd.ExcelFile(excel_data, engine="openpyxl")
        except Exception as e:
            st.error(f"資料讀取失敗，請檢查網路或檔案連結。錯誤資訊: {e}")
            return None

@st.cache_data
def process_year_data(_xls, year_sheet_name):
    """處理單一月份的資料，計算統計資訊，並生成繪圖資料。"""
    df = pd.read_excel(_xls, sheet_name=year_sheet_name)
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
    df = df.dropna(subset=['完整時間'])
    df['月'] = df['月'].astype(int)
    df['日'] = df['日'].astype(int)

    # 計算時間差：用 diff() 取代迴圈，單位是秒
    df['time_diff_sec'] = df['完整時間'].diff().dt.total_seconds()
    
    # 有效行程篩選邏輯，這裡需要用來計算小時數
    valid_diff_mask = (df['time_diff_sec'] > 0) & (df['time_diff_sec'] <= 86400)
    
    # 計算每小段行程的小時數
    df.loc[valid_diff_mask, 'effective_hours'] = df.loc[valid_diff_mask, 'time_diff_sec'] / 3600
    df['effective_hours'] = df['effective_hours'].fillna(0) # 確保無 NaN

    # 🚨 關鍵修正：將 'activity_date' 的生成移到分組之前
    df['activity_date'] = df['完整時間'].dt.date

    go_df = df[df['去回程'] == '去']
    back_df = df[df['去回程'] == '回']

    # 1. 統計項目
    total_days = df[['月', '日']].drop_duplicates().shape[0]
    go_days = go_df[['月', '日']].drop_duplicates().shape[0]
    back_days = back_df[['月', '日']].drop_duplicates().shape[0]

    go_time = go_df['effective_hours'].sum()
    back_time = back_df['effective_hours'].sum()

    year_summary = {
        "總天數": total_days,
        "去程天數": go_days,
        "回程天數": back_days,
        "總時間": round(go_time + back_time, 2),
        "去程時間": round(go_time, 2),
        "回程時間": round(back_time, 2)
    }

    # 2. 🚨 深度分析所需的繪圖資料邏輯 (語法錯誤已修正)
    # 分別對去程和回程按日期分組，計算每日總時數 (groupy + sum)
    daily_stats = df.groupby(['去回程', 'activity_date'])['effective_hours'].sum().reset_index()
    
    # 建立一個欄位，標記這是「第幾天」(1, 2, 3...)
    daily_stats['day_number'] = daily_stats.groupby('去回程')['activity_date'].rank(method='first').astype(int)

    return df, year_summary, daily_stats

# ==============================
# 主程式邏輯
# ==============================
xls = fetch_raw_excel()

if xls:
    available_years = sorted(xls.sheet_names, reverse=True)

    # ==============================
    # 1️⃣ 年度統計與行程細節
    # ==============================
    st.subheader("1️⃣ 年度統計與行程細節")

    # [年份下拉選單]
    selected_year = st.selectbox(
        "選擇要查看的年份",
        available_years,
        key="year_selector"
    )

    year_df, year_stat, daily_stats = process_year_data(xls, selected_year)

    if year_stat:
        col1, col2, col3 = st.columns(3)
        col1.metric("總天數", f"{year_stat['總天數']} 天")
        col2.metric("去程天數", f"{year_stat['去程天數']} 天")
        col3.metric("回程天數", f"{year_stat['回程天數']} 天")

        col4, col5, col6 = st.columns(3)
        col4.metric("總時間", f"{year_stat['總時間']} 小時")
        col5.metric("去程時間", f"{year_stat['去程時間']} 小時")
        col6.metric("回程時間", f"{year_stat['回程時間']} 小時")

        # 每日行程詳情
        with st.expander(f"📚 點擊展開或收合 {selected_year} 每日詳細行程詳情", expanded=False):
            grouped = year_df.groupby(['月', '日'])
            for (m, d), group in grouped:
                st.markdown(f"#### 📍 {m}月{d}日")
                display_df = group[['完整時間', '地點', '去回程']].copy()
                display_df['完整時間'] = display_df['完整時間'].dt.strftime('%H:%M')
                display_df = display_df.rename(columns={'完整時間': '時間'})
                
                # [每日詳細行程表格] -> 🚨 字體應已強制變白
                st.dataframe(display_df, use_container_width=True, key=f"df_{m}_{d}")
    
    # ==============================
    # 🚨 深度數據分析：去/回程每日節奏對比
    # ==============================
    st.markdown("---")
    st.subheader(f"📊 深度數據分析：{selected_year} 去/回程每日節奏對比")
    
    analysis_col1, analysis_col2 = st.columns([1, 2]) # 比例 1:2
    
    with analysis_col1:
        st.write(" ") # 增加間距
        st.write(" ")
        st.write("**方向性平均數據：**")
        avg_go_hours = round(year_stat["去程時間"] / year_stat["去程天數"], 1) if year_stat["去程天數"] > 0 else 0
        avg_back_hours = round(year_stat["回程時間"] / year_stat["回程天數"], 1) if year_stat["回程天數"] > 0 else 0
        
        st.metric("去程 平均每日移動時數", f"{avg_go_hours} 小時/天")
        st.metric("回程 平均每日移動時數", f"{avg_back_hours} 小時/天")
        st.info("📊 分析解讀：此指標能告訴您哪個階段（去或回）走得比較趕。")

    with analysis_col2:
        if not daily_stats.empty:
            fig = px.bar(
                daily_stats, 
                x="day_number", # 橫軸：活動第幾天
                y="effective_hours", # 縱軸：移動小時數
                color="去回程", # 顏色：區分去和回
                barmode="group", # ✅ 分組模式：柱子並排對比
                labels={"day_number": "活動天數 (第X天)", "effective_hours": "移動時數 (小時)"},
                title=f"{selected_year} 去回程每日移動時數對比",
                color_discrete_
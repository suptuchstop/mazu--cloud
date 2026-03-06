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

    # 2. 深度分析所需的繪圖資料邏輯
    df['activity_date'] = df['完整時間'].dt.date
    daily_stats = df.groupby(['去回程', 'activity_
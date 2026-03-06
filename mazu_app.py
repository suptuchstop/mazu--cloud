import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import base64
from datetime import timedelta
# 🚨 刪除：from streamlit_javascript import st_javascript # 我們徹底放棄它
import plotly.express as px # 🚨 新增：用於繪製互動式圖表

# ==============================
# 應用程式配置
# ==============================
st.set_page_config(page_title="白沙屯媽進香資料記錄", layout="wide")

# 常數配置
FILE_URL = "https://raw.githubusercontent.com/suptuchstop/mazu--cloud/main/BaishatunMAZU_Data.xlsx"
APP_TITLE = "🔥 白沙屯媽進香資料記錄 🔥"
AUTHOR_TAG = "βŁãÇķ™ 製" # 您原本保留的格
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
        # 如果找不到圖，顯示警告但讓程式能跑
        st.warning(f"找不到圖片檔案: {image_path}，浮水印和 CSS 優化可能受到影響。")
        return ""

img_base64 = get_base64_image(WATERMARK_IMAGE_PATH)

# ==============================
# 🚨 視覺調和 CSS 優化 (放棄透明，改用深色融和+清晰白字)
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
    .stApp label, .stApp p, .stApp span, .stApp div {{
        color: #ffffff !important;
    }}
    
    /* 標題變白 */
    h1, h2, h3, h4, h5, h6 {{
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
    /* 🚨 視覺調和：表格 (Dataframe) 深色化+強大白字 */
    /* 將預設白色改為深主題色，強大白字網格清晰 */
    /* ----------------------------------------------------------- */
    [data-testid="stDataFrame"] {{
        background-color: {theme_dark_color} !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 4px;
    }}
    
    /* 強制表格內部所有層級設為深色背景，字體變白 */
    [data-testid="stDataFrame"] div,
    [data-testid="stDataFrame"] table,
    [data-testid="stDataFrame"] thead,
    [data-testid="stDataFrame"] tbody,
    [data-testid="stDataFrame"] tr,
    [data-testid="stDataFrame"] th,
    [data-testid="stDataFrame"] td,
    [data-testid="stDataFrame"] canvas {{
        background-color: {theme_dark_color} !important;
        color: #ffffff !important; /* 儲存格文字強制變白 */
        border-color: rgba(255, 255, 255, 0.15) !important; /* 淡淡的白色網格線，清晰可見 */
    }}

    /* 表格頭部 (Header) 文字變白並加粗，背景稍微加深 */
    [data-testid="stDataFrame"] thead th {{
        color: #ffffff !important;
        font-weight: bold !important;
        background-color: #1a0000 !important;
    }}

    /* 滑鼠懸停 (Hover) 時的行背景色，稍微變亮以增加層次感 */
    [data-testid="stDataFrame"] tbody tr:hover td {{
        background-color: rgba(255, 255, 255, 0.08) !important;
    }}

    /* ----------------------------------------------------------- */
    /* 🚨 視覺調和：輸入元件 (Selectbox, Text Input) 深色化+強大白字 */
    /* ----------------------------------------------------------- */
    /* 下拉選單和打字欄位背景改為深色，字體變白 */
    .stSelectbox div[data-baseweb="select"],
    .stTextInput div[data-baseweb="base-input"],
    input,
    .stTextInput input,
    .stTextInput div[role="searchbox"] input {{
        background-color: {theme_dark_color} !important; /* 輸入框背景深色 */
        border-color: rgba(255, 255, 255, 0.4) !important; /* 邊框改為較明顯的半透明白 */
        border-radius: 4px;
        color: #ffffff !important; /* 輸入的文字強制變白 */
    }}

    /* 輸入框內的文字顏色 */
    .stSelectbox div[data-baseweb="select"] div,
    .stTextInput div[data-baseweb="base-input"] input,
    input,
    .stTextInput input {{
        color: #ffffff !important;
    }}
    
    /* 預設提示文字 (Placeholder) 在深色背景下需要稍微變暗，否則文字會太亮看不到。
       如果您想要 placeholder 也是實心白字，請刪除這一小段 CSS。 */
    input::placeholder, .stTextInput input::placeholder {{
        color: rgba(255, 255, 255, 0.5) !important;
    }}

    /* 下拉箭頭變白 */
    .stSelectbox svg {{
        fill: #ffffff !important;
    }}

    /* 下拉選單的「選項列表」保持高透明黑色，確保選項文字白色清晰 */
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
    /* 5. 其他 UI 微調與 Expander 清晰白字 */
    /* ----------------------------------------------------------- */
    
    hr {{
        border-color: rgba(255, 255, 255, 0.2) !important;
    }}

    /* Expander（折疊區塊）樣式調整，確保背景和標題字體白色清晰 */
    div[data-testid="stExpander"] {{
        background-color: {theme_dark_color} !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 4px;
    }}
    
    div[data-testid="stExpander"] p,
    .stEmotion-cache-16un4o p, .stEmotion-cache-p4m44u p {{
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

# 載入基礎 CSS
st.markdown(ultimate_css, unsafe_allow_html=True)

# 顯示浮水印
if img_base64:
    st.markdown(
        f'<img src="data:image/png;base64,{img_base64}" class="watermark" width="700">',
        unsafe_allow_html=True
    )

st.title(f"{APP_TITLE}   {AUTHOR_TAG}")

# ==============================
# 資料讀取與處理 (🚨 升級：新增分析邏輯)
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
    
    # 您原本的有效行程篩選邏輯，這裡需要用來計算小時數
    valid_diff_mask = (df['time_diff_sec'] > 0) & (df['time_diff_sec'] <= 86400)
    
    # 計算每小段行程的小時數，新增欄位 'effective_hours'
    df.loc[valid_diff_mask, 'effective_hours'] = df.loc[valid_diff_mask, 'time_diff_sec'] / 3600
    df['effective_hours'] = df['effective_hours'].fillna(0) # 確保無 NaN

    go_df = df[df['去回程'] == '去']
    back_df = df[df['去回程'] == '回']

    # 1. 保留您原本的統計項目
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

    # 🚨 2. 新增：深度分析所需的繪圖資料邏輯
    # 目標：計算「去程」和「回程」每一天的總移動時數。
    
    # 建立一個輔助欄位，標記這是「進香活動的第幾天」
    df['activity_date'] = df['完整時間'].dt.date
    
    # 分別對去程和回程按日期分組，計算每日總時數 (groupy + sum)
    daily_stats = df.groupby(['去回程', 'activity_date'])['effective_hours'].sum().reset_index()
    
    # 建立一個欄位，標記這是「第幾天」(1, 2, 3...)
    daily_stats['day_number'] = daily_stats.groupby('去回程')['activity_date'].rank(method='first').astype(int)

    # 返回處理後的 DataFrame、統計摘要，以及新增的每日統計資料 (用於繪圖)
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

    # [年份下拉選單] -> 🚨 CSS 會強制背景變深色，文字變白色
    selected_year = st.selectbox(
        "選擇要查看的年份",
        available_years,
        key="year_selector"
    )

    # 🚨 升級：函式回傳多一個daily_stats
    year_df, year_stat, daily_stats = process_year_data(xls, selected_year)

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

        # 每日行程詳情
        with st.expander(f"點擊展開 / 收合 {selected_year} 每日行程詳情", expanded=False):
            grouped = year_df.groupby(['月', '日'])
            for (m, d), group in grouped:
                st.markdown(f"#### 📍 {m}月{d}日")
                display_df = group[['完整時間', '地點', '去回程']].copy()
                display_df['完整時間'] = display_df['完整時間'].dt.strftime('%H:%M')
                display_df = display_df.rename(columns={'完整時間': '時間'})
                
                # [每日詳細行程表格] -> 🚨 CSS 會將背景變深色，文字清晰白色
                st.dataframe(display_df, use_container_width=True, key=f"df_{m}_{d}")
    
    # ==============================
    # 🚨 整合新增：📊 深度數據分析：去/回程每日節奏對比
    # ==============================
    st.markdown("---")
    st.subheader(f"📊 深度數據分析：{selected_year} 去/回程每日節奏對比")
    
    # 建立新的分析區塊，包含 Metric 和圖表
    analysis_col1, analysis_col2 = st.columns([1, 2]) # 比例 1:2
    
    with analysis_col1:
        st.write(" ") # 增加間距
        st.write(" ")
        st.write("**方向性平均數據：**")
        # 計算平均每日移動時數
        avg_go_hours = round(year_stat["去程時間"] / year_stat["去程天數"], 1) if year_stat["去程天數"] > 0 else 0
        avg_back_hours = round(year_stat["回程時間"] / year_stat["回程天數"], 1) if year_stat["回程天數"] > 0 else 0
        
        # 顯示指標卡 (st.metric 預設為白色)
        st.metric("去程 平均每日移動時數", f"{avg_go_hours} 小時/天")
        st.metric("回程 平均每日移動時數", f"{avg_back_hours} 小時/天")
        st.info("📊 分析解讀：此指標能告訴您哪個階段（去或回）走得比較趕。")

    with analysis_col2:
        # 使用 Plotly 繪製互動式分組長條圖
        # 視覺樣式：透明底、白色字體
        if not daily_stats.empty:
            # 建立圖表物件
            fig = px.bar(
                daily_stats, 
                x="day_number", # 橫軸：活動第幾天
                y="effective_hours", # 縱軸：移動小時數
                color="去回程", # 顏色：區分去和回
                barmode="group", # ✅ 分組模式：柱子並排對比
                labels={"day_number": "活動天數 (第X天)", "effective_hours": "移動時數 (小時)"},
                title=f"{selected_year} 去回程每日移動時數對比",
                color_discrete_map={'去': 'gold', '回': 'deepskyblue'} # 金色 and 藍色與主題搭配
            )
            
            # ✅ 強制設定圖表樣式為透明和白色
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', # 紙張背景透明
                plot_bgcolor='rgba(0,0,0,0)', # 繪圖區背景透明
                font_color='#ffffff', # 所有文字設為白色
                title_font_size=20, 
                legend_title_font_color='#ffffff', 
                legend_font_color='#ffffff'
            )
            
            # 設定座標軸樣式
            fig.update_xaxes(showgrid=False, zeroline=False, color='#ffffff')
            fig.update_yaxes(gridcolor='rgba(255, 255, 255, 0.1)', zeroline=False, color='#ffffff')
            
            # 在 Streamlit 中顯示 Plotly 圖表
            st.plotly_chart(fig, use_container_width=True, key="direction_pacing_chart")
        else:
            st.warning("無每日統計資料，無法生成圖表。")

    st.markdown("---")

    # ==============================
    # 2️⃣ 地點關鍵字搜尋
    # ==============================
    st.subheader("2️⃣ 地點查詢 (跨年份搜尋)")

    # [地點查詢文字輸入] -> 🚨 CSS 會將背景變深色，打字文字清晰白色
    keyword = st.text_input("輸入地點關鍵字（例如：白沙屯拱天宮）", placeholder="搜尋地點...", key="search_input")

    if keyword:
        results_df = []
        for year in available_years:
            # 🚨 升級：函式回傳三個參數
            df_for_search, _, _ = process_year_data(xls, year)
            match_df = df_for_search[df_for_search['地點'].astype(str).str.contains(keyword, na=False)]
            
            if not match_df.empty:
                match_df = match_df.copy()
                match_df['年份'] = year
                match_df = match_df[['年份', '完整時間', '地點', '去回程']]
                results_df.append(match_df)

        if results_df:
            final_result_df = pd.concat(results_df)
            final_result_df['完整時間'] = final_result_df['完整時間'].dt.strftime('%Y-%m-%d %H:%M')
            final_result_df = final_result_df.rename(columns={'完整時間': '日期時間'})
            final_result_df = final_result_df.sort_values(["日期時間"], ascending=[False])
            
            st.success(f"找到 {len(final_result_df)} 筆結果。")
            # [搜尋結果表格] -> 🚨 CSS 會將背景變深色，文字清晰白色
            st.dataframe(final_result_df, use_container_width=True, key="search_result_df")
        else:
            st.warning("沒有找到相關地點資訊。")

else:
    st.warning("無法載入資料，請確認遠端檔案連結。")
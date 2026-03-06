import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import base64
from datetime import timedelta
from streamlit_javascript import st_javascript # 🚨 必須安裝：pip install streamlit-javascript

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

# 全域基礎 CSS
basic_css = f"""
<style>
    /* 全域字體變白 */
    .stApp {{
        background: linear-gradient(
            135deg,
            #2b0000 0%,
            #4b0000 50%,
            #1a0000 100%
        );
        color: #ffffff !important;
    }}
    
    /* 強制所有文字變白 */
    .stApp label, .stApp p, .stApp span, .stApp div {{
        color: #ffffff !important;
    }}
    
    /* 標題變白 */
    h1, h2, h3, h4, h5, h6 {{
        color: #ffffff !important;
    }}

    /* 浮水印 */
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
    
    /* 分隔線 */
    hr {{
        border-color: rgba(255, 255, 255, 0.2) !important;
    }}
    
    /* Expander 透明化 */
    [data-testid="stExpander"] {{
        background-color: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }}
</style>
"""

# 載入基礎 CSS
st.markdown(basic_css, unsafe_allow_html=True)

# 顯示浮水印
if img_base64:
    st.markdown(
        f'<img src="data:image/png;base64,{img_base64}" class="watermark" width="700">',
        unsafe_allow_html=True
    )

st.title(f"{APP_TITLE}   {AUTHOR_TAG}")

# ==============================
# UI 介面優化 Part 2：JavaScript 穿透 Shadow DOM 強制透明
# ==============================
def inject_shadow_css():
    """使用 JavaScript 穿透 Shadow DOM，強制修改元件內部樣式為透明"""
    
    # CSS 程式碼塊 (用於注入)
    # 🚨 注意：st-dataframe-grid 預設樣式很難完全去除，我們強制設定其背景和網格。
    shadow_css_content = """
    <style>
        /* ----------------------------------------- */
        /* 1. 表格 (Dataframe) 內部透明化 */
        /* ----------------------------------------- */
        
        /* 強制所有層級背景透明 */
        :host {
            background-color: transparent !important;
        }
        
        div.st-dataframe-container,
        div.st-dataframe-grid,
        canvas {
            background-color: transparent !important;
            border: none !important;
        }
        
        /* 儲存格文字變白，邊框變淡 */
        div.st-dataframe-col-header,
        div.st-dataframe-cell,
        div.st-dataframe-row-header {
            background-color: transparent !important;
            color: #ffffff !important;
            border-color: rgba(255, 255, 255, 0.1) !important;
        }
        
        /* 表頭文字變白加粗 */
        div.st-dataframe-col-header {
            font-weight: bold !important;
        }
        
        /* 滑鼠懸停時的淡淡白色 */
        div.st-dataframe-cell:hover {
            background-color: rgba(255, 255, 255, 0.05) !important;
        }

        /* ----------------------------------------- */
        /* 2. 輸入元件 (Selectbox, Text Input) 內部透明化 */
        /* ----------------------------------------- */
        
        /* 輸入框容器透明化 */
        div[data-baseweb="select"],
        div[data-baseweb="base-input"] {
            background-color: transparent !important;
            border-color: rgba(255, 255, 255, 0.3) !important; /* 邊框淡白 */
            color: #ffffff !important;
        }
        
        /* 輸入的文字和下拉選單文字變白 */
        div[data-baseweb="select"] div,
        input {
            color: #ffffff !important;
        }
        
        /* 下拉箭頭變白 */
        svg {
            fill: #ffffff !important;
        }
        
        /* 🚨 關鍵：下拉選單的選項列表 (Popover) */
        /* 選項列表必須有一定背景色，否則文字會混在一起。
           這裡使用高透明度的黑色，兼顧透明感與可讀性。 */
        div[data-baseweb="popover"] ul {
            background-color: rgba(0, 0, 0, 0.8) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }
        
        /* 選項列表文字變白 */
        div[data-baseweb="popover"] ul li {
            color: #ffffff !important;
        }
        
        /* 滑鼠懸停在選項上時 */
        div[data-baseweb="popover"] ul li:hover {
            background-color: rgba(255, 255, 255, 0.1) !important;
        }
    </style>
    """
    
    # 執行 JavaScript，將 CSS 注入到所有具有 shadowRoot 的元件中
    js_code = f"""
    // 將 CSS 內容轉換為字串
    const css = `{shadow_css_content}`;
    
    // 尋找頁面上所有可能包含 Shadow DOM 的元件
    const components = document.querySelectorAll('st-dataframe, st-selectbox, st-text-input');
    
    components.forEach(comp => {{
        // 如果元件有 shadowRoot
        if (comp.shadowRoot) {{
            // 檢查是否已經注入過
            if (!comp.shadowRoot.querySelector('style.injected-transparent-css')) {{
                const styleSheet = document.createElement("style");
                styleSheet.type = "text/css";
                styleSheet.innerText = css.replace('<style>', '').replace('</style>', '');
                styleSheet.className = 'injected-transparent-css';
                // 將樣式表插入到 Shadow Root 的頭部，確保能覆蓋預設樣式
                comp.shadowRoot.prepend(styleSheet);
            }}
        }}
    }});
    
    // 傳回一個值以符合 st_javascript 的要求
    return "css_injected";
    """
    
    # 呼叫 st_javascript 執行
    st_javascript(js_code)

# ==============================
# 資料讀取與處理（與前一版相同）
# ==============================

@st.cache_resource
def fetch_raw_excel():
    with st.spinner("正在從雲端讀取資料..."):
        try:
            response = requests.get(FILE_URL)
            response.raise_for_status()
            excel_data = BytesIO(response.content)
            return pd.ExcelFile(excel_data, engine="openpyxl")
        except Exception as e:
            st.error(f"資料讀取失敗。錯誤資訊: {e}")
            return None

@st.cache_data
def process_year_data(_xls, year_sheet_name):
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

    df['time_diff_sec'] = df['完整時間'].diff().dt.total_seconds()
    valid_diff_mask = (df['time_diff_sec'] > 0) & (df['time_diff_sec'] <= 86400)
    df.loc[valid_diff_mask, 'effective_hours'] = df.loc[valid_diff_mask, 'time_diff_sec'] / 3600
    df['effective_hours'] = df['effective_hours'].fillna(0)

    go_df = df[df['去回程'] == '去']
    back_df = df[df['去回程'] == '回']

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

    return df, year_summary

# ==============================
# 主程式邏輯
# ==============================
xls = fetch_raw_excel()

if xls:
    # 🚨 關鍵：在載入元件之前呼叫 JS 注入，但 Streamlit 的特殊性使得其在元件載入後執行更有效。
    # 這裡我們將其放在xls讀取成功後，以確保 available_years 準備就緒。

    available_years = sorted(xls.sheet_names, reverse=True)

    # ==============================
    # 1️⃣ 年度統計與行程細節
    # ==============================
    st.subheader("1️⃣ 年度統計與行程細節")

    # [年份下拉選單] -> 🚨 JS 會強制透明
    selected_year = st.selectbox(
        "選擇要查看的年份",
        available_years,
        key="year_selector"
    )

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

        # 每日行程詳情
        with st.expander(f"點擊展開 / 收合 {selected_year} 每日行程詳情", expanded=False):
            grouped = year_df.groupby(['月', '日'])
            for (m, d), group in grouped:
                st.markdown(f"#### 📍 {m}月{d}日")
                display_df = group[['完整時間', '地點', '去回程']].copy()
                display_df['完整時間'] = display_df['完整時間'].dt.strftime('%H:%M')
                display_df = display_df.rename(columns={'完整時間': '時間'})
                
                # [每日詳細行程表格] -> 🚨 JS 會強制透明
                st.dataframe(display_df, use_container_width=True, key=f"df_{m}_{d}")
    
    st.markdown("---")

    # ==============================
    # 2️⃣ 地點關鍵字搜尋
    # ==============================
    st.subheader("2️⃣ 地點查詢 (跨年份搜尋)")

    # [地點查詢文字輸入] -> 🚨 JS 會強制透明
    keyword = st.text_input("輸入地點關鍵字（例如：白沙屯拱天宮）", placeholder="搜尋地點...", key="search_input")

    if keyword:
        results_df = []
        for year in available_years:
            df_for_search, _ = process_year_data(xls, year)
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
            # [搜尋結果表格] -> 🚨 JS 會強制透明
            st.dataframe(final_result_df, use_container_width=True, key="search_result_df")
        else:
            st.warning("沒有找到相關地點資訊。")

    # ==============================
    # 🚨 關鍵：最後執行 JS 注入
    # ==============================
    # 為了確保所有元件都已載入到 DOM 中，我們在程式碼最後面呼叫 JS 注入。
    inject_shadow_css()

else:
    st.warning("無法載入資料，請確認遠端檔案連結。")
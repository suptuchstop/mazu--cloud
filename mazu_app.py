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
APP_TITLE = "🔥白沙屯媽進香資料記錄🔥"
AUTHOR_TAG = " "
WATERMARK_IMAGE_PATH = "mazu_logo.png"

# ==============================
# UI 介面優化（浮水印、全透明元件、白色字體）
# ==============================
@st.cache_data
def get_base64_image(image_path):
    """讀取圖片並轉換為 base64 格式，用於 HTML/CSS"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        # 為了讓程式能跑，如果找不到圖，回傳空字串
        return ""

img_base64 = get_base64_image(WATERMARK_IMAGE_PATH)

# 強大且精細的 CSS 優化
css_style = f"""
<style>
    /* ----------------------------------------------------------- */
    /* 1. 全域設定：背景與字體 */
    /* ----------------------------------------------------------- */
    .stApp {{
        background: linear-gradient(
            135deg,
            #2b0000 0%,
            #4b0000 50%,
            #1a0000 100%
        );
        /* 🚨 關鍵：強制所有文字變白 */
        color: #ffffff !important;
    }}

    /* 強制所有標籤（Label）和普通文字變白 */
    .stApp label, .stApp p, .stApp span, .stApp div {{
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
        opacity: 0.20;
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
    /* 3. 表格（Dataframe）全透明優化 */
    /* ----------------------------------------------------------- */
    /* 隱藏表格元件的預設邊框和背景 */
    [data-testid="stDataFrame"] {{
        background-color: transparent !important;
        border: none !important;
    }}

    /* 針對表格內部的所有層級設為透明 */
    [data-testid="stDataFrame"] div,
    [data-testid="stDataFrame"] canvas,
    [data-testid="stDataFrame"] table,
    [data-testid="stDataFrame"] thead,
    [data-testid="stDataFrame"] tbody,
    [data-testid="stDataFrame"] tr,
    [data-testid="stDataFrame"] th,
    [data-testid="stDataFrame"] td {{
        background-color: transparent !important;
        color: #ffffff !important; /* 儲存格文字變白 */
        border-color: rgba(255, 255, 255, 0.1) !important; /* 淡淡的白色網格線 */
    }}

    /* 表格頭部（Header）文字變白並加粗 */
    [data-testid="stDataFrame"] thead th {{
        color: #ffffff !important;
        font-weight: bold !important;
    }}

    /* 滑鼠懸停（Hover）時的行背景色：淡淡的白色，增加互動感 */
    [data-testid="stDataFrame"] tbody tr:hover td {{
        background-color: rgba(255, 255, 255, 0.05) !important;
    }}

    /* ----------------------------------------------------------- */
    /* 4. 輸入元件（Selectbox, Text Input）全透明優化 */
    /* ----------------------------------------------------------- */
    /* 通用輸入框樣式（Selectbox 和 Text Input） */
    .stSelectbox div[data-baseweb="select"],
    .stTextInput div[data-baseweb="base-input"] {{
        background-color: transparent !important; /* 輸入框背景透明 */
        border-color: rgba(255, 255, 255, 0.3) !important; /* 邊框改為半透明白 */
        border-radius: 4px;
        color: #ffffff !important; /* 輸入的文字變白 */
    }}

    /* 下拉選單和輸入框內的文字顏色 */
    .stSelectbox div[data-baseweb="select"] div,
    .stTextInput div[data-baseweb="base-input"] input {{
        color: #ffffff !important;
    }}

    /* 下拉選單的箭頭顏色 */
    .stSelectbox svg {{
        fill: #ffffff !important;
    }}

    /* 🚨 關鍵：下拉選單的「選項列表」 */
    /* 如果選項列表也完全透明，文字會跟底圖混在一起。
       這裡使用高透明度的黑色，既有通透感，又能保證文字清晰。 */
    div[data-baseweb="popover"] ul {{
        background-color: rgba(0, 0, 0, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }}

    /* 選項列表中的文字變白 */
    div[data-baseweb="popover"] ul li {{
        color: #ffffff !important;
    }}

    /* 滑鼠懸停在選項上時的背景色 */
    div[data-baseweb="popover"] ul li:hover {{
        background-color: rgba(255, 255, 255, 0.1) !important;
    }}

    /* ----------------------------------------------------------- */
    /* 5. 其他 UI 微調 */
    /* ----------------------------------------------------------- */
    /* 標題和副標題文字變白 */
    h1, h2, h3, h4, h5, h6 {{
        color: #ffffff !important;
    }}
    
    /* 分隔線顏色 */
    hr {{
        border-color: rgba(255, 255, 255, 0.2) !important;
    }}

    /* Expander（折疊區塊）樣式調整 */
    .st-emotion-cache-p4m44u {{
        background-color: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }}
</style>
"""

# 載入 CSS
st.markdown(css_style, unsafe_allow_html=True)

# 顯示浮水印（如果有的話）
if img_base64:
    st.markdown(
        f'<img src="data:image/png;base64,{img_base64}" class="watermark" width="700">',
        unsafe_allow_html=True
    )

# 顯示標題
st.title(f"{APP_TITLE}   {AUTHOR_TAG}")

# ==============================
# 資料讀取與處理（與前一版相同）
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
    """處理單一月份的資料並計算統計資訊。"""
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
    available_years = sorted(xls.sheet_names, reverse=True)

    # ==============================
    # 1️⃣ 年度統計與詳細行程
    # ==============================
    st.subheader("1️⃣ 年度統計與詳細行程")

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

        # 每日詳細行程
        # 每日摘要 + 詳細行程
        with st.expander(f"點擊展開 / 收合 {selected_year} 每日行程摘要", expanded=False):

         grouped = year_df.groupby(['月', '日'])

         for (m, d), group in grouped:

            group = group.sort_values('完整時間')

            # ===== 起駕（當天最早）=====
            start_row = group.iloc[0]

            start_text = f"{selected_year}/{m}/{d} {start_row['完整時間'].strftime('%H:%M')} {start_row['地點']} 起駕"

            summary_parts = [start_text]

            # ===== 午休 =====
            lunch_row = group[group['地點'].astype(str).str.contains("午休", na=False)]

            if not lunch_row.empty:
                r = lunch_row.iloc[0]
                lunch_text = f"{selected_year}/{m}/{d} {r['完整時間'].strftime('%H:%M')} {r['地點']} 午休"
                summary_parts.append(lunch_text)

            # ===== 駐駕 =====
            stay_row = group[group['地點'].astype(str).str.contains("駐駕", na=False)]

            if not stay_row.empty:
                r = stay_row.iloc[0]
                stay_text = f"{selected_year}/{m}/{d} {r['完整時間'].strftime('%H:%M')} {r['地點']} 駐駕"
                summary_parts.append(stay_text)

            summary_line = f"{m}/{d}  |  " + " ; ".join(summary_parts)

            # ===== 點日期才顯示詳細行程 =====
            with st.expander(summary_line):

                display_df = group[['完整時間', '地點', '去回程']].copy()

                display_df['完整時間'] = display_df['完整時間'].dt.strftime('%H:%M')

                display_df = display_df.rename(columns={'完整時間': '時間'})

                st.dataframe(display_df, use_container_width=True)



                # 為了讓表格顯示更乾淨，將時間欄位轉換為字串
                display_df['完整時間'] = display_df['完整時間'].dt.strftime('%H:%M')
                display_df = display_df.rename(columns={'完整時間': '時間'})
                
                # 📢 表格會自動套用 CSS 成為全透明
                st.dataframe(display_df, use_container_width=True)
    
    st.markdown("---")

    # ==============================
    # 2️⃣ 地點關鍵字搜尋
    # ==============================
    st.subheader("2️⃣ 地點查詢 (跨年份搜尋)")

    # 📢 打字欄位會自動套用 CSS 成為透明
    keyword = st.text_input("輸入地點關鍵字（例如：拱天宮）", placeholder="搜尋地點...")

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
            # 📢 表格會自動套用 CSS 成為全透明
            st.dataframe(final_result_df, use_container_width=True)
        else:
            st.warning("沒有找到相關地點資訊。")

else:
    st.warning("無法載入資料，請確認遠端檔案連結。")
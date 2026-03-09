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
# UI 介面優化（CSS）
# ==============================
@st.cache_data
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return ""

img_base64 = get_base64_image(WATERMARK_IMAGE_PATH)

st.markdown(f"""
<style>
    .stApp {{
        background: linear-gradient(135deg, #2b0000 0%, #4b0000 50%, #1a0000 100%);
        color: #ffffff !important;
    }}
    .stApp label, .stApp p, .stApp span, .stApp div {{ color: #ffffff !important; }}
    .watermark {{
        position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
        opacity: 0.15; z-index: 0; pointer-events: none; filter: drop-shadow(0 0 100px gold);
    }}
    section[data-testid="stMain"] {{ position: relative; z-index: 1; }}
    .stSelectbox div[data-baseweb="select"], .stTextInput div[data-baseweb="base-input"] {{
        background-color: transparent !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
        color: #ffffff !important;
    }}
    div[data-baseweb="popover"] ul {{ background-color: rgba(0, 0, 0, 0.9) !important; }}
    h1, h2, h3, h4, h5, h6 {{ color: #ffffff !important; }}
    hr {{ border-color: rgba(255, 255, 255, 0.2) !important; }}
</style>
""", unsafe_allow_html=True)

if img_base64:
    st.markdown(f'<img src="data:image/png;base64,{img_base64}" class="watermark" width="700">', unsafe_allow_html=True)

st.title(f"{APP_TITLE} {AUTHOR_TAG}")

# ==============================
# 資料核心邏輯 (效能優化版)
# ==============================

@st.cache_data(show_spinner=False)
def load_all_data(url):
    """
    一次性讀取所有年份數據，避免搜尋時重複發送 Request。
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        xls = pd.ExcelFile(BytesIO(response.content), engine="openpyxl")
        
        all_years_data = {}
        full_list = []
        
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            df.columns = df.columns.str.strip()
            
            # 統一欄位處理
            df['去回程'] = df['去回程'].astype(str).str.strip().replace({'去程': '去', '回程': '回'})
            df['完整時間'] = pd.to_datetime(
                f"{sheet}-" + df['月'].astype(str) + '-' + df['日'].astype(str) + ' ' + df['時間'].astype(str),
                format='%Y-%m-%d %H:%M', errors='coerce'
            )
            df = df.dropna(subset=['完整時間']).sort_values('完整時間')
            
            # 計算時間差 (效能優化：一次性計算)
            df['time_diff_sec'] = df['完整時間'].diff().dt.total_seconds()
            valid_mask = (df['time_diff_sec'] > 0) & (df['time_diff_sec'] <= 86400)
            df['effective_hours'] = 0.0
            df.loc[valid_mask, 'effective_hours'] = df.loc[valid_mask, 'time_diff_sec'] / 3600
            
            all_years_data[sheet] = df
            
            # 準備用於跨年搜尋的總表
            search_part = df[['完整時間', '地點', '去回程']].copy()
            search_part['年份'] = sheet
            full_list.append(search_part)
            
        full_df = pd.concat(full_list) if full_list else pd.DataFrame()
        return all_years_data, full_df, sorted(xls.sheet_names, reverse=True)
    except Exception as e:
        st.error(f"資料讀取失敗: {e}")
        return None, None, []

# 執行載入
all_data, full_df, available_years = load_all_data(FILE_URL)

if all_data:
    # ==============================
    # 1️⃣ 年度統計與詳細行程
    # ==============================
    st.subheader("1️⃣ 年度統計與詳細行程")
    
    selected_year = st.selectbox("選擇年份", available_years, key="year_select")
    year_df = all_data[selected_year]
    
    # 計算統計量
    total_days = year_df[['月', '日']].drop_duplicates().shape[0]
    go_df = year_df[year_df['去回程'] == '去']
    back_df = year_df[year_df['去回程'] == '回']
    
    go_time = go_df['effective_hours'].sum()
    back_time = back_df['effective_hours'].sum()

    # 顯示統計數據
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("總天數", f"{total_days} 天")
    m_col2.metric("去程天數", f"{go_df[['月', '日']].drop_duplicates().shape[0]} 天")
    m_col3.metric("回程天數", f"{back_df[['月', '日']].drop_duplicates().shape[0]} 天")

    m_col4, m_col5, m_col6 = st.columns(3)
    m_col4.metric("總時數", f"{round(go_time + back_time, 1)} 小時")
    m_col5.metric("去程時數", f"{round(go_time, 1)} 小時")
    m_col6.metric("回程時數", f"{round(back_time, 1)} 小時")

    # 每日摘要展開
    with st.expander(f"{selected_year} 每日摘要與行程"):
        grouped = year_df.groupby(["月", "日"])
        for (m, d), g in grouped:
            g_sorted = g.sort_values("完整時間")
            start_node = g_sorted.iloc[0]
            
            # 建立摘要摘要線
            summary_parts = [f"{m}/{d} {start_node['時間']} {start_node['地點']} 起駕"]
            
            if "停駐駕" in g.columns:
                lunch = g[g["停駐駕"].astype(str).str.contains("午休", na=False)]
                if not lunch.empty:
                    summary_parts.append(f"{lunch.iloc[0]['時間']} 午休")
                
                stay = g[g["停駐駕"].astype(str).str.contains("駐駕", na=False)]
                if not stay.empty:
                    summary_parts.append(f"{stay.iloc[0]['時間']} 駐駕")
            
            label = " | ".join(summary_parts)
            
            with st.expander(label):
                st.dataframe(g_sorted[['時間', '地點', '去回程', '停駐駕'] if '停駐駕' in g.columns else ['時間', '地點', '去回程']], use_container_width=True)

    st.markdown("---")

    # ==============================
    # 2️⃣ 地點關鍵字搜尋 (高效搜尋)
    # ==============================
    st.subheader("2️⃣ 跨年份地點查詢")
    
    keyword = st.text_input("輸入地點關鍵字（例如：福安宮）", placeholder="搜尋歷年足跡...")

    if keyword and not full_df.empty:
        # 直接在預載好的總表中過濾
        search_res = full_df[full_df['地點'].astype(str).str.contains(keyword, na=False)].copy()
        
        if not search_res.empty:
            search_res['日期時間'] = search_res['完整時間'].dt.strftime('%Y-%m-%d %H:%M')
            search_res = search_res[['年份', '日期時間', '地點', '去回程']].sort_values('日期時間', ascending=False)
            
            st.success(f"在歷年紀錄中找到 {len(search_res)} 筆關於「{keyword}」的結果：")
            st.dataframe(search_res, use_container_width=True)
        else:
            st.warning(f"查無關於「{keyword}」的資料。")

else:
    st.error("系統初始化失敗，請檢查資料來源。")
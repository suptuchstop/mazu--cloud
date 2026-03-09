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
# 資料處理邏輯
# ==============================

@st.cache_data(show_spinner=False)
def load_all_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        xls = pd.ExcelFile(BytesIO(response.content), engine="openpyxl")
        
        all_years_data = {}
        full_list = []
        
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            df.columns = df.columns.str.strip()
            
            df['去回程'] = df['去回程'].astype(str).str.strip().replace({'去程': '去', '回程': '回'})
            df['完整時間'] = pd.to_datetime(
                f"{sheet}-" + df['月'].astype(str) + '-' + df['日'].astype(str) + ' ' + df['時間'].astype(str),
                format='%Y-%m-%d %H:%M', errors='coerce'
            )
            df = df.dropna(subset=['完整時間']).sort_values('完整時間')
            
            df['time_diff_sec'] = df['完整時間'].diff().dt.total_seconds()
            valid_mask = (df['time_diff_sec'] > 0) & (df['time_diff_sec'] <= 86400)
            df['effective_hours'] = 0.0
            df.loc[valid_mask, 'effective_hours'] = df.loc[valid_mask, 'time_diff_sec'] / 3600
            
            all_years_data[sheet] = df
            search_part = df[['完整時間', '地點', '去回程']].copy()
            search_part['年份'] = sheet
            full_list.append(search_part)
            
        full_df = pd.concat(full_list) if full_list else pd.DataFrame()
        return all_years_data, full_df, sorted(xls.sheet_names, reverse=True)
    except Exception as e:
        st.error(f"資料讀取失敗: {e}")
        return None, None, []

all_data, full_df, available_years = load_all_data(FILE_URL)

if all_data:
    # 1️⃣ 年度統計與詳細行程
    st.subheader("1️⃣ 年度統計與詳細行程")
    selected_year = st.selectbox("選擇年份", available_years, key="year_select")
    year_df = all_data[selected_year]
    
    # 統計計算
    total_days = year_df[['月', '日']].drop_duplicates().shape[0]
    go_df = year_df[year_df['去回程'] == '去']
    back_df = year_df[year_df['去回程'] == '回']
    
    col1, col2, col3 = st.columns(3)
    col1.metric("總天數", f"{total_days} 天")
    col2.metric("去程天數", f"{go_df[['月', '日']].drop_duplicates().shape[0]} 天")
    col3.metric("回程天數", f"{back_df[['月', '日']].drop_duplicates().shape[0]} 天")

    col4, col5, col6 = st.columns(3)
    col4.metric("總時數", f"{round(year_df['effective_hours'].sum(), 1)} 小時")
    col5.metric("去程時數", f"{round(go_df['effective_hours'].sum(), 1)} 小時")
    col6.metric("回程時數", f"{round(back_df['effective_hours'].sum(), 1)} 小時")

    # 每日摘要展開 (更新後的格式)
    with st.expander(f"{selected_year} 每日摘要與行程"):
        grouped = year_df.groupby(["月", "日"], sort=False)
        all_groups = list(grouped)
        
        for idx, ((m, d), g) in enumerate(all_groups):
            g_sorted = g.sort_values("完整時間")
            is_last_day = (idx == len(all_groups) - 1)
            
            # 1. 起駕資訊
            start_node = g_sorted.iloc[0]
            summary_parts = [f"{m}/{d}", f"{start_node['時間']} {start_node['地點']} 起駕"]
            
            if "停駐駕" in g.columns:
                # 2. 午休資訊
                lunch = g[g["停駐駕"].astype(str).str.contains("午休", na=False)]
                if not lunch.empty:
                    summary_parts.append(f"{lunch.iloc[0]['時間']} {lunch.iloc[0]['地點']} 午休")
                
                # 3. 駐駕 或 回宮 資訊
                stay = g[g["停駐駕"].astype(str).str.contains("駐駕", na=False)]
                if not stay.empty:
                    summary_parts.append(f"{stay.iloc[0]['時間']} {stay.iloc[0]['地點']} 駐駕")
                elif is_last_day:
                    # 最後一天找回宮
                    back_home = g[g["停駐駕"].astype(str).str.contains("回宮", na=False)]
                    if not back_home.empty:
                        node = back_home.iloc[0]
                        summary_parts.append(f"{node['時間']} {node['地點']}")
                        summary_parts.append("回宮")
            
            # 使用雙橫線分隔
            label = "  ||  ".join(summary_parts)
            
            with st.expander(label):
                cols_to_show = ['時間', '地點', '去回程']
                if '停駐駕' in g.columns: cols_to_show.append('停駐駕')
                st.dataframe(g_sorted[cols_to_show], use_container_width=True)

    st.markdown("---")

    # 2️⃣ 跨年份地點查詢
    st.subheader("2️⃣ 跨年份地點查詢")
    keyword = st.text_input("輸入地點關鍵字（例如：福安宮）", placeholder="搜尋歷年足跡...")

    if keyword and not full_df.empty:
        search_res = full_df[full_df['地點'].astype(str).str.contains(keyword, na=False)].copy()
        if not search_res.empty:
            search_res['日期時間'] = search_res['完整時間'].dt.strftime('%Y-%m-%d %H:%M')
            search_res = search_res[['年份', '日期時間', '地點', '去回程']].sort_values('日期時間', ascending=False)
            st.success(f"找到 {len(search_res)} 筆結果：")
            st.dataframe(search_res, use_container_width=True)
        else:
            st.warning(f"查無資料。")

else:
    st.error("系統初始化失敗，請檢查資料來源。")
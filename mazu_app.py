import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import base64
from datetime import time

# ==============================
# 應用程式配置
# ==============================
st.set_page_config(page_title="白沙屯媽進香資料記錄", layout="wide")

FILE_URL = "https://raw.githubusercontent.com/suptuchstop/mazu--cloud/main/BaishatunMAZU_Data.xlsx"
APP_TITLE = "🔥白沙屯媽進香資料記錄🔥"
WATERMARK_IMAGE_PATH = "mazu_logo.png"

# ==============================
# UI 介面優化
# ==============================
@st.cache_data
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except: return ""

img_base64 = get_base64_image(WATERMARK_IMAGE_PATH)

st.markdown(f"""
<style>
    .stApp {{
        background: #2b0000 !important;
        background-image: linear-gradient(135deg, #2b0000 0%, #4b0000 50%, #1a0000 100%) !important;
        background-attachment: fixed;
    }}
    .stApp p, .stApp span, .stApp label, .stApp div, .stApp h1, .stApp h2, .stApp h3 {{
        color: #ffffff !important;
    }}
    div[data-baseweb="select"] > div {{
        background-color: #3d0000 !important;
        color: #FFD700 !important;
        border: 1px solid rgba(255, 215, 0, 0.5) !important;
    }}
    ul[role="listbox"] {{ background-color: #3d0000 !important; }}
    ul[role="listbox"] li {{ color: #ffffff !important; }}
    [data-testid="stMetricValue"] {{ color: #FFD700 !important; font-weight: bold !important; }}
    [data-testid="stExpander"] {{
        background-color: #1a1a1a !important;
        border: 1px solid rgba(255, 215, 0, 0.3) !important;
        border-radius: 10px !important;
        margin-bottom: 12px !important;
        will-change: transform;
    }}
    [data-testid="stExpander"] details summary {{ background-color: #262626 !important; border-radius: 10px 10px 0 0; }}
    [data-testid="stExpander"] details summary p {{
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
        color: #ffffff !important;
        white-space: pre-wrap !important;
    }}
    .stDataFrame div {{ background-color: transparent !important; }}
    .watermark {{
        position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
        opacity: 0.12; z-index: 0; pointer-events: none;
    }}
</style>
""", unsafe_allow_html=True)

if img_base64:
    st.markdown(f'<img src="data:image/png;base64,{img_base64}" class="watermark" width="700">', unsafe_allow_html=True)

st.title(f"{APP_TITLE}")

# ==============================
# 資料載入與時數計算
# ==============================
@st.cache_data(show_spinner=False)
def load_all_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        xls = pd.ExcelFile(BytesIO(response.content), engine="openpyxl")
        all_data_dict, full_list = {}, []
        
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            df.columns = df.columns.str.strip()
            df['去回程'] = df['去回程'].astype(str).str.strip().replace({'去程': '去', '回程': '回'})
            
            # 建立完整時間並強制排序
            df['完整時間'] = pd.to_datetime(sheet + '-' + df['月'].astype(str) + '-' + df['日'].astype(str) + ' ' + df['時間'].astype(str), errors='coerce')
            df = df.dropna(subset=['完整時間']).sort_values('完整時間')
            
            # 計算有效時數
            df['time_diff_sec'] = df['完整時間'].diff().dt.total_seconds()
            df['effective_hours'] = df['time_diff_sec'].apply(lambda x: x/3600 if 0 < x <= 86400 else 0)
            
            all_data_dict[sheet] = df
            full_list.append(df[['完整時間', '地點', '去回程']].assign(年份=sheet))
        return all_data_dict, pd.concat(full_list), sorted(xls.sheet_names, reverse=True)
    except: return None, None, []

all_data, full_df, available_years = load_all_data(FILE_URL)

if all_data:
    selected_year = st.selectbox("請選擇年份", available_years)
    year_df = all_data[selected_year].copy()
    year_df['raw_date'] = year_df['完整時間'].dt.date

    # --- 1. 年度統計面板 ---
    go_df = year_df[year_df['去回程'] == '去']
    back_df = year_df[year_df['去回程'] == '回']
    col1, col2, col3 = st.columns(3)
    col1.metric("總天數", f"{year_df['raw_date'].nunique()} 天")
    col2.metric("去程天數", f"{go_df['raw_date'].nunique()} 天")
    col3.metric("回程天數", f"{back_df['raw_date'].nunique()} 天")
    col4, col5, col6 = st.columns(3)
    col4.metric("總時數", f"{round(year_df['effective_hours'].sum(), 1)} hr")
    col5.metric("去程時數", f"{round(go_df['effective_hours'].sum(), 1)} hr")
    col6.metric("回程時數", f"{round(back_df['effective_hours'].sum(), 1)} hr")

    st.markdown("---")
    # --- 2. 每日摘要與詳細行程 (表格完整顯示版) ---
    st.subheader(f"📅 {selected_year} 行程摘要")
    
    grouped = year_df.groupby("raw_date", sort=False)

    for idx, (g_date, g) in enumerate(grouped):
        # 1. 確保時間由早到晚排序
        g_sorted = g.sort_values("完整時間", ascending=True)
        
        # --- 摘要邏輯 ---
        line1 = g_date.strftime('%m/%d')
        
        # Line 2: 找當天第一個 "登轎" 或 "起駕"
        start_nodes = g_sorted[g_sorted['停駐駕'].astype(str).str.contains("起駕|登轎", na=False)]
        if not start_nodes.empty:
            s_node = start_nodes.iloc[0]
            line2 = f"{s_node['時間']}  {s_node['地點']}  {s_node['停駐駕']}"
        else:
            s_node = g_sorted.iloc[0]
            line2 = f"{s_node['時間']}  {s_node['地點']}  起駕"
        
        # Line 3: 找當天第一個 "午休"
        line3 = ""
        l_match = g_sorted[g_sorted['停駐駕'].astype(str).str.contains("午休", na=False)]
        if not l_match.empty:
            l_node = l_match.iloc[0]
            line3 = f"{l_node['時間']}  {l_node['地點']}  午休"
        
        # Line 4: 找當天最後一個關鍵終點
        line4 = ""
        end_found = False
        for kw in ["回宮", "朝天宮", "駐駕"]:
            e_match = g_sorted[g_sorted['停駐駕'].astype(str).str.contains(kw, na=False)]
            if not e_match.empty:
                e_node = e_match.iloc[-1]
                label = f"抵達{kw}" if kw == "朝天宮" else kw
                line4 = f"{e_node['時間']}  {e_node['地點']}  {label}"
                end_found = True
                break
        
        if not end_found and len(g_sorted) > 1:
            e_node = g_sorted.iloc[-1]
            if not (e_node['時間'] == s_node['時間'] and e_node['地點'] == s_node['地點']):
                line4 = f"{e_node['時間']}  {e_node['地點']}  駐駕"

        summary_lines = [line1, line2]
        if line3: summary_lines.append(line3)
        if line4: summary_lines.append(line4)
        label_text = "\n".join(summary_lines)
        
        # --- 詳細行程 (點開後) ---
        with st.expander(label_text):
            # 這裡就是關鍵：直接顯示 g_sorted 的全部，不選欄位，不濾資料
            # 這樣 Excel 裡面的 大甲、清水、伸港 等每一筆都會跑出來
            st.dataframe(g_sorted, use_container_width=True)


    # --- 3. 搜尋功能 ---
    st.markdown("---")
    st.subheader("🔍 地點查詢")
    search_key = st.text_input("搜尋關鍵字")
    if search_key and not full_df.empty:
        res = full_df[full_df['地點'].astype(str).str.contains(search_key, na=False)].copy()
        if not res.empty:
            res['日期時間'] = res['完整時間'].dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(res[['年份', '日期時間', '地點', '去回程']].sort_values('日期時間', ascending=False), use_container_width=True)
else:
    st.error("無法載入資料")
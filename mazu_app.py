import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import base64

# ==============================
# 應用程式配置
# ==============================
st.set_page_config(page_title="白沙屯媽進香資料記錄", layout="wide")

FILE_URL = "https://raw.githubusercontent.com/suptuchstop/mazu--cloud/main/BaishatunMAZU_Data.xlsx"
APP_TITLE = "🔥白沙屯媽進香資料記錄🔥"
WATERMARK_IMAGE_PATH = "mazu_logo.png"

# ==============================
# UI 介面優化 (解決下拉選單文字變白與滑動問題)
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
    /* 1. 全域背景 - 確保底色穩固 */
    .stApp {{
        background: #2b0000 !important;
        background-image: linear-gradient(135deg, #2b0000 0%, #4b0000 50%, #1a0000 100%) !important;
        background-attachment: fixed;
    }}

    /* 2. 文字顏色強制白色 */
    .stApp p, .stApp span, .stApp label, .stApp div, .stApp h1, .stApp h2, .stApp h3 {{
        color: #ffffff !important;
    }}

    /* 3. 解決下拉選單 (selectbox) 文字看不到的問題 */
    /* 強制選取框內部的背景為深色，文字為黃金色 */
    div[data-baseweb="select"] > div {{
        background-color: #3d0000 !important;
        color: #FFD700 !important;
        border: 1px solid rgba(255, 215, 0, 0.5) !important;
    }}
    
    /* 下拉選單展開後的選項清單 */
    ul[role="listbox"] {{
        background-color: #3d0000 !important;
    }}
    
    ul[role="listbox"] li {{
        color: #ffffff !important;
    }}

    /* 4. 數據高亮 (金色) */
    [data-testid="stMetricValue"] {{
        color: #FFD700 !important;
        font-weight: bold !important;
    }}

    /* 5. 徹底解決滑動變白問題：強制使用實心背景 */
    [data-testid="stExpander"] {{
        background-color: #1a1a1a !important;
        border: 1px solid rgba(255, 215, 0, 0.3) !important;
        border-radius: 10px !important;
        margin-bottom: 12px !important;
        will-change: transform;
    }}
    
    [data-testid="stExpander"] details summary {{
        background-color: #262626 !important;
        border-radius: 10px 10px 0 0;
    }}

    [data-testid="stExpander"] details summary p {{
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
        color: #ffffff !important;
        white-space: pre-wrap !important;
    }}

    /* 6. 修正 Dataframe 顯示 */
    .stDataFrame div {{
        background-color: transparent !important;
    }}
    
    .watermark {{
        position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
        opacity: 0.12; z-index: 0; pointer-events: none;
    }}

    /* 手機版字體 */
    @media (max-width: 600px) {{
        [data-testid="stExpander"] details summary p {{
            font-size: 12px !important;
        }}
    }}
</style>
""", unsafe_allow_html=True)

if img_base64:
    st.markdown(f'<img src="data:image/png;base64,{img_base64}" class="watermark" width="700">', unsafe_allow_html=True)

st.title(f"{APP_TITLE}")

# ==============================
# 資料核心邏輯
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
            df['完整時間'] = pd.to_datetime(f"{sheet}-"+df['月'].astype(str)+'-'+df['日'].astype(str)+' '+df['時間'].astype(str), format='%Y-%m-%d %H:%M', errors='coerce')
            df = df.dropna(subset=['完整時間']).sort_values('完整時間')
            
            df['time_diff_sec'] = df['完整時間'].diff().dt.total_seconds()
            df['effective_hours'] = df['time_diff_sec'].apply(lambda x: x/3600 if 0 < x <= 86400 else 0)
            
            all_data_dict[sheet] = df
            full_list.append(df[['完整時間', '地點', '去回程']].assign(年份=sheet))
        return all_data_dict, pd.concat(full_list), sorted(xls.sheet_names, reverse=True)
    except: return None, None, []

all_data, full_df, available_years = load_all_data(FILE_URL)

if all_data:
    # --- 1. 年度統計面板 ---
    # 這裡就是你提到的下拉選單位置
    selected_year = st.selectbox("請選擇年份", available_years)
    year_df = all_data[selected_year]
    
    go_df = year_df[year_df['去回程'] == '去']
    back_df = year_df[year_df['去回程'] == '回']

    col1, col2, col3 = st.columns(3)
    col1.metric("總天數", f"{year_df[['月', '日']].drop_duplicates().shape[0]} 天")
    col2.metric("去程天數", f"{go_df[['月', '日']].drop_duplicates().shape[0]} 天")
    col3.metric("回程天數", f"{back_df[['月', '日']].drop_duplicates().shape[0]} 天")

    col4, col5, col6 = st.columns(3)
    col4.metric("總時數", f"{round(year_df['effective_hours'].sum(), 1)} hr")
    col5.metric("去程時數", f"{round(go_df['effective_hours'].sum(), 1)} hr")
    col6.metric("回程時數", f"{round(back_df['effective_hours'].sum(), 1)} hr")

    st.markdown("---")

    # --- 2. 每日摘要 (修正滑動問題與重複) ---
    st.subheader(f"📅 {selected_year} 每日行程摘要與詳細行程")
    grouped = year_df.groupby("group_date", sort=False)

    for idx, (g_date, g) in enumerate(grouped):
        g_sorted = g.sort_values("完整時間")
    
        # Line 1: 日期顯示 (支援併日日期範圍)
        unique_dates = g_sorted['完整時間'].dt.strftime('%m/%d').unique()
        line1 = " - ".join(unique_dates) if len(unique_dates) > 1 else unique_dates[0]
    
        # Line 2: 真正的第一筆 (absolute_first_node 或 組內首筆)
        first_node = absolute_first_node if (idx == 0) else g_sorted.iloc[0]
        status = first_node['停駐駕'] if (pd.notna(first_node.get('停駐駕')) and str(first_node['停駐駕']).strip() != "") else "起駕"
        line2 = f"{first_node['時間']}  {first_node['地點']}  {status}"
    
        # Line 3: 午休 (略過邏輯不變)
        line3 = ""
        # ... (午休抓取邏輯)
    
        # Line 4: 終點/駐駕 (增加過濾邏輯)
        line4 = ""
        if len(g_sorted) > 1:  # 關鍵：只有當這組資料超過一筆時，才去抓終點
            found = False
            for kw in ["回宮", "朝天宮", "駐駕"]:
                m = g[g['停駐駕'].astype(str).str.contains(kw, na=False)]
                if not m.empty:
                    node = m.iloc[-1]
                    label = f"抵達{kw}" if kw == "朝天宮" else kw
                    line4 = f"{node['時間']}  {node['地點']}  {label}"
                    found = True
                    break
            if not found:
                last = g_sorted.iloc[-1]
                line4 = f"{last['時間']}  {last['地點']}"

        # 組合摘要：建立一個 set 來過濾內容完全一樣的行
        display_lines = [line1, line2]
        if line3: display_lines.append(line3)
        # 如果 line4 存在，且它的「時間+地點」跟 line2 不同，才加入
        if line4:
            # 簡單檢查：如果時間地點都一樣，就不重複顯示
            if not (first_node['時間'] in line4 and first_node['地點'] in line4):
                display_lines.append(line4)
            
        label_text = "\n".join(display_lines)
    
        with st.expander(label_text):
             st.dataframe(g_sorted[['月', '日', '時間', '地點', '去回程', '停駐駕']], use_container_width=True)



    # --- 3. 搜尋 ---
    st.markdown("---")
    st.subheader("🔍 跨年份地點查詢")
    search_key = st.text_input("搜尋地點關鍵字")
    if search_key and not full_df.empty:
        res = full_df[full_df['地點'].astype(str).str.contains(search_key, na=False)].copy()
        if not res.empty:
            res['日期時間'] = res['完整時間'].dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(res[['年份', '日期時間', '地點', '去回程']].sort_values('日期時間', ascending=False), use_container_width=True)
else:
    st.error("無法載入資料")
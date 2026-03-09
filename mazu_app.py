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
# UI 樣式修正
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
    div[data-baseweb="select"] {{ background-color: #3d0000 !important; border-radius: 8px; }}
    div[data-baseweb="select"] > div {{ background-color: transparent !important; color: #FFD700 !important; }}
    div[data-baseweb="popover"] ul {{ background-color: #3d0000 !important; }}
    div[data-baseweb="popover"] li {{ color: #ffffff !important; }}

    [data-testid="stMetricValue"] {{ color: #FFD700 !important; font-weight: bold !important; }}

    [data-testid="stExpander"] {{
        background-color: #1a1a1a !important;
        border: 1px solid rgba(255, 215, 0, 0.3) !important;
        border-radius: 10px !important;
        margin-bottom: 12px !important;
    }}
    [data-testid="stExpander"] details summary {{ background-color: #262626 !important; border-radius: 10px 10px 0 0; }}
</style>
""", unsafe_allow_html=True)

# ==============================
# 資料核心邏輯 (精準鎖定首筆)
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
            df = df.dropna(subset=['完整時間']).sort_values('完整時間').reset_index(drop=True)
            
            df['time_diff_sec'] = df['完整時間'].diff().dt.total_seconds()
            df['effective_hours'] = df['time_diff_sec'].apply(lambda x: x/3600 if 0 < x <= 86400 else 0)
            
            all_data_dict[sheet] = df
            full_list.append(df[['完整時間', '地點', '去回程']].assign(年份=sheet))
        return all_data_dict, pd.concat(full_list), sorted(xls.sheet_names, reverse=True)
    except: return None, None, []

all_data, full_df, available_years = load_all_data(FILE_URL)

if all_data:
    selected_year = st.selectbox("選擇年份", available_years)
    year_df = all_data[selected_year].copy()

    # 記住這一年真正的第一筆資料 (不論時間)
    absolute_first_node = year_df.iloc[0]

    # 併日判斷邏輯
    year_df['group_date'] = year_df['完整時間'].dt.date
    if absolute_first_node['完整時間'].time() >= time(23, 15):
        actual_days = year_df['group_date'].unique()
        if len(actual_days) > 1:
            year_df.loc[year_df['group_date'] == actual_days[0], 'group_date'] = actual_days[1]

    # 統計
    t_days = year_df['group_date'].nunique()
    go_df = year_df[year_df['去回程'] == '去']
    back_df = year_df[year_df['去回程'] == '回']

    c1, c2, c3 = st.columns(3)
    c1.metric("總天數", f"{t_days} 天")
    c2.metric("去程天數", f"{go_df['group_date'].nunique()} 天")
    c3.metric("回程天數", f"{back_df['group_date'].nunique()} 天")
    
    st.markdown("---")

    # --- 每日摘要渲染 ---
    grouped = year_df.groupby("group_date", sort=False)
    for idx, (g_date, g) in enumerate(grouped):
        g_sorted = g.sort_values("完整時間")
        
        # Line 1: 日期
        dates = g_sorted['完整時間'].dt.strftime('%m/%d').unique()
        line1 = " - ".join(dates) if len(dates) > 1 else dates[0]
        
        # Line 2: 修正邏輯 - 如果這是第一組摘要，強制使用 absolute_first_node
        if idx == 0:
            first_node = absolute_first_node
        else:
            first_node = g_sorted.iloc[0]
            
        status = first_node['停駐駕'] if (pd.notna(first_node.get('停駐駕')) and str(first_node['停駐駕']).strip() != "") else "起駕"
        line2 = f"{first_node['時間']}  {first_node['地點']}  {status}"
        
        # Line 3: 午休
        line3 = ""
        if '停駐駕' in g.columns:
            l_match = g[g['停駐駕'].astype(str).str.contains("午休", na=False)]
            if not l_match.empty:
                t = l_match.iloc[0]
                line3 = f"{t['時間']}  {t['地點']}  午休"
        
        # Line 4: 駐駕
        line4 = ""
        if '停駐駕' in g.columns:
            found = False
            for kw in ["回宮", "朝天宮", "駐駕"]:
                m = g[g['停駐駕'].astype(str).str.contains(kw, na=False)]
                if not m.empty:
                    node = m.iloc[-1]
                    label = f"抵達{kw}" if kw == "朝天宮" else kw
                    line4 = f"{node['時間']}  {node['地點']}  {label}"
                    found = True
                    break
            if not found and len(g_sorted) > 1:
                last = g_sorted.iloc[-1]
                line4 = f"{last['時間']}  {last['地點']}"

        summary_list = [line1, line2]
        if line3: summary_list.append(line3)
        if line4 and line4 != line2: summary_list.append(line4)
            
        label_text = "\n".join(summary_list)
        
        with st.expander(label_text):
            st.dataframe(g_sorted[['月', '日', '時間', '地點', '去回程', '停駐駕']], use_container_width=True)

    # 跨年份搜尋
    st.markdown("---")
    st.subheader("🔍 跨年份地點查詢")
    sk = st.text_input("搜尋地點")
    if sk and not full_df.empty:
        res = full_df[full_df['地點'].astype(str).str.contains(sk, na=False)].copy()
        if not res.empty:
            res['日期時間'] = res['完整時間'].dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(res[['年份', '日期時間', '地點', '去回程']].sort_values('日期時間', ascending=False), use_container_width=True)
else:
    st.error("載入失敗")
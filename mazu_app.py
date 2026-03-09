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
    [data-testid="stExpander"] {{
        background-color: #1a1a1a !important;
        border: 1px solid rgba(255, 215, 0, 0.3) !important;
        border-radius: 10px !important;
        margin-bottom: 12px !important;
    }}
</style>
""", unsafe_allow_html=True)

# ==============================
# 資料載入
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

    # 直接使用原始日期進行分組 (不處理併日)
    year_df['raw_date'] = year_df['完整時間'].dt.date

    # 統計
    t_days = year_df['raw_date'].nunique()
    c1, c2, c3 = st.columns(3)
    c1.metric("總天數", f"{t_days} 天")
    c4, c5, c6 = st.columns(3)
    c4.metric("總時數", f"{round(year_df['effective_hours'].sum(), 1)} hr")

    st.markdown("---")

    # --- 2. 每日摘要與詳細行程 ---
    st.subheader(f"📅 {selected_year} 行程摘要")
    
    # 按照日期分組
    grouped = year_df.groupby("raw_date", sort=False)

    for idx, (g_date, g) in enumerate(grouped):
        g_sorted = g.sort_values("完整時間")
        
        # Line 1: 日期
        line1 = g_date.strftime('%m/%d')
        
        # Line 2: 起點
        first_node = g_sorted.iloc[0]
        status = first_node['停駐駕'] if (pd.notna(first_node.get('停駐駕')) and str(first_node['停駐駕']).strip() != "") else "起駕"
        line2 = f"{first_node['時間']}  {first_node['地點']}  {status}"
        
        # Line 3: 午休
        line3 = ""
        if '停駐駕' in g.columns:
            l_match = g[g['停駐駕'].astype(str).str.contains("午休", na=False)]
            if not l_match.empty:
                target = l_match.iloc[0]
                line3 = f"{target['時間']}  {target['地點']}  午休"
        
        # Line 4: 終點 (過濾單筆重複)
        line4 = ""
        if len(g_sorted) > 1:
            found_end = False
            for kw in ["回宮", "朝天宮", "駐駕"]:
                t_match = g[g['停駐駕'].astype(str).str.contains(kw, na=False)]
                if not t_match.empty:
                    t_node = t_match.iloc[-1]
                    label = f"抵達{kw}" if kw == "朝天宮" else kw
                    line4 = f"{t_node['時間']}  {t_node['地點']}  {label}"
                    found_end = True
                    break
            if not found_end:
                last_node = g_sorted.iloc[-1]
                line4 = f"{last_node['時間']}  {last_node['地點']}"

        # 組合摘要文字
        summary_lines = [line1, line2]
        if line3: summary_lines.append(line3)
        # 最終重複檢查：如果 line4 的核心內容 (時間+地點) 已經在 line2 出現，就不顯示
        if line4:
            if not (first_node['時間'] in line4 and first_node['地點'] in line4):
                summary_lines.append(line4)
            
        label_text = "\n".join(summary_lines)
        
        # 展開後顯示該日所有行程資料
        with st.expander(label_text):
            cols = ['時間', '地點', '去回程']
            if '停駐駕' in g.columns:
                cols.append('停駐駕')
            # 顯示該分組 (g_sorted) 內的所有筆數
            st.dataframe(g_sorted[cols], use_container_width=True)

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
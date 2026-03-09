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
    /* 下拉選單樣式修正 */
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
    [data-testid="stExpander"] details summary p {{
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
        color: #ffffff !important;
        white-space: pre-wrap !important;
    }}
    .watermark {{ position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); opacity: 0.12; z-index: 0; pointer-events: none; }}
</style>
""", unsafe_allow_html=True)

if img_base64:
    st.markdown(f'<img src="data:image/png;base64,{img_base64}" class="watermark" width="700">', unsafe_allow_html=True)

st.title(f"{APP_TITLE}")

# ==============================
# 資料核心邏輯 (併日邏輯)
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
    selected_year = st.selectbox("選擇年份", available_years)
    year_df = all_data[selected_year]

    # --- 併日處理邏輯 ---
    # 建立一個標記，用來決定哪些紀錄屬於哪一組摘要
    year_df['group_date'] = year_df['完整時間'].dt.date
    first_record_time = year_df.iloc[0]['完整時間']
    
    # 判斷第一天起駕是否晚於 23:15
    merge_first_day = False
    if first_record_time.time() >= time(23, 15):
        merge_first_day = True
        # 將第一天的 group_date 改為第二天的日期
        first_day = year_df['group_date'].unique()[0]
        second_day = year_df['group_date'].unique()[1] if len(year_df['group_date'].unique()) > 1 else first_day
        year_df.loc[year_df['group_date'] == first_day, 'group_date'] = second_day

    # 重新計算天數 (以 group_date 為準)
    t_days = year_df['group_date'].nunique()
    go_df = year_df[year_df['去回程'] == '去']
    back_df = year_df[year_df['去回程'] == '回']

    # 顯示面板
    c1, c2, c3 = st.columns(3)
    c1.metric("總天數", f"{t_days} 天")
    c2.metric("去程天數", f"{go_df['group_date'].nunique()} 天")
    c3.metric("回程天數", f"{back_df['group_date'].nunique()} 天")
    
    c4, c5, c6 = st.columns(3)
    c4.metric("總時數", f"{round(year_df['effective_hours'].sum(), 1)} hr")
    c5.metric("去程時數", f"{round(go_df['effective_hours'].sum(), 1)} hr")
    c6.metric("回程時數", f"{round(back_df['effective_hours'].sum(), 1)} hr")

    st.markdown("---")

    # --- 2. 每日摘要 (含併日顯示) ---
    st.subheader(f"📅 {selected_year} 每日摘要與行程")
    
    # 按合併後的日期分組
    grouped = year_df.groupby("group_date", sort=False)
    
    for idx, (g_date, g) in enumerate(grouped):
        g_sorted = g.sort_values("完整時間")
        
        # Line 1: 日期顯示 (如果是合併的，顯示 05/01-05/02)
        unique_actual_days = g_sorted['完整時間'].dt.strftime('%m/%d').unique()
        line1 = " - ".join(unique_actual_days) if len(unique_actual_days) > 1 else unique_actual_days[0]
        
        # Line 2: 起駕 (該組第一筆)
        first_node = g_sorted.iloc[0]
        line2 = f"{first_node['時間']}  {first_node['地點']}  起駕"
        
        # Line 3: 午休 (抓該組內含午休的紀錄)
        line3 = ""
        if '停駐駕' in g.columns:
            l_match = g[g['停駐駕'].astype(str).str.contains("午休", na=False)]
            if not l_match.empty:
                target = l_match.iloc[0]
                line3 = f"{target['時間']}  {target['地點']}  午休"
        
        # Line 4: 終點
        line4 = ""
        if '停駐駕' in g.columns:
            found_end = False
            for kw in ["回宮", "朝天宮", "駐駕"]:
                t_match = g[g['停駐駕'].astype(str).str.contains(kw, na=False)]
                if not t_match.empty:
                    t_node = t_match.iloc[-1]
                    status = f"抵達{kw}" if kw == "朝天宮" else kw
                    line4 = f"{t_node['時間']}  {t_node['地點']}  {status}"
                    found_end = True
                    break
            if not found_end:
                last_node = g_sorted.iloc[-1]
                line4 = f"{last_node['時間']}  {last_node['地點']}"

        summary_list = [line1, line2]
        if line3: summary_list.append(line3)
        if line4 and line4 != line2: summary_list.append(line4)
            
        label_text = "\n".join(summary_list)
        
        with st.expander(label_text):
            # 表格內增加「月」、「日」欄位以便區分合併後的紀錄
            cols = ['月', '日', '時間', '地點', '去回程']
            if '停駐駕' in g.columns: cols.append('停駐駕')
            st.dataframe(g_sorted[cols], use_container_width=True)

    # --- 3. 搜尋 ---
    st.markdown("---")
    st.subheader("🔍 跨年份地點查詢")
    search_key = st.text_input("搜尋地點或宮廟名稱")
    if search_key and not full_df.empty:
        res = full_df[full_df['地點'].astype(str).str.contains(search_key, na=False)].copy()
        if not res.empty:
            res['日期時間'] = res['完整時間'].dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(res[['年份', '日期時間', '地點', '去回程']].sort_values('日期時間', ascending=False), use_container_width=True)
else:
    st.error("無法載入資料")
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
# UI 介面優化 (徹底解決手機端顯示問題)
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
    /* 1. 全域背景與文字基礎 */
    .stApp {{
        background: linear-gradient(135deg, #2b0000 0%, #4b0000 50%, #1a0000 100%) !important;
        color: #ffffff !important;
    }}

    /* 2. 強制文字顏色（包含選擇框與標籤） */
    .stApp p, .stApp span, .stApp label, .stApp div, .stApp h1, .stApp h2, .stApp h3 {{
        color: #ffffff !important;
    }}

    /* 3. 重點指標高亮 (金色) */
    [data-testid="stMetricValue"] {{
        color: #FFD700 !important;
        font-weight: bold !important;
    }}

    /* 4. 解決手機版展開後變白色的問題 (CSS 強制覆蓋) */
    /* 針對 st.expander 的所有狀態強制設定背景色 */
    [data-testid="stExpander"] {{
        background-color: rgba(30, 30, 30, 0.7) !important;
        border: 1px solid rgba(255, 215, 0, 0.2) !important;
        border-radius: 8px !important;
    }}
    
    [data-testid="stExpander"] details summary {{
        background-color: rgba(20, 0, 0, 0.5) !important;
        color: #ffffff !important;
    }}

    [data-testid="stExpander"] p {{
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
        font-size: 14px !important;
        line-height: 1.5 !important;
        color: #ffffff !important;
        white-space: pre-wrap !important; /* 手機版自動換行防止截斷 */
    }}

    /* 5. 修正 Dataframe 防止白色遮擋 */
    .stDataFrame div {{
        background-color: transparent !important;
    }}
    
    .watermark {{
        position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
        opacity: 0.12; z-index: 0; pointer-events: none;
    }}

    /* 手機版字體微調 */
    @media (max-width: 600px) {{
        [data-testid="stExpander"] p {{
            font-size: 12px !important;
        }}
    }}
</style>
""", unsafe_allow_html=True)

if img_base64:
    st.markdown(f'<img src="data:image/png;base64,{img_base64}" class="watermark" width="700">', unsafe_allow_html=True)

st.title(f"{APP_TITLE}")

# ==============================
# 資料核心邏輯 (優化搜尋條件)
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
    # 統計面板
    selected_year = st.selectbox("選擇年份", available_years)
    year_df = all_data[selected_year]
    
    go_df = year_df[year_df['去回程'] == '去']
    back_df = year_df[year_df['去回程'] == '回']

    c1, c2, c3 = st.columns(3)
    c1.metric("總天數", f"{year_df[['月', '日']].drop_duplicates().shape[0]} 天")
    c2.metric("去程天數", f"{go_df[['月', '日']].drop_duplicates().shape[0]} 天")
    c3.metric("回程天數", f"{back_df[['月', '日']].drop_duplicates().shape[0]} 天")

    c4, c5, c6 = st.columns(3)
    c4.metric("總時數", f"{round(year_df['effective_hours'].sum(), 1)} hr")
    c5.metric("去程時數", f"{round(go_df['effective_hours'].sum(), 1)} hr")
    c6.metric("回程時數", f"{round(back_df['effective_hours'].sum(), 1)} hr")

    st.markdown("---")

    # --- 每日摘要核心邏輯 ---
    with st.expander(f"📅 {selected_year} 每日摘要與行程記錄"):
        grouped = year_df.groupby(["月", "日"], sort=False)
        for idx, ((m, d), g) in enumerate(grouped):
            g_sorted = g.sort_values("完整時間")
            
            # 1. 起駕
            first = g_sorted.iloc[0]
            p2 = f"{first['時間']} {first['地點']} 起駕"
            
            # 2. 午休 (優化關鍵字判斷)
            p3 = " " * 15
            if '停駐駕' in g.columns:
                # 模糊搜尋包含「午休」字樣的列
                l_match = g[g['停駐駕'].astype(str).str.contains("午休", na=False)]
                if not l_match.empty:
                    target = l_match.iloc[0]
                    p3 = f"{target['時間']} {target['地點']} 午休"
            
            # 3. 終點 (駐駕/朝天宮/回宮)
            p4 = ""
            if '停駐駕' in g.columns:
                found_p4 = False
                for kw in ["回宮", "朝天宮", "駐駕"]:
                    target_match = g[g['停駐駕'].astype(str).str.contains(kw, na=False)]
                    if not target_match.empty:
                        t_node = target_match.iloc[-1]
                        status = f"抵達{kw}" if kw == "朝天宮" else kw
                        p4 = f"{t_node['時間']} {t_node['地點']} {status}"
                        found_p4 = True
                        break
                if not found_p4:
                    last_node = g_sorted.iloc[-1]
                    p4 = f"{last_node['時間']} {last_node['地點']}"

            # 組合標籤
            label = f"{m:02d}/{d:02d} || {p2} || {p3} || {p4}"
            
            with st.expander(label):
                cols = ['時間', '地點', '去回程']
                if '停駐駕' in g.columns: cols.append('停駐駕')
                st.dataframe(g_sorted[cols], use_container_width=True)

    # 搜尋部分保持不變
    st.markdown("---")
    st.subheader("🔍 跨年份地點查詢")
    keyword = st.text_input("搜尋關鍵字")
    if keyword and not full_df.empty:
        res = full_df[full_df['地點'].astype(str).str.contains(keyword, na=False)].copy()
        if not res.empty:
            res['日期時間'] = res['完整時間'].dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(res[['年份', '日期時間', '地點', '去回程']].sort_values('日期時間', ascending=False), use_container_width=True)
else:
    st.error("資料載入失敗")
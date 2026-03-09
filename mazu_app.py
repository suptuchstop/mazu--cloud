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
# UI 介面優化（徹底解決手機白色遮擋與字體截斷）
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
    /* 1. 全域背景與基礎文字 */
    .stApp {{
        background: linear-gradient(135deg, #2b0000 0%, #4b0000 50%, #1a0000 100%) !important;
        color: #ffffff !important;
    }}

    /* 2. 強制所有元件文字顏色 */
    .stApp p, .stApp span, .stApp label, .stApp div, .stApp h1, .stApp h2, .stApp h3 {{
        color: #ffffff !important;
    }}

    /* 3. Metric 數據優化 (金色) */
    [data-testid="stMetricValue"] {{
        color: #FFD700 !important;
        font-weight: bold !important;
    }}

    /* 4. Expander 標題修正：解決手機版白色遮擋問題 */
    /* 這裡使用透明度較低的深色背景，確保白色字體在任何模式下都清晰 */
    .st-emotion-cache-p4m44u {{
        background-color: rgba(30, 30, 30, 0.8) !important; 
        border: 1px solid rgba(255, 215, 0, 0.3) !important;
        border-radius: 8px !important;
        margin-bottom: 5px !important;
    }}
    
    .st-emotion-cache-p4m44u p {{
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
        font-size: 13px !important;
        white-space: pre !important;
        color: #ffffff !important;
    }}

    /* 5. 修正 Dataframe 背景顏色防止過白 */
    .stDataFrame div {{
        background-color: rgba(0, 0, 0, 0.2) !important;
    }}
    
    /* 6. 浮水印 */
    .watermark {{
        position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
        opacity: 0.12; z-index: 0; pointer-events: none;
    }}

    /* 7. 針對手機小螢幕隱藏部分空格或調整比例 */
    @media (max-width: 600px) {{
        .st-emotion-cache-p4m44u p {{
            font-size: 11px !important;
            letter-spacing: -0.5px;
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
        all_years_data, full_list = {}, []
        
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            df.columns = df.columns.str.strip()
            df['去回程'] = df['去回程'].astype(str).str.strip().replace({'去程': '去', '回程': '回'})
            df['完整時間'] = pd.to_datetime(f"{sheet}-"+df['月'].astype(str)+'-'+df['日'].astype(str)+' '+df['時間'].astype(str), format='%Y-%m-%d %H:%M', errors='coerce')
            df = df.dropna(subset=['完整時間']).sort_values('完整時間')
            df['time_diff_sec'] = df['完整時間'].diff().dt.total_seconds()
            df['effective_hours'] = df['time_diff_sec'].apply(lambda x: x/3600 if 0 < x <= 86400 else 0)
            all_years_data[sheet] = df
            s_part = df[['完整時間', '地點', '去回程']].copy()
            s_part['年份'] = sheet
            full_list.append(s_part)
        return all_years_data, pd.concat(full_list), sorted(xls.sheet_names, reverse=True)
    except: return None, None, []

all_data, full_df, available_years = load_all_data(FILE_URL)

if all_data:
    # --- 1. 年度統計 ---
    selected_year = st.selectbox("選擇年份", available_years)
    year_df = all_data[selected_year]
    
    t_days = year_df[['月', '日']].drop_duplicates().shape[0]
    go_df = year_df[year_df['去回程'] == '去']
    back_df = year_df[year_df['去回程'] == '回']

    c1, c2, c3 = st.columns(3)
    c1.metric("總天數", f"{t_days} 天")
    c2.metric("去程天數", f"{go_df[['月', '日']].drop_duplicates().shape[0]} 天")
    c3.metric("回程天數", f"{back_df[['月', '日']].drop_duplicates().shape[0]} 天")

    c4, c5, c6 = st.columns(3)
    c4.metric("總時數", f"{round(year_df['effective_hours'].sum(), 1)} hr")
    c5.metric("去程時數", f"{round(go_df['effective_hours'].sum(), 1)} hr")
    c6.metric("回程時數", f"{round(back_df['effective_hours'].sum(), 1)} hr")

    st.markdown("---")

    # --- 2. 每日摘要 (修正判斷邏輯與對齊) ---
    with st.expander(f"📅 {selected_year} 每日摘要行程 (點擊查看詳情)"):
        grouped = year_df.groupby(["月", "日"], sort=False)
        all_days = list(grouped)
        
        for idx, ((m, d), g) in enumerate(all_days):
            g_sorted = g.sort_values("完整時間")
            
            # P1: 日期 (5字元)
            p1 = f"{m:02d}/{d:02d}"
            
            # P2: 起駕
            first = g_sorted.iloc[0]
            start_txt = f"{first['時間']} {first['地點']} 起駕"
            p2 = f"{start_txt[:12]:<12}" # 縮短字數適配手機
            
            # P3: 午休 (不論是否最後一天都必須獨立判斷)
            p3 = " " * 12
            if "停駐駕" in g.columns:
                lunch = g[g["停駐駕"].astype(str).str.contains("午休", na=False)]
                if not lunch.empty:
                    l_node = lunch.iloc[0]
                    l_txt = f"{l_node['時間']} {l_node['地點']} 午休"
                    p3 = f"{l_txt[:12]:<12}"
            
            # P4: 終點 (駐駕/朝天宮/回宮)
            p4 = ""
            if "停駐駕" in g.columns:
                # 依優先序尋找
                found = False
                for kw in ["回宮", "朝天宮", "駐駕"]:
                    match = g[g["停駐駕"].astype(str).str.contains(kw, na=False)]
                    if not match.empty:
                        target = match.iloc[-1] # 找最後一筆符合的
                        status = f"抵達{kw}" if kw == "朝天宮" else kw
                        p4 = f"{target['時間']} {target['地點']} {status}"
                        found = True
                        break
                
                # 如果這天剛好沒有寫關鍵字，則抓該天最後一筆
                if not found:
                    last_node = g_sorted.iloc[-1]
                    p4 = f"{last_node['時間']} {last_node['地點']}"

            # 組合對齊標籤 (用較短的間隔防止手機截斷)
            label = f"{p1} || {p2} || {p3} || {p4}"
            
            with st.expander(label):
                cols = ['時間', '地點', '去回程']
                if '停駐駕' in g.columns: cols.append('停駐駕')
                st.dataframe(g_sorted[cols], use_container_width=True)

    # --- 3. 搜尋 ---
    st.markdown("---")
    st.subheader("🔍 跨年份地點查詢")
    keyword = st.text_input("搜尋地點", placeholder="例如：拱天宮")
    if keyword and not full_df.empty:
        res = full_df[full_df['地點'].astype(str).str.contains(keyword, na=False)].copy()
        if not res.empty:
            res['日期時間'] = res['完整時間'].dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(res[['年份', '日期時間', '地點', '去回程']].sort_values('日期時間', ascending=False), use_container_width=True)
else:
    st.error("初始化失敗")
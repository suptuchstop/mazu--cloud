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
# UI CSS (保持原有透明風)
# ==============================
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #2b0000 0%, #4b0000 50%, #1a0000 100%); color: #ffffff !important; }
    .stApp label, .stApp p, .stApp span, .stApp div { color: #ffffff !important; }
    .stSelectbox div[data-baseweb="select"], .stTextInput div[data-baseweb="base-input"] {
        background-color: transparent !important; border-color: rgba(255, 255, 255, 0.3) !important;
    }
    div[data-baseweb="popover"] ul { background-color: rgba(0, 0, 0, 0.9) !important; }
</style>
""", unsafe_allow_html=True)

# ==============================
# 資料核心邏輯
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
            df['完整時間'] = pd.to_datetime(f"{sheet}-"+df['月'].astype(str)+'-'+df['日'].astype(str)+' '+df['時間'].astype(str), format='%Y-%m-%d %H:%M', errors='coerce')
            df = df.dropna(subset=['完整時間']).sort_values('完整時間')
            
            # 預算時數
            df['time_diff_sec'] = df['完整時間'].diff().dt.total_seconds()
            df['effective_hours'] = df['time_diff_sec'].apply(lambda x: x/3600 if 0 < x <= 86400 else 0)
            
            all_years_data[sheet] = df
            s_part = df[['完整時間', '地點', '去回程']].copy()
            s_part['年份'] = sheet
            full_list.append(s_part)
            
        return all_years_data, pd.concat(full_list), sorted(xls.sheet_names, reverse=True)
    except:
        return None, None, []

all_data, full_df, available_years = load_all_data(FILE_URL)

if all_data:
    st.subheader("1️⃣ 年度統計與詳細行程")
    selected_year = st.selectbox("選擇年份", available_years)
    year_df = all_data[selected_year]
    
    # 統計卡片
    c1, c2, c3 = st.columns(3)
    c1.metric("總天數", f"{year_df[['月','日']].drop_duplicates().shape[0]} 天")
    c2.metric("去程時數", f"{round(year_df[year_df['去回程']=='去']['effective_hours'].sum(), 1)} hr")
    c3.metric("回程時數", f"{round(year_df[year_df['去回程']=='回']['effective_hours'].sum(), 1)} hr")

    # 每日摘要展開
    with st.expander(f"{selected_year} 每日摘要與行程"):
        grouped = year_df.groupby(["月", "日"], sort=False)
        all_days = list(grouped)
        
        for idx, ((m, d), g) in enumerate(all_days):
            g_sorted = g.sort_values("完整時間")
            
            # --- 判斷 1: 起駕 (當天第一筆) ---
            first = g_sorted.iloc[0]
            part1 = f"{m}/{d}"
            part2 = f"{first['時間']} {first['地點']} 起駕"
            
            # --- 判斷 2: 午休 (找關鍵字) ---
            part3 = ""
            if "停駐駕" in g.columns:
                lunch = g[g["停駐駕"].astype(str).str.contains("午休", na=False)]
                if not lunch.empty:
                    part3 = f"{lunch.iloc[0]['時間']} {lunch.iloc[0]['地點']} 午休"
            
            # --- 判斷 3: 駐駕 / 朝天宮 / 回宮 ---
            part4 = ""
            if "停駐駕" in g.columns:
                # 優先權：回宮 > 朝天宮 > 駐駕
                special_keywords = ["回宮", "朝天宮", "駐駕"]
                found_final = False
                
                for kw in special_keywords:
                    match = g[g["停駐駕"].astype(str).str.contains(kw, na=False)]
                    if not match.empty:
                        target = match.iloc[0]
                        # 如果是朝天宮，特別加上「抵達」字樣
                        status_label = f"抵達{kw}" if kw == "朝天宮" else kw
                        part4 = f"{target['時間']} {target['地點']} {status_label}"
                        found_final = True
                        break
                
                # 如果這天沒有任何標註，但它是最後一筆
                if not found_final and idx == len(all_days) - 1:
                    last = g_sorted.iloc[-1]
                    part4 = f"{last['時間']} {last['地點']}"

            # 組合摘要：格式固定為 [日期] || [起駕] || [午休] || [終點]
            label = f"{part1}  ||  {part2}  ||  {part3:^20}  ||  {part4}"
            
            with st.expander(label):
                cols = ['時間', '地點', '去回程']
                if '停駐駕' in g.columns: cols.append('停駐駕')
                st.dataframe(g_sorted[cols], use_container_width=True)

    st.markdown("---")
    # 跨年搜尋
    st.subheader("2️⃣ 跨年份地點查詢")
    keyword = st.text_input("輸入地點關鍵字")
    if keyword and not full_df.empty:
        res = full_df[full_df['地點'].astype(str).str.contains(keyword, na=False)].copy()
        if not res.empty:
            res['日期時間'] = res['完整時間'].dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(res[['年份', '日期時間', '地點', '去回程']].sort_values('日期時間', ascending=False), use_container_width=True)

else:
    st.error("資料載入失敗")
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
# UI CSS (保持全透明風格)
# ==============================
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #2b0000 0%, #4b0000 50%, #1a0000 100%); color: #ffffff !important; }
    .stApp label, .stApp p, .stApp span, .stApp div { color: #ffffff !important; }
    .stSelectbox div[data-baseweb="select"], .stTextInput div[data-baseweb="base-input"] {
        background-color: transparent !important; border-color: rgba(255, 255, 255, 0.3) !important;
    }
    div[data-baseweb="popover"] ul { background-color: rgba(0, 0, 0, 0.9) !important; }
    [data-testid="stMetricValue"] { color: #FFD700 !important; } /* 讓數據顯示為金色 */
</style>
""", unsafe_allow_html=True)

# ==============================
# 資料核心邏輯 (快取優化)
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
            # 統一「去/回」格式
            df['去回程'] = df['去回程'].astype(str).str.strip().replace({'去程': '去', '回程': '回'})
            # 轉換時間
            df['完整時間'] = pd.to_datetime(
                f"{sheet}-" + df['月'].astype(str) + '-' + df['日'].astype(str) + ' ' + df['時間'].astype(str), 
                format='%Y-%m-%d %H:%M', errors='coerce'
            )
            df = df.dropna(subset=['完整時間']).sort_values('完整時間')
            
            # 計算每筆資料間的時間差 (有效行走時數)
            df['time_diff_sec'] = df['完整時間'].diff().dt.total_seconds()
            # 過濾異常值（例如跨年或超過24小時的斷點不計入行走時數）
            df['effective_hours'] = df['time_diff_sec'].apply(lambda x: x/3600 if 0 < x <= 86400 else 0)
            
            all_years_data[sheet] = df
            s_part = df[['完整時間', '地點', '去回程']].copy()
            s_part['年份'] = sheet
            full_list.append(s_part)
            
        return all_years_data, pd.concat(full_list), sorted(xls.sheet_names, reverse=True)
    except Exception as e:
        return None, None, []

all_data, full_df, available_years = load_all_data(FILE_URL)

if all_data:
    st.subheader("1️⃣ 年度統計與詳細行程")
    selected_year = st.selectbox("選擇年份", available_years)
    year_df = all_data[selected_year]
    
    # --- 年度數據計算 ---
    # 天數計算 (依據 月/日 不重複計算)
    total_days = year_df[['月', '日']].drop_duplicates().shape[0]
    go_days = year_df[year_df['去回程'] == '去'][['月', '日']].drop_duplicates().shape[0]
    back_days = year_df[year_df['去回程'] == '回'][['月', '日']].drop_duplicates().shape[0]
    
    # 時數計算
    total_hours = year_df['effective_hours'].sum()
    go_hours = year_df[year_df['去回程'] == '去']['effective_hours'].sum()
    back_hours = year_df[year_df['去回程'] == '回']['effective_hours'].sum()

    # --- 顯示年度統計卡片 ---
    col1, col2, col3 = st.columns(3)
    col1.metric("總天數", f"{total_days} 天")
    col2.metric("去程天數", f"{go_days} 天")
    col3.metric("回程天數", f"{back_days} 天")

    col4, col5, col6 = st.columns(3)
    col4.metric("總時數", f"{round(total_hours, 1)} hr")
    col5.metric("去程時數", f"{round(go_hours, 1)} hr")
    col6.metric("回程時數", f"{round(back_hours, 1)} hr")

    st.markdown("---")

    # --- 每日摘要展開 ---
    with st.expander(f"{selected_year} 每日摘要與行程記錄"):
        grouped = year_df.groupby(["月", "日"], sort=False)
        all_days = list(grouped)
        
        for idx, ((m, d), g) in enumerate(all_days):
            g_sorted = g.sort_values("完整時間")
            
            # 1. 起駕 (當天第一筆)
            first = g_sorted.iloc[0]
            part1 = f"{m}/{d}"
            part2 = f"{first['時間']} {first['地點']} 起駕"
            
            # 2. 午休 (判斷是否有午休，若無則留白空間)
            part3 = ""
            if "停駐駕" in g.columns:
                lunch = g[g["停駐駕"].astype(str).str.contains("午休", na=False)]
                if not lunch.empty:
                    part3 = f"{lunch.iloc[0]['時間']} {lunch.iloc[0]['地點']} 午休"
            
            # 3. 終點判斷 (駐駕/朝天宮/回宮)
            part4 = ""
            if "停駐駕" in g.columns:
                special_keywords = ["回宮", "朝天宮", "駐駕"]
                found_final = False
                for kw in special_keywords:
                    match = g[g["停駐駕"].astype(str).str.contains(kw, na=False)]
                    if not match.empty:
                        target = match.iloc[0]
                        status = f"抵達{kw}" if kw == "朝天宮" else kw
                        part4 = f"{target['時間']} {target['地點']} {status}"
                        found_final = True
                        break
                # 若當天無關鍵字但為最後一筆
                if not found_final and idx == len(all_days) - 1:
                    last = g_sorted.iloc[-1]
                    part4 = f"{last['時間']} {last['地點']}"

            # 組合對齊標籤
            label = f"{part1}  ||  {part2}  ||  {part3:^25}  ||  {part4}"
            
            with st.expander(label):
                cols = ['時間', '地點', '去回程']
                if '停駐駕' in g.columns: cols.append('停駐駕')
                st.dataframe(g_sorted[cols], use_container_width=True)
# ------------------------------
    # 2️⃣ 跨年份地點查詢
    # ------------------------------
    st.subheader("2️⃣ 跨年份地點查詢")
    keyword = st.text_input("輸入地點關鍵字（例如：福安宮）", key="search_input")
    
    if keyword and not full_df.empty:
        # 在預載好的總表中進行關鍵字篩選
        res = full_df[full_df['地點'].astype(str).str.contains(keyword, na=False)].copy()
        
        if not res.empty:
            # 格式化顯示時間
            res['日期時間'] = res['完整時間'].dt.strftime('%Y-%m-%d %H:%M')
            # 整理欄位並依照時間由新到舊排序
            display_res = res[['年份', '日期時間', '地點', '去回程']].sort_values('日期時間', ascending=False)
            
            st.success(f"在歷年紀錄中找到 {len(display_res)} 筆關於「{keyword}」的結果：")
            st.dataframe(display_res, use_container_width=True)
        else:
            st.warning(f"查無關於「{keyword}」的資料。")

else:
    st.error("系統初始化失敗，請檢查資料來源（Excel 連結或格式）。")
import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import base64
from datetime import timedelta
import logging

# 設定日誌記錄，以便在後台查看錯誤細節
logging.basicConfig(level=logging.INFO)

# ==============================
# 初始化與設定 (Initialization)
# ==============================

st.set_page_config(page_title="白沙屯媽進香資料記錄", layout="wide")

FILE_URL = "https://raw.githubusercontent.com/suptuchstop/mazu--cloud/main/BaishatunMAZU_Data.xlsx"
APP_TITLE = "🔥白沙屯媽進香資料記錄🔥"
WATERMARK_IMAGE_PATH = "mazu_logo.png"

# ==============================
# 自定義介面樣式 (Custom Styling)
# ==============================

@st.cache_data
def get_base64_image(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        logging.warning(f"無法載入浮水印圖片: {e}")
        return ""

img_base64 = get_base64_image(WATERMARK_IMAGE_PATH)

st.markdown("""
<style>
.stApp {
    background: #2b0000;
    background-image: linear-gradient(135deg, #2b0000 0%, #4b0000 50%, #1a0000 100%);
}

.stApp p, .stApp span, .stApp label, .stApp div, .stApp h1, .stApp h2, .stApp h3 {
    color: #ffffff !important;
}

[data-testid="stMetricValue"] {
    color: #FFD700 !important;
    font-weight: bold;
}

[data-testid="stExpander"] {
    background: #1a1a1a;
    border: 1px solid rgba(255, 215, 0, 0.3);
    border-radius: 10px;
    margin-bottom: 12px;
}

.watermark {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    opacity: 0.12;
    z-index: 0;
}
</style>
""", unsafe_allow_html=True)

if img_base64:
    st.markdown(
        f'<img src="data:image/png;base64,{img_base64}" class="watermark" width="700">',
        unsafe_allow_html=True
    )

st.title(APP_TITLE)

# ==============================
# 資料載入與整理 (Data Loading & Preprocessing)
# ==============================

@st.cache_data
def load_data():
    try:
        logging.info(f"正在從 {FILE_URL} 載入資料...")
        r = requests.get(FILE_URL)
        r.raise_for_status() # 檢查網路請求是否成功
        
        # 讀取 Excel 檔案的所有 Sheet
        sheets = pd.read_excel(BytesIO(r.content), sheet_name=None)
        logging.info(f"成功載入資料，共 {len(sheets)} 個年份。")
    except requests.exceptions.RequestException as e:
        logging.error(f"網路請求失敗: {e}")
        st.error(f"❌ 無法連接到資料來源。請檢查網路連線或稍後再試。 (錯誤細節: {e})")
        return pd.DataFrame() # 傳回空的 DataFrame 防止後續程式碼崩潰
    except Exception as e:
        logging.error(f"資料讀取失敗: {e}")
        st.error(f"❌ 資料格式錯誤或無法讀取。 (錯誤細節: {e})")
        return pd.DataFrame()

    df_list = []

    for name, data in sheets.items():
        try:
            # 將 Sheet 名稱（年份）轉為整數
            year_val = int(name)
            # 清理資料：丟棄全為空的行
            data = data.dropna(how="all")
            # 建立年份欄位
            data["年份"] = year_val
            df_list.append(data)
        except ValueError:
            logging.warning(f"跳過無效的 Sheet 名稱（非年份）: {name}")
            continue

    if not df_list:
        st.warning("⚠️ 資料集中未找到有效年份的資料。")
        return pd.DataFrame()

    # 合併所有年份資料
    df = pd.concat(df_list, ignore_index=True)

    # 清理欄位名稱空白
    df.columns = df.columns.str.strip()

    # 強制將「月」、「日」轉為整數，確保 zfill 正確
    df["月"] = df["月"].fillna(0).astype(int)
    df["日"] = df["日"].fillna(0).astype(int)

    # 清理並確保「時間」欄位為字串
    df["時間"] = df["時間"].astype(str).str.strip()

    # 建立 datetime 字串 (YYYY-MM-DD HH:MM)
    datetime_str = (
        df["年份"].astype(str) + "-" +
        df["月"].astype(str).str.zfill(2) + "-" +
        df["日"].astype(str).str.zfill(2) + " " +
        df["時間"]
    )

    # 轉換為完整時間，強制拋棄錯誤格式 (errors="coerce")
    df["完整時間"] = pd.to_datetime(datetime_str, format="%Y-%m-%d %H:%M", errors="coerce")
    
    # 丟棄「時間」欄位無法辨識的記錄，確保資料完整性
    df = df.dropna(subset=["完整時間"])

    # 建立摘要日 (依據「完整時間」的日期)
    df["摘要日"] = df["完整時間"].dt.date

    # --- 關鍵核心邏輯修正 (文化日與深夜起駕) ---
    # 白沙屯拱天宮進香文化：深夜起駕算入新一天行程。
    # 判斷標準：若時間在 23:30 到 00:00 之間。
    df["行軍時間"] = df["完整時間"]
    mask = (df["完整時間"].dt.hour == 23) & (df["完整時間"].dt.minute >= 30)
    # 將行軍時間增加一天
    df.loc[mask, "行軍時間"] = df.loc[mask, "行軍時間"] + timedelta(days=1)
    # 提取「行軍日」日期
    df["行軍日"] = df["行軍時間"].dt.date

    # 確保「年」欄位存在並排序
    df["年"] = df["年份"]
    df = df.sort_values("完整時間")

    return df

df = load_data()

# ==============================
# 年份選擇與地點搜尋 (移到上方)
# ==============================

if df.empty:
    st.stop() # 如果資料為空，停止執行後續介面

# 提取不重複年份並從大到小排序 ( Desc order )
years = sorted(df["年"].unique(), reverse=True)
year = st.selectbox("選擇年份", years, index=0)

# ==============================
# 年度統計指標
# ==============================

st.header(f"{year} 白沙屯媽祖進香資料總覽")

# 計算統計指標。注意：統計天數應基於文化日「行軍日」
total_days = year_df["行軍日"].nunique()
go_days = year_df[year_df["去回程"] == "去程"]["行軍日"].nunique()
back_days = year_df[year_df["去回程"] == "回程"]["行軍日"].nunique()

start_time = year_df.iloc[0]["完整時間"]
end_time = year_df.iloc[-1]["完整時間"]
# 總時數 (最後記錄 - 第一記錄)
total_hours = round((end_time - start_time).total_seconds() / 3600, 1)

go_df = year_df[year_df["去回程"] == "去程"]
back_df = year_df[year_df["去回程"] == "回程"]

# 分別計算去程與回程時數 (假設資料是連續記錄)
if not go_df.empty:
    go_hours = round((go_df.iloc[-1]["完整時間"] - go_df.iloc[0]["完整時間"]).total_seconds() / 3600, 1)
else:
    go_hours = 0.0

if not back_df.empty:
    back_hours = round((back_df.iloc[-1]["完整時間"] - back_df.iloc[0]["完整時間"]).total_seconds() / 3600, 1)
else:
    back_hours = 0.0

# 顯示統計指標列
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("總天數", total_days)
c2.metric("去程天數", go_days)
c3.metric("回程天數", back_days)
c4.metric("總時數", total_hours)
c5.metric("去程時數", go_hours)
c6.metric("回程時數", back_hours)

st.divider()

# ==============================
# 每日行程摘要與詳細內容
# ==============================

st.subheader("每日行程摘要")

# --- 關鍵核心邏輯修正 (兵馬先動，標題日期回溯) ---
# 依「行軍日」（文化日）進行分組，並自動排序 ( chronological order )
grouped = year_df.groupby("行軍日", sort=True)

for g_date, g_df in grouped:
    
    # 組合摘要文字列
    summary_lines = []
    
    # --- **NEW: 標題日期前置與起駕事件** ---
    # 功能需求 2 的 G欄判斷
    
    # 取得起駕 (當天第一筆)
    start_row = g_df.sort_values("完整時間").iloc[0]
    
    # **NEW: 標題起駕日期回溯**
    # 如果起駕時間是深夜 (23:30-00:00)，這筆記錄在Excel中日曆天是前一天。
    # 這裡直接從 `start_row` 提取其原本的「摘要日」來顯示。
    start_date_display = pd.to_datetime(start_row["摘要日"]).strftime("%m/%d")
    
    # 組合起駕摘要：日期前置
    summary_lines.append(f"{start_date_display} 起駕: {start_row['完整時間'].strftime('%H:%M')} {start_row['地點']}")

    # 尋找特定的停駐駕事件。此時分組日期 `g_date` 就是行程的文化日日期。
    # 在Excel中，這整天行程的日曆日期可能跨越兩天（例如深夜起駕， Excel中是前一天深夜）。
    
    # **NEW: 午休、駐駕等事件日期前置**
    # 我們不依賴 Excel 的行順序，而是依據事件的停駐駕類別來查找。
    
    lunch_rest = g_df[g_df["停駐駕"] == "午休"]
    if not lunch_rest.empty:
        l_row = lunch_rest.iloc[0]
        l_date_display = pd.to_datetime(l_row["摘要日"]).strftime("%m/%d")
        summary_lines.append(f"{l_date_display} 午休: {l_row['完整時間'].strftime('%H:%M')} {l_row['地點']}")

    night_rest = g_df[g_df["停駐駕"] == "駐駕"]
    if not night_rest.empty:
        n_row = night_rest.iloc[0]
        n_date_display = pd.to_datetime(n_row["摘要日"]).strftime("%m/%d")
        summary_lines.append(f"{n_date_display} 駐駕: {n_row['完整時間'].strftime('%H:%M')} {n_row['地點']}")

    chaotian_arrival = g_df[g_df["停駐駕"] == "朝天宮"]
    if not chaotian_arrival.empty:
        c_row = chaotian_arrival.iloc[0]
        c_date_display = pd.to_datetime(c_row["摘要日"]).strftime("%m/%d")
        summary_lines.append(f"{c_date_display} 抵達北港: {c_row['完整時間'].strftime('%H:%M')}")

    home_return = g_df[g_df["停駐駕"] == "回宮"]
    if not home_return.empty:
        h_row = home_return.iloc[0]
        h_date_display = pd.to_datetime(h_row["摘要日"]).strftime("%m/%d")
        summary_lines.append(f"{h_date_display} 回宮: {h_row['完整時間'].strftime('%H:%M')}")

    # 將所有找到的事件組合成一個分號分隔的字串
    daily_summary_text = " ; ".join(summary_lines)
    
    # --- **NEW: 展開器標題日期處理** ---
    # **展開器的日期標題應顯示「日曆上的實際日期」 (g_df.iloc[0]["摘要日"])**。
    # 這樣使用者一眼就能看出這一天行程跨越了哪個日曆天。
    expander_date_display = pd.to_datetime(g_date).strftime("%m/%d")

    # 建立展開器 (st.expander)，標題包含回溯後的日期和摘要文字
    with st.expander(f"{expander_date_display} {daily_summary_text}"):
        
        # --- **NEW: 詳細行程內容合併 (跨年度地點搜尋需求修正)** ---
        # 顯示展開後的詳細內容表格。
        # 這裡必須使用「同一個行軍日分組內」的資料 (g_df)，
        # 才能確保展開內容與標題上顯示的摘要文字是完全一致的。
        
        # 建立一個副本進行顯示
        display_df = g_df[["完整時間", "地點", "去回程", "停駐駕"]].copy()
        # 格式化顯示時間
        display_df["時間"] = display_df["完整時間"].dt.strftime("%H:%M")
        # 重新排列欄位順序，讓時間排在最前面
        display_df = display_df[["時間", "地點", "去回程", "停駐駕"]]
        # 依時間升序排序
        display_df = display_df.sort_values("時間")

        # 顯示詳細表格
        st.dataframe(display_df, use_container_width=True, hide_index=True)

# 地點搜尋文字框 ( st.text_input )
keyword = st.text_input("跨年度地點關鍵字搜尋,例:白沙屯拱天宮")

# 執行篩選
year_df = df[df["年"] == year].copy()
if keyword:
    year_df = year_df[year_df["地點"].str.contains(keyword, na=False)]

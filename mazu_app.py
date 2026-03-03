import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

st.title("白沙屯媽祖行程雲端查詢系統")

# -------------------------
# 讀取 Excel
# -------------------------
@st.cache_data
def load_data(file_path):
    xls = pd.ExcelFile(file_path)
    all_data = {}
    summary = []

    for sheet in xls.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet)
        df.columns = df.columns.str.strip()

        df['去回程'] = df['去回程'].astype(str).str.strip().replace({'去程':'去','回程':'回'})
        df['停駐駕'] = df['停駐駕'].astype(str).str.strip()

        df['時間_dt'] = pd.to_datetime(df['時間'], format='%H:%M', errors='coerce')

        # 自動時間排序
        df = df.sort_values(['月','日','時間_dt'])

        all_data[str(sheet)] = df

        # 統計
        total_days = df[['月','日']].drop_duplicates().shape[0]
        go_days = df[df['去回程']=='去'][['月','日']].drop_duplicates().shape[0]
        back_days = df[df['去回程']=='回'][['月','日']].drop_duplicates().shape[0]

        go_time = 0
        back_time = 0

        for _, group in df.groupby(['月','日']):
            g = group[group['去回程']=='去']['時間_dt'].dropna()
            if len(g)>=2:
                go_time += (g.max()-g.min()).seconds/3600

            b = group[group['去回程']=='回']['時間_dt'].dropna()
            if len(b)>=2:
                back_time += (b.max()-b.min()).seconds/3600

        summary.append({
            "年份": sheet,
            "總天數": total_days,
            "去程天數": go_days,
            "回程天數": back_days,
            "總時間(時)": round(go_time+back_time,2),
            "去程時間(時)": round(go_time,2),
            "回程時間(時)": round(back_time,2)
        })

    return all_data, pd.DataFrame(summary)


# -------------------------
# 輸入 pCloud 檔案路徑
# -------------------------
file_path = st.text_input(
    "請輸入 pCloud Excel 路徑 (例如 P:/BaishatunMAZU_Data.xlsx)"
)

if file_path:
    try:
        data_dict, summary_df = load_data(file_path)

        st.subheader("年度統計總覽")
        st.dataframe(summary_df, use_container_width=True)

        # -------------------------
        # 年份選擇
        # -------------------------
        st.divider()
        year = st.selectbox("選擇年份", summary_df["年份"])

        df_year = data_dict[year]

        # -------------------------
        # 日期選擇
        # -------------------------
        unique_days = df_year[['月','日']].drop_duplicates()
        unique_days['日期'] = unique_days.apply(
            lambda x: f"{int(x['月']):02d}/{int(x['日']):02d}", axis=1
        )

        day_select = st.selectbox("選擇日期", unique_days['日期'])

        m, d = map(int, day_select.split("/"))
        df_day = df_year[(df_year['月']==m) & (df_year['日']==d)]

        st.subheader(f"{year} 年 {day_select} 詳細行程")
        st.dataframe(
            df_day[['時間','地點','去回程','停駐駕']],
            use_container_width=True
        )

        # -------------------------
        # 地點關鍵字搜尋
        # -------------------------
        st.divider()
        st.subheader("地點關鍵字搜尋")

        keyword = st.text_input("輸入地點關鍵字")

        if keyword:
            results = []

            for y, df in data_dict.items():
                match = df[df['地點'].astype(str).str.contains(keyword, na=False)]
                if not match.empty:
                    days = match[['月','日']].drop_duplicates()
                    for _, row in days.iterrows():
                        results.append({
                            "年份": y,
                            "日期": f"{int(row['月']):02d}/{int(row['日']):02d}"
                        })

            if results:
                result_df = pd.DataFrame(results).sort_values(['年份','日期'])
                st.dataframe(result_df, use_container_width=True)
            else:
                st.warning("沒有找到相關停駐紀錄")

    except Exception as e:
        st.error(f"讀取失敗：{e}")
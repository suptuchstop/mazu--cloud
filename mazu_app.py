import streamlit as st
import pandas as pd
import requests
from io import BytesIO

st.set_page_config(page_title="白沙屯媽祖年度統計", layout="wide")

st.title("白沙屯媽祖年度統計總覽")

# ===== GitHub Raw Excel 直連 =====
file_url = "https://raw.githubusercontent.com/suptuchstop/mazu--cloud/main/BaishatunMAZU_Data.xlsx"

try:
    # 下載 Excel
    response = requests.get(file_url)
    response.raise_for_status()

    excel_data = BytesIO(response.content)
    xls = pd.ExcelFile(excel_data, engine="openpyxl")

    st.write("讀到的 Sheets：", xls.sheet_names)

    summary = []

    for sheet in xls.sheet_names:

        df = pd.read_excel(xls, sheet_name=sheet)
        df.columns = df.columns.str.strip()

        # ===== 清理 去回程 =====
        df['去回程'] = (
            df['去回程']
            .astype(str)
            .str.strip()
            .replace({
                '去程': '去',
                '回程': '回',
                '去 ': '去',
                '回 ': '回'
            })
        )

        # ===== 建立完整時間 =====
        df['完整時間'] = pd.to_datetime(
            df['月'].astype(str) + '-' +
            df['日'].astype(str) + ' ' +
            df['時間'].astype(str),
            format='%m-%d %H:%M',
            errors='coerce'
        )

        df = df.sort_values('完整時間')

        go_time = 0
        back_time = 0

        # ===== 去程 =====
        go_df = df[df['去回程'] == '去'].dropna(subset=['完整時間'])
        go_times = go_df['完整時間'].tolist()

        for i in range(1, len(go_times)):
            diff = (go_times[i] - go_times[i - 1]).total_seconds()
            if 0 < diff <= 60 * 60 * 24:
                go_time += diff / 3600

        # ===== 回程 =====
        back_df = df[df['去回程'] == '回'].dropna(subset=['完整時間'])
        back_times = back_df['完整時間'].tolist()

        for i in range(1, len(back_times)):
            diff = (back_times[i] - back_times[i - 1]).total_seconds()
            if 0 < diff <= 60 * 60 * 24:
                back_time += diff / 3600

        # ===== 天數統計 =====
        total_days = df[['月', '日']].drop_duplicates().shape[0]
        go_days = go_df[['月', '日']].drop_duplicates().shape[0]
        back_days = back_df[['月', '日']].drop_duplicates().shape[0]

        summary.append({
            "年份": sheet,
            "總天數": total_days,
            "去程天數": go_days,
            "回程天數": back_days,
            "總時間(時)": round(go_time + back_time, 2),
            "去程時間(時)": round(go_time, 2),
            "回程時間(時)": round(back_time, 2)
        })

    summary_df = pd.DataFrame(summary)

    st.subheader("年度統計總覽")
    st.dataframe(summary_df, use_container_width=True)

except Exception as e:
    st.error(f"讀取失敗：{e}")
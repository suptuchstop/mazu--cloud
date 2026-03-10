import streamlit as st
import pandas as pd
from datetime import timedelta

st.set_page_config(layout="wide")

# ==============================
# 讀取資料
# ==============================

@st.cache_data
def load_data():

    df = pd.read_excel("BaishatunMAZU_Data.xlsx")

    df.columns = df.columns.str.strip()

    # 建立完整時間
    df['完整時間'] = pd.to_datetime(
        df['日期'].astype(str) + " " + df['時間'].astype(str)
    )

    # ==============================
    # 媽祖行軍邏輯
    # ==============================

    # 摘要用日期（保持原始）
    df['摘要日'] = df['完整時間'].dt.date

    # 行軍時間（23:30跨夜）
    df['行軍時間'] = df['完整時間']

    mask = (
        (df['完整時間'].dt.hour == 23) &
        (df['完整時間'].dt.minute >= 30)
    )

    df.loc[mask, '行軍時間'] = df.loc[mask, '行軍時間'] + timedelta(days=1)

    df['行軍日'] = df['行軍時間'].dt.date

    # 年度
    df['年'] = df['完整時間'].dt.year

    return df


df = load_data()

# ==============================
# 年份選擇
# ==============================

years = sorted(df['年'].unique())

year = st.sidebar.selectbox("選擇年份", years)

year_df = df[df['年'] == year].copy()

# ==============================
# 年度統計
# ==============================

st.title(f"{year} 白沙屯媽祖進香")

total_days = year_df['行軍日'].nunique()

go_days = year_df[year_df['去回程']=="去程"]['行軍日'].nunique()

back_days = year_df[year_df['去回程']=="回程"]['行軍日'].nunique()

# 時數

start_time = year_df.iloc[0]['完整時間']
end_time = year_df.iloc[-1]['完整時間']

total_hours = round((end_time-start_time).total_seconds()/3600,1)

go_df = year_df[year_df['去回程']=="去程"]
back_df = year_df[year_df['去回程']=="回程"]

go_hours = round(
    (go_df.iloc[-1]['完整時間'] - go_df.iloc[0]['完整時間']).total_seconds()/3600
    ,1
)

back_hours = round(
    (back_df.iloc[-1]['完整時間'] - back_df.iloc[0]['完整時間']).total_seconds()/3600
    ,1
)

c1,c2,c3,c4,c5,c6 = st.columns(6)

c1.metric("總天數", total_days)
c2.metric("去程天數", go_days)
c3.metric("回程天數", back_days)

c4.metric("總時數", total_hours)
c5.metric("去程時數", go_hours)
c6.metric("回程時數", back_hours)

st.divider()

# ==============================
# 每日摘要
# ==============================

grouped = year_df.groupby('摘要日', sort=False)

for g_date, g_df in grouped:

    date_str = pd.to_datetime(g_date).strftime("%m/%d")

    line = []

    # 起駕（當天最早）
    start_row = g_df.sort_values("完整時間").iloc[0]

    line.append(
        f"起駕:{start_row['完整時間'].strftime('%H:%M')} {start_row['地點']}"
    )

    # 午休
    rest = g_df[g_df['停駐駕']=="午休"]

    if len(rest)>0:

        r = rest.iloc[0]

        line.append(
            f"午休:{r['完整時間'].strftime('%H:%M')} {r['地點']}"
        )

    # 駐駕
    night = g_df[g_df['停駐駕']=="駐駕"]

    if len(night)>0:

        n = night.iloc[0]

        line.append(
            f"駐駕:{n['完整時間'].strftime('%H:%M')} {n['地點']}"
        )

    # 朝天宮
    chaotian = g_df[g_df['停駐駕']=="朝天宮"]

    if len(chaotian)>0:

        n = chaotian.iloc[0]

        line.append(
            f"抵達北港:{n['完整時間'].strftime('%H:%M')}"
        )

    # 回宮
    home = g_df[g_df['停駐駕']=="回宮"]

    if len(home)>0:

        n = home.iloc[0]

        line.append(
            f"回宮:{n['完整時間'].strftime('%H:%M')}"
        )

    summary = " ; ".join(line)

    with st.expander(f"{date_str}  {summary}"):

        # 詳細行程（用行軍日）
        day_rows = year_df[year_df['行軍日']==g_df.iloc[0]['行軍日']].copy()

        display_df = day_rows[
            ['完整時間','地點','去回程','停駐駕']
        ].copy()

        display_df['時間'] = display_df['完整時間'].dt.strftime('%H:%M')

        display_df = display_df[
            ['時間','地點','去回程','停駐駕']
        ]

        st.dataframe(display_df,use_container_width=True)
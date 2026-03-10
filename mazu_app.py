import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import base64
from datetime import timedelta

st.set_page_config(page_title="白沙屯媽進香資料記錄", layout="wide")

FILE_URL="https://raw.githubusercontent.com/suptuchstop/mazu--cloud/main/BaishatunMAZU_Data.xlsx"
APP_TITLE="🔥白沙屯媽進香資料記錄🔥"
WATERMARK_IMAGE_PATH="mazu_logo.png"

# ==============================
# 背景圖片
# ==============================

@st.cache_data
def get_base64_image(path):
    try:
        with open(path,"rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

img_base64=get_base64_image(WATERMARK_IMAGE_PATH)

st.markdown("""
<style>
.stApp{
background:#2b0000;
background-image:linear-gradient(135deg,#2b0000 0%,#4b0000 50%,#1a0000 100%);
}

.stApp p,.stApp span,.stApp label,.stApp div,.stApp h1,.stApp h2,.stApp h3{
color:#ffffff !important;
}

[data-testid="stMetricValue"]{
color:#FFD700 !important;
font-weight:bold;
}

[data-testid="stExpander"]{
background:#1a1a1a;
border:1px solid rgba(255,215,0,0.3);
border-radius:10px;
margin-bottom:12px;
}

.watermark{
position:fixed;
top:50%;
left:50%;
transform:translate(-50%,-50%);
opacity:0.12;
z-index:0;
}
</style>
""",unsafe_allow_html=True)

if img_base64:
    st.markdown(
        f'<img src="data:image/png;base64,{img_base64}" class="watermark" width="700">',
        unsafe_allow_html=True
    )

st.title(APP_TITLE)

# ==============================
# 讀取Excel (所有Sheet)
# ==============================

@st.cache_data
def load_data():

    r=requests.get(FILE_URL)
    r.raise_for_status()

    sheets=pd.read_excel(BytesIO(r.content),sheet_name=None)

    df_list=[]

    for name,data in sheets.items():
        data["年份"]=int(name)
        df_list.append(data)

    df=pd.concat(df_list,ignore_index=True)

    df.columns=df.columns.str.strip()

    df["月"]=df["月"].astype(int)
    df["日"]=df["日"].astype(int)

    df["完整時間"]=pd.to_datetime(
        df["年份"].astype(str)+"-"+
        df["月"].astype(str)+"-"+
        df["日"].astype(str)+" "+
        df["時間"].astype(str)
    )

    df["摘要日"]=df["完整時間"].dt.date

    df["行軍時間"]=df["完整時間"]

    mask=(df["完整時間"].dt.hour==23)&(df["完整時間"].dt.minute>=30)

    df.loc[mask,"行軍時間"]=df.loc[mask,"行軍時間"]+timedelta(days=1)

    df["行軍日"]=df["行軍時間"].dt.date

    df["年"]=df["年份"]

    df=df.sort_values("完整時間")

    return df

df=load_data()

# ==============================
# 年份選擇 (移到上方)
# ==============================

years=sorted(df["年"].unique())

year=st.selectbox("選擇年份",years,index=len(years)-1)

# ==============================
# 地點搜尋
# ==============================

keyword=st.text_input("地點關鍵字搜尋")

year_df=df[df["年"]==year].copy()

if keyword:
    year_df=year_df[year_df["地點"].str.contains(keyword,na=False)]

# ==============================
# 年度統計
# ==============================

st.title(f"{year} 白沙屯媽祖進香")

total_days=year_df["行軍日"].nunique()

go_days=year_df[year_df["去回程"]=="去程"]["行軍日"].nunique()

back_days=year_df[year_df["去回程"]=="回程"]["行軍日"].nunique()

start=year_df.iloc[0]["完整時間"]
end=year_df.iloc[-1]["完整時間"]

total_hours=round((end-start).total_seconds()/3600,1)

go_df=year_df[year_df["去回程"]=="去程"]
back_df=year_df[year_df["去回程"]=="回程"]

go_hours=round((go_df.iloc[-1]["完整時間"]-go_df.iloc[0]["完整時間"]).total_seconds()/3600,1)
back_hours=round((back_df.iloc[-1]["完整時間"]-back_df.iloc[0]["完整時間"]).total_seconds()/3600,1)

c1,c2,c3,c4,c5,c6=st.columns(6)

c1.metric("總天數",total_days)
c2.metric("去程天數",go_days)
c3.metric("回程天數",back_days)

c4.metric("總時數",total_hours)
c5.metric("去程時數",go_hours)
c6.metric("回程時數",back_hours)

st.divider()

# ==============================
# 每日摘要
# ==============================

grouped=year_df.groupby("摘要日",sort=False)

for g_date,g_df in grouped:

    date_str=pd.to_datetime(g_date).strftime("%m/%d")

    line=[]

    start_row=g_df.sort_values("完整時間").iloc[0]

    line.append(f"起駕:{start_row['完整時間'].strftime('%H:%M')} {start_row['地點']}")

    rest=g_df[g_df["停駐駕"]=="午休"]
    if len(rest)>0:
        r=rest.iloc[0]
        line.append(f"午休:{r['完整時間'].strftime('%H:%M')} {r['地點']}")

    night=g_df[g_df["停駐駕"]=="駐駕"]
    if len(night)>0:
        n=night.iloc[0]
        line.append(f"駐駕:{n['完整時間'].strftime('%H:%M')} {n['地點']}")

    chaotian=g_df[g_df["停駐駕"]=="朝天宮"]
    if len(chaotian)>0:
        n=chaotian.iloc[0]
        line.append(f"抵達北港:{n['完整時間'].strftime('%H:%M')}")

    home=g_df[g_df["停駐駕"]=="回宮"]
    if len(home)>0:
        n=home.iloc[0]
        line.append(f"回宮:{n['完整時間'].strftime('%H:%M')}")

    summary=" ; ".join(line)

    with st.expander(f"{date_str}  {summary}"):

        day_rows=year_df[year_df["行軍日"]==g_df.iloc[0]["行軍日"]]

        display_df=day_rows[["完整時間","地點","去回程","停駐駕"]].copy()

        display_df["時間"]=display_df["完整時間"].dt.strftime("%H:%M")

        display_df=display_df[["時間","地點","去回程","停駐駕"]]

        st.dataframe(display_df,use_container_width=True)
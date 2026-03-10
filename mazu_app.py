import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import base64
from datetime import timedelta

# ==============================
# 應用程式配置
# ==============================
st.set_page_config(page_title="白沙屯媽進香資料記錄", layout="wide")

FILE_URL = "https://raw.githubusercontent.com/suptuchstop/mazu--cloud/main/BaishatunMAZU_Data.xlsx"
APP_TITLE = "🔥白沙屯媽進香資料記錄🔥"
WATERMARK_IMAGE_PATH = "mazu_logo.png"

# ==============================
# UI (完全不動)
# ==============================
@st.cache_data
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return ""

img_base64 = get_base64_image(WATERMARK_IMAGE_PATH)

st.markdown("""
<style>
.stApp{
background:#2b0000;
background-image:linear-gradient(135deg,#2b0000 0%,#4b0000 50%,#1a0000 100%);
background-attachment:fixed;
}
.stApp p,.stApp span,.stApp label,.stApp div,.stApp h1,.stApp h2,.stApp h3{
color:white!important;
}
</style>
""",unsafe_allow_html=True)

if img_base64:
    st.markdown(
        f'<img src="data:image/png;base64,{img_base64}" style="position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);opacity:0.12;">',
        unsafe_allow_html=True
    )

st.title(APP_TITLE)

# ==============================
# 資料讀取
# ==============================
@st.cache_data(show_spinner=False)
def load_all_data(url):

    response=requests.get(url)
    response.raise_for_status()

    xls=pd.ExcelFile(BytesIO(response.content),engine="openpyxl")

    all_data={}
    full_list=[]

    for sheet in xls.sheet_names:

        df=pd.read_excel(xls,sheet_name=sheet)
        df.columns=df.columns.str.strip()

        df['去回程']=df['去回程'].astype(str).str.strip().replace({
            '去程':'去',
            '回程':'回'
        })

        # 完整時間
        df['完整時間']=pd.to_datetime(
            df['年份'].astype(str)+"-"+df['月'].astype(str)+"-"+df['日'].astype(str)+" "+df['時間'].astype(str),
            errors='coerce'
        )

        df=df.dropna(subset=['完整時間'])

        df=df.sort_values("完整時間").reset_index(drop=True)

        # =====================
        # 修正1：時間差 (不分去回)
        # =====================
        diff=df['完整時間'].diff().dt.total_seconds()

        df['effective_hours']=diff.apply(
            lambda x:x/3600 if pd.notna(x) and 0<x<=48 else 0
        )

        # =====================
        # 修正2：凌晨算前一天
        # =====================
        df['adjusted_date']=df['完整時間']

        mask=df['完整時間'].dt.hour<3

        df.loc[mask,'adjusted_date']=df.loc[mask,'adjusted_date']-pd.Timedelta(days=1)

        df['adjusted_date']=df['adjusted_date'].dt.date

        all_data[sheet]=df

        full_list.append(
            df[['完整時間','地點','去回程']].assign(年份=sheet)
        )

    return all_data,pd.concat(full_list),sorted(xls.sheet_names,reverse=True)

all_data,full_df,available_years=load_all_data(FILE_URL)

# ==============================
# 主畫面
# ==============================
if all_data:

    selected_year=st.selectbox("請選擇年份",available_years)

    year_df=all_data[selected_year].copy()

    # ==========================
    # 年度統計
    # ==========================

    go_df=year_df[year_df['去回程']=="去"]
    back_df=year_df[year_df['去回程']=="回"]

    col1,col2,col3=st.columns(3)

    col1.metric("總天數",f"{year_df['adjusted_date'].nunique()} 天")
    col2.metric("去程天數",f"{go_df['adjusted_date'].nunique()} 天")
    col3.metric("回程天數",f"{back_df['adjusted_date'].nunique()} 天")

    col4,col5,col6=st.columns(3)

    col4.metric("總時數",f"{round(year_df['effective_hours'].sum(),1)} hr")
    col5.metric("去程時數",f"{round(go_df['effective_hours'].sum(),1)} hr")
    col6.metric("回程時數",f"{round(back_df['effective_hours'].sum(),1)} hr")

    st.markdown("---")

    # ==========================
    # 每日摘要
    # ==========================
    st.subheader(f"📅 {selected_year} 行程摘要")

    grouped=year_df.groupby('adjusted_date',sort=False)

    for g_date,g in grouped:

        g=g.sort_values("完整時間")

        first_node=g.iloc[0]
        last_node=g.iloc[-1]

        line1=g_date.strftime('%m/%d')

        status_start="起駕"

        if '停駐駕' in g.columns:
            if pd.notna(first_node['停駐駕']) and str(first_node['停駐駕']).strip()!="":
                status_start=first_node['停駐駕']

        line2=f"{first_node['時間']}  {first_node['地點']}  {status_start}"

        line3=""
        if '停駐駕' in g.columns:

            lunch=g[g['停駐駕'].astype(str).str.contains("午休",na=False)]

            if not lunch.empty:
                t=lunch.iloc[0]
                line3=f"{t['時間']}  {t['地點']}  午休"

        line4=f"{last_node['時間']}  {last_node['地點']}  駐駕"

        summary=[line1,line2]

        if line3:
            summary.append(line3)

        summary.append(line4)

        label="\n".join(summary)

        with st.expander(label):

            st.dataframe(
                g.sort_values("完整時間"),
                use_container_width=True
            )

    # ==========================
    # 搜尋
    # ==========================
    st.markdown("---")

    st.subheader("🔍 地點查詢")

    key=st.text_input("搜尋關鍵字")

    if key:

        res=full_df[full_df['地點'].astype(str).str.contains(key,na=False)].copy()

        if not res.empty:

            res['日期時間']=res['完整時間'].dt.strftime('%Y-%m-%d %H:%M')

            st.dataframe(
                res[['年份','日期時間','地點','去回程']].sort_values('日期時間',ascending=False),
                use_container_width=True
            )

else:
    st.error("資料載入失敗")
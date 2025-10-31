import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date
from io import BytesIO

st.set_page_config(page_title="股票歷史資料下載器", layout="centered")
st.title("📈 股票歷史資料下載器（Streamlit Cloud 版）")
st.caption("支援 0001.HK、2330.TW、AAPL｜資料來源：Yahoo Finance")

ticker = st.text_input("股票代號", value="0001.HK")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("開始日期", value=date(2005, 1, 1))
with col2:
    end_date = st.date_input("結束日期", value=date.today())

if st.button("📥 下載歷史資料"):
    if not ticker.strip():
        st.error("請輸入股票代號！")
    else:
        with st.spinner(f"正在下載 {ticker}..."):
            try:
                data = yf.download(ticker, start=start_date, end=end_date)
            except Exception as e:
                st.error(f"❌ 下載失敗：{e}")
                data = pd.DataFrame()

        if data.empty:
            st.error(f"無法取得 {ticker} 的資料，請檢查代號（如 .HK）或日期。")
        else:
            # 重設索引
            data = data.reset_index()
            # 展平 MultiIndex 欄位（關鍵！）
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = ['_'.join(col).strip() if col[1] != '' else col[0] for col in data.columns]

            st.success(f"✅ 成功取得 {len(data)} 筆資料！")
            st.subheader("前5筆")
            st.dataframe(data.head())
            st.subheader("後5筆")
            st.dataframe(data.tail())

            # === 直接從記憶體生成 Excel（不寫入磁碟）===
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                data.to_excel(writer, index=False, sheet_name='Data')
            excel_data = output.getvalue()

            safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in ticker)

            st.download_button(
                label="💾 點此下載 Excel 檔案",
                data=excel_data,
                file_name=f"{safe_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
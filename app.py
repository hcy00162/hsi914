import streamlit as st
import yfinance as yf
import pandas as pd
import os
from datetime import datetime, date

# ====== 設定頁面 ======
st.set_page_config(page_title="股票歷史資料下載器", layout="centered")
st.title("📈 股票歷史資料下載器（Yahoo Finance）")
st.caption("支援港股(.HK)、美股、台股(.TW)等｜資料來源：Yahoo Finance")

# ====== 使用者輸入 ======
ticker = st.text_input("請輸入股票代號（例如：0001.HK、AAPL、2330.TW）", value="0001.HK")

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("開始日期", value=date(2005, 1, 1))
with col2:
    end_date = st.date_input("結束日期", value=date.today())

# ====== 下載按鈕 ======
if st.button("📥 下載歷史資料"):
    if not ticker.strip():
        st.error("請輸入股票代號！")
    else:
        with st.spinner(f"正在下載 {ticker} 的資料..."):
            try:
                data = yf.download(ticker, start=start_date, end=end_date)
            except Exception as e:
                st.error(f"下載失敗：{e}")
                data = pd.DataFrame()

        if data.empty:
            st.error(f"❌ 無法取得 {ticker} 的資料，請檢查代號或日期。")
        else:
            # 重設索引
            data = data.reset_index()

            # 展平 MultiIndex 欄位（防呆）
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = ['_'.join(col).strip() if col[1] != '' else col[0] for col in data.columns]

            # 顯示資料預覽
            st.success(f"✅ 成功下載 {len(data)} 筆資料！")
            st.subheader("前5筆資料")
            st.dataframe(data.head())
            st.subheader("後5筆資料")
            st.dataframe(data.tail())

            # 建立 downloads 資料夾
            os.makedirs("downloads", exist_ok=True)

            # 儲存 Excel
            safe_ticker = "".join(c if c.isalnum() or c in "._-" else "_" for c in ticker)
            output_path = f"downloads/{safe_ticker}.xlsx"
            data.to_excel(output_path, index=False)

            # 提供下載按鈕
            with open(output_path, "rb") as f:
                st.download_button(
                    label="💾 下載 Excel 檔案",
                    data=f,
                    file_name=f"{safe_ticker}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            st.info(f"檔案已儲存至本地：`{output_path}`")

# ====== 使用說明 ======
with st.expander("ℹ️ 使用說明"):
    st.markdown("""
    - **港股**：加 `.HK`，例如 `0001.HK`
    - **台股**：加 `.TW`，例如 `2330.TW`
    - **美股**：直接輸入代號，例如 `AAPL`、`TSLA`
    - 結束日期可設為未來，系統會自動下載至最新交易日
    - 下載的檔案會同時儲存在 `downloads/` 資料夾（方便你本地管理）
    """)
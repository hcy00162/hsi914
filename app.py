import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date
from io import BytesIO

# ====== 頁面設定 ======
st.set_page_config(
    page_title="股票歷史資料下載器",
    page_icon="📈",
    layout="centered"
)

# 自訂標題與 Logo（使用免費圖示）
st.image("https://cdn-icons-png.flaticon.com/512/2592/2592425.png", width=80)
st.title("📊 股票歷史資料下載器")
st.markdown("由 [你的名字] 提供｜資料來源：Yahoo Finance")
st.markdown("---")

# ====== 使用者輸入 ======
ticker = st.text_input("請輸入股票代號", value="0001.HK")

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("開始日期", value=date(2005, 1, 1))
with col2:
    end_date = st.date_input("結束日期", value=date.today())

# ====== 常見股票與說明 ======
with st.expander("📌 常見股票代號與使用說明"):
    st.markdown("""
    ### 🔹 常見代號
    - **港股**：`0001.HK`（長和）、`0700.HK`（騰訊）、`0941.HK`（中移動）
    - **台股**：`2330.TW`（台積電）、`2454.TW`（聯發科）、`2317.TW`（鴻海）
    - **美股**：`AAPL`（蘋果）、`TSLA`（特斯拉）、`GOOGL`（Google）

    ### 🔹 使用說明
    1. 輸入股票代號（記得加 `.HK`、`.TW` 等市場代碼）
    2. 選擇日期範圍（結束日期可設為未來，系統會自動下載至最新）
    3. 點擊「下載資料」
    4. 預覽資料與走勢圖
    5. 選擇格式並下載 Excel 或 CSV

    > 💡 資料每日更新，收盤價已調整除權息（Adj Close 未顯示，但 Close 可用於長期分析）
    """)

# ====== 下載按鈕 ======
if st.button("📥 下載歷史資料"):
    if not ticker.strip():
        st.error("❌ 請輸入股票代號！")
    else:
        with st.spinner(f"正在下載 {ticker} 的資料..."):
            try:
                data = yf.download(ticker, start=start_date, end=end_date)
            except Exception as e:
                st.error(f"❌ 下載失敗：{e}")
                data = pd.DataFrame()

        if data.empty:
            st.error(f"無法取得 {ticker} 的資料，請檢查代號或日期範圍。")
        else:
            # 重設索引
            data = data.reset_index()
            # 展平 MultiIndex 欄位（防呆）
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = ['_'.join(col).strip() if col[1] != '' else col[0] for col in data.columns]

            st.success(f"✅ 成功下載 {len(data)} 筆資料！")

            # ====== 顯示資料預覽 ======
            st.subheader("前5筆資料")
            st.dataframe(data.head())

            # ====== 股價走勢圖 ======
            st.subheader("📈 股價走勢圖（收盤價）")
            if 'Date' in data.columns and 'Close' in data.columns:
                chart_data = data.set_index('Date')[['Close']]
                st.line_chart(chart_data)
            else:
                st.warning("無法繪製走勢圖：缺少 Date 或 Close 欄位")

            st.subheader("📊 成交量趨勢")
            if 'Date' in data.columns and 'Volume' in data.columns:
                vol_data = data.set_index('Date')[['Volume']]
                st.bar_chart(vol_data)
            else:
                st.warning("無法顯示成交量")

            # ====== 選擇下載格式 ======
            format_choice = st.radio(
                "選擇下載格式",
                ["Excel (.xlsx)", "CSV (.csv)"],
                horizontal=True
            )

            # 生成檔案
            safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in ticker)

            if format_choice == "Excel (.xlsx)":
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    data.to_excel(writer, index=False, sheet_name='StockData')
                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                file_ext = ".xlsx"
            else:  # CSV
                output = data.to_csv(index=False).encode('utf-8')
                mime_type = "text/csv"
                file_ext = ".csv"

            st.download_button(
                label=f"⬇️ 下載 {format_choice}",
                data=output,
                file_name=f"{safe_name}{file_ext}",
                mime=mime_type,
                type="primary"
            )
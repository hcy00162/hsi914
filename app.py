import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date
from io import BytesIO

# ====== 頁面設定 ======
st.set_page_config(page_title="股票歷史資料下載器", layout="centered")
st.title("📈 股票歷史資料下載器")
st.caption("支援港股(.HK)、台股(.TW)、美股｜資料來源：Yahoo Finance")

# ====== 使用者輸入 ======
ticker = st.text_input("請輸入股票代號（例如：0001.HK、2330.TW、AAPL）", value="0001.HK")

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("開始日期", value=date(2005, 1, 1))
with col2:
    end_date = st.date_input("結束日期", value=date.today())

# ====== 下載邏輯 ======
if st.button("📥 下載歷史資料"):
    if not ticker.strip():
        st.error("請輸入股票代號！")
    else:
        with st.spinner(f"正在下載 {ticker} 的資料..."):
            try:
                data = yf.download(ticker, start=start_date, end=end_date)
            except Exception as e:
                st.error(f"❌ 下載失敗：{e}")
                data = pd.DataFrame()

        if data.empty:
            st.error(f"無法取得 {ticker} 的資料，請檢查代號（如 .HK）或日期範圍。")
        else:
            # 重設索引（Date 變一般欄位）
            data = data.reset_index()
            
            # 展平 MultiIndex 欄位（防呆）
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = ['_'.join(col).strip() if col[1] != '' else col[0] for col in data.columns]

            st.success(f"✅ 成功下載 {len(data)} 筆資料！")
            
            st.subheader("前5筆資料")
            st.dataframe(data.head())
            
            st.subheader("後5筆資料")
            st.dataframe(data.tail())

            # 生成 Excel（記憶體中）
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                data.to_excel(writer, index=False, sheet_name='StockData')
            excel_data = output.getvalue()

            # 安全檔案名
            safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in ticker)

            st.download_button(
                label="💾 點此下載 Excel 檔案",
                data=excel_data,
                file_name=f"{safe_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# ====== 使用說明與常見股票列表（放在最下方） ======
st.markdown("---")
st.subheader("ℹ️ 使用說明")
st.markdown("""
- 輸入股票代號時，請**包含市場代碼**：
  - **港股**：`0001.HK`、`0700.HK`、`2318.HK`
  - **台股**：`2330.TW`、`2454.TW`、`2317.TW`
  - **美股**：`AAPL`、`TSLA`、`NVDA`（無需加後綴）
- 結束日期可設為未來，系統會自動下載至最新交易日。
- 下載的 Excel 檔案包含：日期、開盤價、最高價、最低價、收盤價、調整後收盤價、成交量。
""")

st.subheader("📌 常見股票代號參考")
st.markdown("""
| 市場 | 股票名稱       | 代號        |
|------|----------------|-------------|
| 港股 | 長和           | `0001.HK`   |
| 港股 | 匯豐控股       | `0005.HK`   |
| 港股 | 腾訊控股       | `0700.HK`   |
| 港股 | 友邦保險       | `1299.HK`   |
| 台股 | 台積電         | `2330.TW`   |
| 台股 | 聯發科         | `2454.TW`   |
| 台股 | 鴻海           | `2317.TW`   |
| 美股 | Apple          | `AAPL`      |
| 美股 | Tesla          | `TSLA`      |
| 美股 | NVIDIA         | `NVDA`      |
""")

st.caption("本服務使用 Yahoo Finance 資料｜部署於 Streamlit Cloud")
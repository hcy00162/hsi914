import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="📊 HSI 季節性波幅分析", layout="wide")
st.title("📊 HSI 季節性波幅分析工具")

# 上傳檔案
uploaded_file = st.file_uploader("上傳 HSI Excel 檔案（如 HSI2710.xlsx）", type=["xlsx"])
if uploaded_file is None:
    st.info("💡 請上傳您的 HSI 歷史數據 Excel 檔案")
    st.stop()

# 讀取資料
df = pd.read_excel(uploaded_file, engine='openpyxl')
df['Date'] = pd.to_datetime(df['Date'])
df = df.sort_values('Date').reset_index(drop=True)

# 側邊欄參數
with st.sidebar:
    st.header("⚙️ 參數設定")
    START_MONTH = st.selectbox("起始月份", options=list(range(1, 13)), index=10)  # 預設 11 月
    START_DAY = st.slider("起始日", min_value=1, max_value=31, value=3)
    END_MONTH = st.selectbox("結束月份", options=list(range(1, 13)), index=11)   # 預設 12 月
    END_DAY = st.slider("結束日", min_value=1, max_value=31, value=30)
    MIN_YEAR = st.slider("起始年份", 2000, 2024, 2005)
    MAX_YEAR = st.slider("結束年份", 2005, 2024, 2024)

# 核心函數
def calculate_volatility_for_date(start_month, start_day):
    results = []
    for year in range(MIN_YEAR, MAX_YEAR + 1):
        try:
            target_date = pd.to_datetime(f"{year}-{start_month:02d}-{start_day:02d}")
        except ValueError:
            continue
        end_date = pd.to_datetime(f"{year}-{END_MONTH:02d}-{END_DAY:02d}")
        
        month_data = df[df['Date'].dt.year == year]
        candidates = month_data[
            (month_data['Date'] >= target_date) &
            (month_data['Date'] <= pd.to_datetime(f"{year}-{start_month:02d}-28") + pd.DateOffset(days=3))
        ]
        if candidates.empty:
            continue
        start_row = candidates.iloc[0]
        start_date = start_row['Date']
        start_low = start_row['Low']
        start_high = start_row['High']
        
        period = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
        if period.empty:
            continue
        max_high = period['High'].max()
        min_low = period['Low'].min()
        
        upside = (max_high - start_low) / start_low * 100
        downside = (start_high - min_low) / start_high * 100
        results.append({'Year': year, 'Upside_%': upside, 'Downside_%': downside})
    
    if not results:
        return None, None, 0
    df_res = pd.DataFrame(results)
    return df_res['Upside_%'], df_res['Downside_%'], len(df_res)

# 計算指定日結果
st.subheader(f"📈 從每年 {START_MONTH}/{START_DAY} 起算的波幅（至 {END_MONTH}/{END_DAY}）")
upside_series, downside_series, n = calculate_volatility_for_date(START_MONTH, START_DAY)
if upside_series is not None:
    st.write(f"📊 有效年份：{n} 年")
    st.write(f"📈 平均上升波幅：{upside_series.mean():.2f}%")
    st.write(f"📉 平均下跌波幅：{downside_series.mean():.2f}%")
    
    # 完整表格
    full_results = []
    for year in range(MIN_YEAR, MAX_YEAR + 1):
        try:
            target_date = pd.to_datetime(f"{year}-{START_MONTH:02d}-{START_DAY:02d}")
        except ValueError:
            continue
        end_date = pd.to_datetime(f"{year}-{END_MONTH:02d}-{END_DAY:02d}")
        month_data = df[df['Date'].dt.year == year]
        candidates = month_data[
            (month_data['Date'] >= target_date) &
            (month_data['Date'] <= pd.to_datetime(f"{year}-{START_MONTH:02d}-28") + pd.DateOffset(days=3))
        ]
        if candidates.empty:
            continue
        start_row = candidates.iloc[0]
        start_date = start_row['Date']
        start_low = start_row['Low']
        start_high = start_row['High']
        period = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
        if period.empty:
            continue
        max_high = period['High'].max()
        min_low = period['Low'].min()
        upside = (max_high - start_low) / start_low * 100
        downside = (start_high - min_low) / start_high * 100
        full_results.append({
            'Year': year,
            'Start_Date': start_date,
            'Start_Low': start_low,
            'Start_High': start_high,
            'Max_High': max_high,
            'Min_Low': min_low,
            'Upside_%': upside,
            'Downside_%': downside
        })
    result_df = pd.DataFrame(full_results)
    st.dataframe(result_df.round(2))
else:
    st.error("❌ 無有效數據")

# 最佳進場日分析
if st.sidebar.button("🔍 分析最佳進場日"):
    st.subheader("🎯 最佳進場日分析（90% 年份保證波幅）")
    
    days_in_month = {1:31, 2:29, 3:31, 4:30, 5:31, 6:30,
                     7:31, 8:31, 9:30, 10:31, 11:30, 12:31}.get(START_MONTH, 31)
    
    best_long_day, best_long_val = None, -999
    best_short_day, best_short_val = None, -999
    
    for day in range(1, days_in_month + 1):
        up_series, down_series, count = calculate_volatility_for_date(START_MONTH, day)
        if up_series is not None and count >= 10:
            sorted_up = up_series.sort_values().reset_index(drop=True)
            sorted_down = down_series.sort_values().reset_index(drop=True)
            idx_90 = min(2, len(sorted_up) - 1)  # 第3小
            up_90 = sorted_up.iloc[idx_90]
            down_90 = sorted_down.iloc[idx_90]
            
            if up_90 > best_long_val:
                best_long_val = up_90
                best_long_day = day
            if down_90 > best_short_val:
                best_short_val = down_90
                best_short_day = day
    
    if best_long_day:
        st.success(f"✅ 最佳做多日：{START_MONTH}/{best_long_day} → 90% 年份 Upside ≥ {best_long_val:.2f}%")
        st.success(f"✅ 最佳做空日：{START_MONTH}/{best_short_day} → 90% 年份 Downside ≥ {best_short_val:.2f}%")
    else:
        st.warning("⚠️ 無足夠數據分析最佳進場日")
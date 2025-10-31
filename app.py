import streamlit as st
import pandas as pd
import numpy as np
import os

# 標題
st.title("📊 HSI 季節性波幅分析（2005–2024）")

# 讀取 Excel（假設檔案與 app.py 同目錄）
file_path = "HSI2710.xlsx"
if not os.path.exists(file_path):
    st.error("❌ 找不到 HSI2710.xlsx，請確認檔案已上傳至 GitHub 倉庫根目錄。")
    st.stop()

df = pd.read_excel(file_path, engine='openpyxl')
df['Date'] = pd.to_datetime(df['Date'])
df = df.sort_values('Date').reset_index(drop=True)

# 參數設定（可由使用者調整）
st.sidebar.header("⚙️ 參數設定")
START_MONTH = st.sidebar.selectbox("起始月份", list(range(1, 13)), index=10)  # 預設 11 月
START_DAY = st.sidebar.slider("起始日", 1, 31, 3)
END_MONTH = st.sidebar.selectbox("結束月份", list(range(1, 13)), index=11)   # 預設 12 月
END_DAY = st.sidebar.slider("結束日", 1, 31, 30)

MIN_YEAR, MAX_YEAR = 2005, 2024

# 計算指定起始日的波幅
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

# 計算結果
upside_series, downside_series, n = calculate_volatility_for_date(START_MONTH, START_DAY)

if n == 0:
    st.warning("⚠️ 無有效數據，請調整參數。")
else:
    # 計算分位數（100% = 最小值，90% = 第3小，85% = 第4小）
    def get_kth_smallest(series, k):
        sorted_vals = series.sort_values().reset_index(drop=True)
        return sorted_vals.iloc[k - 1] if len(sorted_vals) >= k else None

    k1, k3, k4 = 1, 3, 4
    quantiles = pd.DataFrame({
        'Label': ['100% (最少值)', '90% (第3小)', '85% (第4小)'],
        'Upside_%': [
            get_kth_smallest(upside_series, k1),
            get_kth_smallest(upside_series, k3),
            get_kth_smallest(upside_series, k4)
        ],
        'Downside_%': [
            get_kth_smallest(downside_series, k1),
            get_kth_smallest(downside_series, k3),
            get_kth_smallest(downside_series, k4)
        ]
    }).round(2)

    st.subheader(f"📈 從每年 {START_MONTH}/{START_DAY} 起算的波幅統計")
    st.dataframe(quantiles)

    # 找出最佳做多/做空日（遍歷當月 1–31 日）
    st.subheader("🎯 最佳進場日分析（90% 年份保證波幅）")
    best_long_day, best_short_day = None, None
    best_long_val, best_short_val = -999, -999

    days_in_month = {1:31, 2:29, 3:31, 4:30, 5:31, 6:30,
                     7:31, 8:31, 9:30, 10:31, 11:30, 12:31}.get(START_MONTH, 31)

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
        st.info("ℹ️ 無足夠數據分析最佳進場日")
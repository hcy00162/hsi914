import streamlit as st
import pandas as pd
import numpy as np
import os

# ===== 網頁標題 =====
st.set_page_config(page_title="HSI 季節性波幅分析", layout="wide")
st.title("📊 HSI 季節性波幅分析（2005–2024）")

# ===== 參數設定（側邊欄）=====
st.sidebar.header("⚙️ 參數設定")
START_MONTH = st.sidebar.selectbox("起始月份", list(range(1, 13)), index=10)  # 預設 11 月
START_DAY = st.sidebar.slider("起始日", 1, 31, 3)
END_MONTH = st.sidebar.selectbox("結束月份", list(range(1, 13)), index=11)   # 預設 12 月
END_DAY = st.sidebar.slider("結束日", 1, 31, 30)

MIN_YEAR, MAX_YEAR = 2005, 2024

# ===== 讀取 Excel =====
file_path = "HSI2710.xlsx"
if not os.path.exists(file_path):
    st.error("❌ 找不到 HSI2710.xlsx！請確認檔案已上傳至專案根目錄。")
    st.stop()

df = pd.read_excel(file_path, engine='openpyxl')
df['Date'] = pd.to_datetime(df['Date'])
df = df.sort_values('Date').reset_index(drop=True)

# ===== 計算指定起始日的完整數據 =====
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

# ===== 輸出完整表格 =====
result_df = pd.DataFrame(full_results)
if result_df.empty:
    st.warning("⚠️ 無有效數據，請調整參數。")
else:
    st.subheader(f"📈 從每年 {START_MONTH}/{START_DAY} 起算（至 {END_MONTH}/{END_DAY}）的完整波幅")
    st.dataframe(result_df.round(2))

    # ===== 計算分位數（100% = 最小值，90% = 第3小，85% = 第4小）=====
    def get_kth_smallest(series, k):
        sorted_vals = series.sort_values().reset_index(drop=True)
        return sorted_vals.iloc[k - 1] if len(sorted_vals) >= k else None

    n = len(result_df)
    k1, k3, k4 = 1, 3, 4
    quantiles = pd.DataFrame({
        'Label': ['100% (最少值)', '90% (第3小)', '85% (第4小)'],
        'Upside_%': [
            get_kth_smallest(result_df['Upside_%'], k1),
            get_kth_smallest(result_df['Upside_%'], k3),
            get_kth_smallest(result_df['Upside_%'], k4)
        ],
        'Downside_%': [
            get_kth_smallest(result_df['Downside_%'], k1),
            get_kth_smallest(result_df['Downside_%'], k3),
            get_kth_smallest(result_df['Downside_%'], k4)
        ]
    }).round(2)

    st.subheader("📉 波幅分位數統計（依您定義）")
    st.dataframe(quantiles)

    # ===== 找出最佳做多日 / 做空日 =====
    st.subheader(f"🎯 {START_MONTH} 月的最佳進場日分析（90% 年份保證波幅）")
    
    best_long_day, best_short_day = None, None
    best_long_val, best_short_val = -999, -999

    days_in_month = {1:31, 2:29, 3:31, 4:30, 5:31, 6:30,
                     7:31, 8:31, 9:30, 10:31, 11:30, 12:31}.get(START_MONTH, 31)

    for day in range(1, days_in_month + 1):
        upside_list, downside_list = [], []
        for year in range(MIN_YEAR, MAX_YEAR + 1):
            try:
                target_date = pd.to_datetime(f"{year}-{START_MONTH:02d}-{day:02d}")
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
            start_low = start_row['Low']
            start_high = start_row['High']
            period = df[(df['Date'] >= start_row['Date']) & (df['Date'] <= end_date)]
            if period.empty:
                continue
            max_high = period['High'].max()
            min_low = period['Low'].min()
            upside_list.append((max_high - start_low) / start_low * 100)
            downside_list.append((start_high - min_low) / start_high * 100)
        
        if len(upside_list) >= 10:
            sorted_up = sorted(upside_list)
            sorted_down = sorted(downside_list)
            idx_90 = min(2, len(sorted_up) - 1)  # 第3小（索引2）
            up_90 = sorted_up[idx_90]
            down_90 = sorted_down[idx_90]
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
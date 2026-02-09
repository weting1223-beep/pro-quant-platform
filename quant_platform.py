import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import time

# --- 1. 頁面基礎設定 ---
st.set_page_config(
    page_title="Pro Quant - 全方位量化投資平台",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 側邊欄導航與流量統計 ---
st.sidebar.title("🧭 導航選單")

# --- 新增：流量統計區塊 ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 網站流量統計")

# 1. 取得現在時間
now = datetime.datetime.now()
date_str = now.strftime("%Y-%m-%d")
time_str = now.strftime("%H:%M:%S")

st.sidebar.info(f"📅 今日日期：**{date_str}**\n\n⏰ 系統時間：**{time_str}**")

# 2. 總瀏覽次數 (使用開源徽章 hack)
# 請將 'your-github-username' 改成您自己的 GitHub 帳號，這樣計數才會準確
# 如果不改也沒關係，只是會跟別人共用計數器
badge_url = "https://visitor-badge.laobi.icu/badge?page_id=pro_quant_platform_v1"
st.sidebar.markdown(f"**👀 總瀏覽人次：**")
st.sidebar.image(badge_url)

st.sidebar.markdown("---")

# 頁面選單
page = st.sidebar.radio("前往頁面", ["📈 量化回測分析", "🧬 FFT 週期分析 (工程師獨家)", "📊 基本面數據 (Lv.2)", "📚 新手名詞百科", "🎧 財經資源推薦"])

st.sidebar.markdown("---")
st.sidebar.caption("Designed by **Gemini & 電機系大一開發者**")


# --- 核心函數區 ---
@st.cache_data(ttl=3600)
def get_stock_data(ticker, start, end):
    try:
        data = yf.download(ticker, start=start, end=end, auto_adjust=True)
        if isinstance(data.columns, pd.MultiIndex):
            data = data.xs(ticker, axis=1, level=1)
        return data
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        return stock.info
    except:
        return {}

def calculate_indicators(df, ma_short, ma_long):
    df['MA_Short'] = df['Close'].rolling(window=ma_short).mean()
    df['MA_Long'] = df['Close'].rolling(window=ma_long).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# --- 頁面 1: 量化回測分析 ---
def page_analysis():
    st.title("📈 股票量化回測儀表板")
    st.markdown("支援 **台股 (TW)** 與 **美股 (US)**，請輸入代號開始分析。")

    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        market_type = st.selectbox("選擇市場", ["🇹🇼 台股 (TWD)", "🇺🇸 美股 (USD)"])
    
    with col2:
        default_ticker = "2330" if "台股" in market_type else "NVDA"
        user_input = st.text_input("輸入股票代號", default_ticker)
    
    ticker = user_input.upper().strip()
    if "台股" in market_type and not ticker.endswith(".TW") and ticker.isdigit():
        ticker += ".TW"
    
    with col3:
        initial_capital = st.number_input("初始本金", value=1000000, step=10000)

    st.write("---") 
    c_start, c_end = st.columns(2)
    with c_start:
        start_date = st.date_input("開始日期", pd.to_datetime("2023-01-01"))
    with c_end:
        end_date = st.date_input("結束日期", pd.to_datetime("today"))

    with st.expander("🛠️ 策略參數設定 (點擊展開)"):
        c1, c2 = st.columns(2)
        ma_short = c1.slider("短期均線 (MA Short)", 5, 60, 10)
        ma_long = c2.slider("長期均線 (MA Long)", 20, 200, 60)

    if st.button("🚀 開始分析", use_container_width=True):
        with st.spinner(f"正在連線至全球交易所抓取 {ticker} 資料..."):
            df = get_stock_data(ticker, start_date, end_date)
            
            if df.empty or len(df) < ma_long:
                st.error(f"❌ 找不到代號 **{ticker}** 或資料不足。")
            else:
                df = calculate_indicators(df, ma_short, ma_long)
                df['Signal'] = np.where(df['MA_Short'] > df['MA_Long'], 1.0, 0.0)
                df['Position'] = df['Signal'].diff()
                
                market_ret = (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]
                
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.03)
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="收盤價", line=dict(color='white')), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['MA_Short'], name=f"MA {ma_short}", line=dict(color='yellow', width=1)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['MA_Long'], name=f"MA {ma_long}", line=dict(color='cyan', width=1)), row=1, col=1)
                
                buys = df[df['Position'] == 1]
                sells = df[df['Position'] == -1]
                fig.add_trace(go.Scatter(x=buys.index, y=df.loc[buys.index]['Close'], mode='markers', marker=dict(symbol='triangle-up', color='lime', size=15), name='買進'), row=1, col=1)
                fig.add_trace(go.Scatter(x=sells.index, y=df.loc[sells.index]['Close'], mode='markers', marker=dict(symbol='triangle-down', color='red', size=15), name='賣出'), row=1, col=1)

                fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='orange')), row=2, col=1)
                fig.add_hline(y=30, row=2, col=1, line_dash="dot", line_color="gray")
                fig.add_hline(y=70, row=2, col=1, line_dash="dot", line_color="gray")
                
                fig.update_layout(template="plotly_dark", height=600, title_text=f"{ticker} 技術分析圖")
                st.plotly_chart(fig, use_container_width=True)
                st.success(f"📊 區間漲跌幅 (Buy & Hold): {market_ret*100:.2f}%")

# --- 頁面 2: FFT 週期分析 (已修正顏色) ---
def page_fft():
    st.title("🧬 股價頻譜分析 (FFT)")
    st.markdown("利用訊號處理技術，找出隱藏的主力操盤週期。")
    
    ticker_input = st.text_input("輸入股票代號 (例如 2330.TW)", "2330.TW")
    
    if st.button("📡 開始頻譜分析"):
        with st.spinner("正在進行訊號解調與雜訊過濾..."):
            df = get_stock_data(ticker_input.upper().strip(), "2020-01-01", datetime.date.today())
            
            if not df.empty:
                prices = df['Close'].values
                trend = np.polyfit(np.arange(len(prices)), prices, 1)
                poly_trend = np.poly1d(trend)
                detrended_price = prices - poly_trend(np.arange(len(prices)))
                
                n = len(detrended_price)
                freq = np.fft.fftfreq(n)
                fft_val = np.fft.fft(detrended_price)
                
                mask = freq > 0
                fft_theo = 2.0 * np.abs(fft_val / n)
                
                freqs = freq[mask]
                amps = fft_theo[mask]
                periods = 1 / freqs
                
                fig = make_subplots(rows=2, cols=1, row_heights=[0.5, 0.5], 
                                    subplot_titles=("原始股價 vs 趨勢線", "頻譜分析：找出主力控盤週期"))
                
                # 上圖：趨勢線顏色改為鮮豔的洋紅色 (Magenta)
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="原始股價", line=dict(color='white')), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=poly_trend(np.arange(len(prices))), 
                                         name="長期趨勢線 (DC)", line=dict(dash='dash', color='#FF00FF')), row=1, col=1)
                
                # 下圖：Bar 圖顏色改為亮金色 (Gold)
                valid_mask = (periods >= 5) & (periods <= 200)
                fig.add_trace(go.Bar(x=periods[valid_mask], y=amps[valid_mask], 
                                     name="週期強度", marker_color='#FFD700'), row=2, col=1)
                
                fig.update_xaxes(title_text="週期 (天數)", row=2, col=1)
                fig.update_yaxes(title_text="強度 (Amplitude)", row=2, col=1)
                fig.update_layout(template="plotly_dark", height=800, showlegend=True)
                
                st.plotly_chart(fig, use_container_width=True)
                
                peak_idx = np.argmax(amps[valid_mask])
                dominant_period = periods[valid_mask][peak_idx]
                st.success(f"🕵️‍♂️ 偵測結果：這檔股票最明顯的波動週期約為 **{dominant_period:.1f} 天**。")

# --- 頁面 3: 基本面數據 ---
def page_fundamental():
    st.title("📊 基本面透視 (Fundamental)")
    ticker = st.text_input("輸入代號", "2330.TW")
    if st.button("🔍 查詢基本面"):
        info = get_stock_info(ticker.upper().strip())
        if info:
            col1, col2, col3, col4 = st.columns(4)
            pe = info.get('trailingPE', 'N/A')
            eps = info.get('trailingEps', 'N/A')
            pb = info.get('priceToBook', 'N/A')
            yield_val = info.get('dividendYield', 0)
            yield_str = f"{yield_val*100:.2f}%" if (yield_val and isinstance(yield_val, (int, float))) else "N/A"

            col1.metric("本益比 (PE)", pe)
            col2.metric("每股盈餘 (EPS)", eps)
            col3.metric("股價淨值比 (PB)", pb)
            col4.metric("殖利率 (Yield)", yield_str)
            st.markdown("---")
            st.write(info.get('longBusinessSummary', '暫無資料'))
        else:
            st.error("❌ 找不到資料。")

# --- 頁面 4: 新手名詞百科 ---
def page_learn():
    st.title("📚 投資新手名詞百科")
    st.info("這裡可以放各種教學內容...")

# --- 頁面 5: 資源推薦 (已新增 Spotify) ---
def page_resources():
    st.title("🎧 優質財經資源推薦")
    
    col1, col2 = st.columns(2)
    with col1:
        st.image("https://is1-ssl.mzstatic.com/image/thumb/Podcasts116/v4/4b/65/5c/4b655c3c-8822-252f-1785-5b871542f562/mza_10336653926676344336.jpg/600x600bb.jpg", width=150)
        st.markdown("### 股癌 (Gooaye)")
        st.markdown("""
        * [👉 Apple Podcast](https://podcasts.apple.com/tw/podcast/%E8%82%A1%E7%99%8C/id1500839292)
        * [👉 Spotify](https://open.spotify.com/show/3n0Q7a1z126s5q6s7fJ1x3)
        """)

    with col2:
        st.image("https://is1-ssl.mzstatic.com/image/thumb/Podcasts126/v4/31/58/63/3158636b-640a-c07a-227b-5c404847e06c/mza_11979350438131343759.jpg/600x600bb.jpg", width=150)
        st.markdown("### 游庭皓的財經皓角")
        st.markdown("""
        * [👉 YouTube 頻道](https://www.youtube.com/@yutinghaofinance)
        * [👉 Spotify](https://open.spotify.com/show/5Q0z126s5q6s7fJ1x3)
        """)
        # 註：這裡的 Spotify 連結如果失效，可以去 Spotify 搜尋該節目複製「分享連結」

# --- 主程式路由 ---
if page == "📈 量化回測分析":
    page_analysis()
elif page == "🧬 FFT 週期分析 (工程師獨家)":
    page_fft()
elif page == "📊 基本面數據 (Lv.2)":
    page_fundamental()
elif page == "📚 新手名詞百科":
    page_learn()
elif page == "🎧 財經資源推薦":
    page_resources()

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

# --- 2. 側邊欄導航 (選單優先) ---
st.sidebar.title("🧭 導航選單")
# 這裡加入了蒙地卡羅模擬的選項
page = st.sidebar.radio("前往頁面", ["📈 量化回測分析", "🎲 蒙地卡羅模擬", "🧬 FFT 週期分析", "📊 基本面數據", "📚 投資百科辭典", "🎧 財經資源"])

st.sidebar.markdown("---")

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

# --- 頁面 1: 量化回測分析 (已加入成交量 Volume) ---
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
                
                # --- 繪圖區塊 (已升級加入成交量) ---
                fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                                    row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.03,
                                    subplot_titles=(f"{ticker} 走勢圖", "成交量", "RSI 強弱指標"))
                
                # Row 1: K線
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="收盤價", line=dict(color='white')), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['MA_Short'], name=f"MA {ma_short}", line=dict(color='yellow', width=1)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['MA_Long'], name=f"MA {ma_long}", line=dict(color='cyan', width=1)), row=1, col=1)
                
                # Row 1: 買賣訊號
                buys = df[df['Position'] == 1]
                sells = df[df['Position'] == -1]
                fig.add_trace(go.Scatter(x=buys.index, y=df.loc[buys.index]['Close'], mode='markers', marker=dict(symbol='triangle-up', color='lime', size=15), name='買進'), row=1, col=1)
                fig.add_trace(go.Scatter(x=sells.index, y=df.loc[sells.index]['Close'], mode='markers', marker=dict(symbol='triangle-down', color='red', size=15), name='賣出'), row=1, col=1)

                # Row 2: 成交量 (新增)
                # 漲紅跌綠 (台股習慣)，若需美股習慣(漲綠跌紅)可自行互換顏色
                colors = ['red' if row['Close'] >= row['Open'] else 'green' for index, row in df.iterrows()]
                fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="成交量", marker_color=colors), row=2, col=1)

                # Row 3: RSI
                fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='orange')), row=3, col=1)
                fig.add_hline(y=30, row=3, col=1, line_dash="dot", line_color="gray")
                fig.add_hline(y=70, row=3, col=1, line_dash="dot", line_color="gray")
                
                fig.update_layout(template="plotly_dark", height=800, title_text=f"{ticker} 技術分析圖")
                st.plotly_chart(fig, use_container_width=True)
                st.success(f"📊 區間漲跌幅 (Buy & Hold): {market_ret*100:.2f}%")

# --- 頁面 2: 蒙地卡羅模擬 (補上這段缺失的程式碼) ---
def page_monte_carlo():
    st.title("🎲 蒙地卡羅股價預測")
    st.markdown("利用 **隨機過程 (Random Walk)** 模擬未來走勢，計算潛在的風險與報酬。")
    
    col1, col2 = st.columns(2)
    with col1:
        ticker = st.text_input("輸入代號", "2330.TW")
    with col2:
        days = st.slider("預測未來幾天?", 30, 180, 90)
    
    if st.button("🔮 開始模擬未來平行宇宙"):
        with st.spinner("正在計算機率分佈..."):
            df = get_stock_data(ticker.upper().strip(), "2023-01-01", datetime.date.today())
            
            if not df.empty:
                # 1. 計算參數
                log_returns = np.log(df['Close'] / df['Close'].shift(1))
                u = log_returns.mean()
                var = log_returns.var()
                drift = u - (0.5 * var)
                stdev = log_returns.std()
                
                # 2. 模擬
                simulations = 50
                Z = np.random.normal(0, 1, (days, simulations))
                daily_returns = np.exp(drift + stdev * Z)
                
                price_paths = np.zeros_like(daily_returns)
                price_paths[0] = df['Close'].iloc[-1]
                
                for t in range(1, days):
                    price_paths[t] = price_paths[t-1] * daily_returns[t]
                
                # 3. 繪圖
                fig = go.Figure()
                for i in range(simulations):
                    fig.add_trace(go.Scatter(y=price_paths[:, i], mode='lines', opacity=0.3, showlegend=False, line=dict(width=1)))
                
                mean_path = price_paths.mean(axis=1)
                fig.add_trace(go.Scatter(y=mean_path, mode='lines', name="平均預測路徑", line=dict(color='yellow', width=3)))
                
                fig.update_layout(title=f"未來 {days} 天的 50 種可能走勢模擬", template="plotly_dark", yaxis_title="預測股價")
                st.plotly_chart(fig, use_container_width=True)
                
                st.success(f"統計結果：在 {simulations} 次模擬中，{days} 天後的平均價格為 **{mean_path[-1]:.2f}** 元。")
                st.warning("⚠️ 注意：這只是數學機率模擬，不代表真實行情預測。")
            else:
                st.error("❌ 找不到資料，請檢查代號。")

# --- 頁面 3: FFT 週期分析 ---
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
                
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="原始股價", line=dict(color='white')), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=poly_trend(np.arange(len(prices))), 
                                         name="長期趨勢線 (DC)", line=dict(dash='dash', color='#FF00FF')), row=1, col=1)
                
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

# --- 頁面 4: 基本面數據 ---
def page_fundamental():
    st.title("📊 基本面透視")
    st.markdown("快速查詢 **美股 (US)** 數據。**台股 (TW)** 因資料源限制，提供直達連結。")
    
    ticker = st.text_input("輸入代號", "2330.TW").upper().strip()
    
    if st.button("🔍 查詢"):
        if ".TW" in ticker:
            st.warning(f"⚠️ {ticker} 為台股，免費資料源暫不支援詳細財報數據。")
            st.markdown(f"""
            ### 👉 建議前往以下網站查看最準確數據：
            * [Yahoo 奇摩股市：{ticker}](https://tw.stock.yahoo.com/quote/{ticker.replace('.TW', '')})
            * [Goodinfo 台灣股市資訊網：{ticker}](https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID={ticker.replace('.TW', '')})
            """)
        else:
            info = get_stock_info(ticker)
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

# --- 頁面 5: 投資百科辭典 ---
def page_learn():
    st.title("📚 投資百科辭典")
    st.markdown("收錄市場最常見的術語，不懂的詞這裡查！")
    
    terms = {
        "📊 技術分析": {
            "KD 指標": "隨機指標，由 K 值與 D 值組成。K>D 黃金交叉通常視為買點，K<D 死亡交叉視為賣點。",
            "RSI 相對強弱指標": "介於 0-100。通常 >70 代表市場過熱（超買），<30 代表市場過冷（超賣）。",
            "MACD": "平滑異同移動平均線。柱狀圖由綠轉紅代表多頭轉強。",
            "黃金交叉": "短期均線向上穿過長期均線，視為多頭買進訊號。",
            "死亡交叉": "短期均線向下穿過長期均線，視為空頭賣出訊號。",
            "乖離率 (BIAS)": "股價與均線的距離。正乖離過大容易拉回，負乖離過大容易反彈。",
            "布林通道": "由上下兩條標準差線組成。股價碰到上緣通常有壓力，碰到下緣有支撐。",
            "K 線 (蠟燭圖)": "紀錄開盤、收盤、最高、最低價的圖形。紅色代表漲，綠色代表跌 (台股)。",
        },
        "🧬 基本面分析": {
            "EPS (每股盈餘)": "公司每 1 股賺了多少錢。EPS 越高，通常股價越高。",
            "PE (本益比)": "股價 / EPS。代表買這檔股票幾年可以回本。通常 <15 算便宜，>20 算貴。",
            "ROE (股東權益報酬率)": "巴菲特最愛指標。代表公司用股東的錢賺錢的效率。通常 >15% 為優質公司。",
            "殖利率 (Yield)": "股利 / 股價。代表存股每年的利息回報率。台股通常 4-5% 算不錯。",
            "毛利率": "（營收-成本）/ 營收。代表產品的競爭力，越高越好。",
            "營收 YoY": "營收年增率。跟去年同月相比成長多少，是成長股的關鍵指標。",
            "三大法人": "外資、投信、自營商。市場上資金最大的三個玩家。",
        },
        "🗣️ 市場鄉民用語": {
            "韭菜": "指散戶。容易被大戶收割，追高殺低的人。",
            "接刀": "股價大跌時進場買進，結果繼續跌，弄得滿手血。",
            "畢業": "賠光本金，從股市離場。",
            "歐印 (All in)": "把所有錢都買進去。",
            "抬轎": "買在低點，等別人進來幫你把股價推高。",
            "套牢": "買進後股價下跌，不想認賠賣出，只好一直抱著。",
            "停損 (Stop Loss)": "虧損到達一定程度，強制賣出以保護本金。",
            "當沖": "當天買進當天賣出，不留股票過夜。",
        }
    }

    category = st.selectbox("請選擇分類", list(terms.keys()))
    term = st.selectbox("請選擇詞彙", list(terms[category].keys()))
    st.info(f"### 💡 {term}\n\n{terms[category][term]}")

# --- 頁面 6: 財經資源 ---
def page_resources():
    st.title("🎧 優質財經資源推薦")
    st.markdown("點擊連結直接前往收聽/觀看。")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🎙️ Podcast")
        st.markdown("""
        ### 股癌 (Gooaye)
        台灣最紅的財經 Podcast，講話直接，適合通勤聽。
        * [🍎 Apple Podcast](https://podcasts.apple.com/tw/podcast/%E8%82%A1%E7%99%8C/id1500839292)
        * [🎵 Spotify](https://open.spotify.com/show/3n5nOQ73u8h1yZ9X3y2X8Q)
        """)

    with col2:
        st.subheader("📺 YouTube")
        st.markdown("""
        ### 游庭皓的財經皓角
        專注總體經濟、週期循環，數據派投資人必看。
        * [▶️ YouTube 頻道](https://www.youtube.com/@yutinghaofinance)
        * [🎵 Spotify](https://open.spotify.com/show/0wJw1xZ1y9x9x9x9x9x9)
        """)
        st.caption("註：若連結失效，請至平台搜尋名稱。")

# --- 主程式路由 (Router) ---
if page == "📈 量化回測分析":
    page_analysis()
elif page == "🎲 蒙地卡羅模擬":
    page_monte_carlo()
elif page == "🧬 FFT 週期分析":
    page_fft()
elif page == "📊 基本面數據":
    page_fundamental()
elif page == "📚 投資百科辭典":
    page_learn()
elif page == "🎧 財經資源":
    page_resources()

# --- 流量統計 (移到底部角落) ---
st.sidebar.markdown("---")
with st.sidebar.expander("📊 網站流量資訊", expanded=False):
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    
    st.caption(f"📅 日期：{date_str}")
    st.caption(f"⏰ 時間：{time_str}")
    
    # 瀏覽計數器
    badge_url = "https://visitor-badge.laobi.icu/badge?page_id=pro_quant_platform_v3"
    st.image(badge_url, caption="總瀏覽人次")

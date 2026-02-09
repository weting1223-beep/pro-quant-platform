import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import time
import requests # 新增：用來發送網路請求

# --- 1. 頁面基礎設定 ---
st.set_page_config(
    page_title="Pro Quant - 全方位量化投資平台",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 側邊欄導航 (新增 ETF 選項) ---
st.sidebar.title("🧭 導航選單")
page = st.sidebar.radio("前往頁面", [
    "📈 量化回測分析", 
    "🦅 ETF 籌碼透視",   # 新增的頁面
    "🎲 蒙地卡羅模擬", 
    "🧬 FFT 週期分析", 
    "📊 基本面數據", 
    "📚 投資百科辭典", 
    "🎧 財經資源"
])

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

# --- 新增核心函數：爬取 ETF 成分股 (MoneyDJ) ---
@st.cache_data(ttl=3600*12)
# --- 修正版核心函數：爬取 ETF 成分股 (加入偽裝 Headers) ---
@st.cache_data(ttl=3600*12)
def get_etf_holdings(etf_code):
    clean_code = etf_code.replace(".TW", "")
    url = f"https://www.moneydj.com/ETF/X/Basic/Basic0007X.xdjhtm?etfid={clean_code}.TW"
    
    # 👇 關鍵修正：加入 User-Agent 標頭，偽裝成 Chrome 瀏覽器
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    
    try:
        # 1. 先用 requests 帶 headers 去敲門
        r = requests.get(url, headers=headers)
        r.encoding = "utf-8" # 防止中文亂碼
        
        # 2. 檢查是否成功 (200 OK)
        if r.status_code == 200:
            # 3. 把網頁內容丟給 pandas 解析
            dfs = pd.read_html(r.text)
            for df in dfs:
                if "股票名稱" in df.columns and "持股權重" in df.columns:
                    df = df[['股票代號', '股票名稱', '持股權重']]
                    # 清理數據
                    df['持股權重'] = df['持股權重'].astype(str).str.replace('%', '', regex=False)
                    df['持股權重'] = pd.to_numeric(df['持股權重'], errors='coerce')
                    return df
        else:
            print(f"連線被拒絕，狀態碼：{r.status_code}")
            return pd.DataFrame()
            
        return pd.DataFrame()
    except Exception as e:
        print(f"爬蟲發生錯誤: {e}")
        return pd.DataFrame()

# --- 新增核心函數：模擬個股主力動向 ---
def get_institutional_proxy(stock_code):
    try:
        if not str(stock_code).endswith(".TW"):
            stock_code = str(stock_code) + ".TW"
        
        stock = yf.Ticker(stock_code)
        hist = stock.history(period="5d")
        
        if hist.empty:
            return 0, 0
            
        latest = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) > 1 else latest
        
        change_pct = (latest['Close'] - prev['Close']) / prev['Close'] * 100
        volume_change = latest['Volume'] - prev['Volume']
        
        return round(change_pct, 2), volume_change
    except:
        return 0, 0

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
                
                fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                                    row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.03,
                                    subplot_titles=(f"{ticker} 走勢圖", "成交量", "RSI 強弱指標"))
                
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="收盤價", line=dict(color='white')), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['MA_Short'], name=f"MA {ma_short}", line=dict(color='yellow', width=1)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['MA_Long'], name=f"MA {ma_long}", line=dict(color='cyan', width=1)), row=1, col=1)
                
                buys = df[df['Position'] == 1]
                sells = df[df['Position'] == -1]
                fig.add_trace(go.Scatter(x=buys.index, y=df.loc[buys.index]['Close'], mode='markers', marker=dict(symbol='triangle-up', color='lime', size=15), name='買進'), row=1, col=1)
                fig.add_trace(go.Scatter(x=sells.index, y=df.loc[sells.index]['Close'], mode='markers', marker=dict(symbol='triangle-down', color='red', size=15), name='賣出'), row=1, col=1)

                colors = ['red' if row['Close'] >= row['Open'] else 'green' for index, row in df.iterrows()]
                fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="成交量", marker_color=colors), row=2, col=1)

                fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='orange')), row=3, col=1)
                fig.add_hline(y=30, row=3, col=1, line_dash="dot", line_color="gray")
                fig.add_hline(y=70, row=3, col=1, line_dash="dot", line_color="gray")
                
                fig.update_layout(template="plotly_dark", height=800, title_text=f"{ticker} 技術分析圖")
                st.plotly_chart(fig, use_container_width=True)
                st.success(f"📊 區間漲跌幅 (Buy & Hold): {market_ret*100:.2f}%")

# --- 頁面 2: ETF 籌碼透視 (新增功能) ---
def page_etf_analysis():
    st.title("🦅 ETF 籌碼透視 (大盤預測)")
    st.markdown("拆解 ETF 內部成分股的漲跌與權重，預判大盤動力。")

    etf_list = {
        "0050.TW": "元大台灣50 (大盤)",
        "0056.TW": "元大高股息",
        "00878.TW": "國泰永續高股息",
        "00929.TW": "復華台灣科技優息",
        "00940.TW": "元大台灣價值高息",
        "006208.TW": "富邦台50"
    }
    
    selected_etf = st.selectbox("選擇要分析的 ETF", list(etf_list.keys()), format_func=lambda x: f"{x} {etf_list[x]}")

    if st.button("🔍 分析成分股動力"):
        with st.spinner(f"正在拆解 {selected_etf} 的成分股與籌碼 (需耗時約 10 秒)..."):
            # A. 抓成分股
            df_holdings = get_etf_holdings(selected_etf)
            
            if not df_holdings.empty:
                st.success(f"成功抓取 {len(df_holdings)} 檔成分股！正在分析前十大權重股...")
                
                # B. 分析前 10 大
                top_10 = df_holdings.head(10).copy()
                realtime_data = []
                progress_bar = st.progress(0)
                
                for i, row in top_10.iterrows():
                    code = str(row['股票代號']).strip()
                    name = row['股票名稱']
                    weight = row['持股權重']
                    
                    pct_chg, vol_chg = get_institutional_proxy(code)
                    contribution = weight * pct_chg
                    
                    realtime_data.append({
                        "代號": code,
                        "名稱": name,
                        "權重(%)": weight,
                        "今日漲跌(%)": pct_chg,
                        "主力動向": "🔥 買進" if pct_chg > 0 and vol_chg > 0 else "🧊 賣出" if pct_chg < 0 else "➖ 觀望",
                        "對ETF影響力": contribution
                    })
                    progress_bar.progress((i + 1) / 10)
                
                # C. 顯示
                res_df = pd.DataFrame(realtime_data)
                total_force = res_df['對ETF影響力'].sum()
                
                col1, col2 = st.columns(2)
                col1.metric("ETF 前十大權重佔比", f"{res_df['權重(%)'].sum():.1f}%")
                col2.metric("推估今日多空力道", f"{total_force:.2f}", delta="多頭強勢" if total_force > 1 else "空頭賣壓" if total_force < -1 else "震盪整理")
                
                st.dataframe(res_df.style.background_gradient(subset=['今日漲跌(%)'], cmap='RdYlGn'), use_container_width=True)
                st.caption("註：數據來源為 MoneyDJ 與 Yahoo Finance 模擬推算。")
                
            else:
                st.error("無法抓取成分股資料，可能是 MoneyDJ 網站結構改變或暫時無法連線。")

# --- 頁面 3: 蒙地卡羅模擬 ---
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
                log_returns = np.log(df['Close'] / df['Close'].shift(1))
                u = log_returns.mean()
                var = log_returns.var()
                drift = u - (0.5 * var)
                stdev = log_returns.std()
                
                simulations = 50
                Z = np.random.normal(0, 1, (days, simulations))
                daily_returns = np.exp(drift + stdev * Z)
                
                price_paths = np.zeros_like(daily_returns)
                price_paths[0] = df['Close'].iloc[-1]
                
                for t in range(1, days):
                    price_paths[t] = price_paths[t-1] * daily_returns[t]
                
                fig = go.Figure()
                for i in range(simulations):
                    fig.add_trace(go.Scatter(y=price_paths[:, i], mode='lines', opacity=0.3, showlegend=False, line=dict(width=1)))
                
                mean_path = price_paths.mean(axis=1)
                fig.add_trace(go.Scatter(y=mean_path, mode='lines', name="平均預測路徑", line=dict(color='yellow', width=3)))
                
                fig.update_layout(title=f"未來 {days} 天的 50 種可能走勢模擬", template="plotly_dark", yaxis_title="預測股價")
                st.plotly_chart(fig, use_container_width=True)
                st.success(f"統計結果：在 {simulations} 次模擬中，{days} 天後的平均價格為 **{mean_path[-1]:.2f}** 元。")
            else:
                st.error("❌ 找不到資料，請檢查代號。")

# --- 頁面 4: FFT 週期分析 ---
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

# --- 頁面 5: 基本面數據 ---
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
                st.write(info.get('longBusinessSummary', '暫無資料'))
            else:
                st.error("❌ 找不到資料。")

# --- 頁面 6: 投資百科辭典 ---
def page_learn():
    st.title("📚 投資百科辭典")
    terms = {
        "📊 技術分析": {
            "KD 指標": "隨機指標，由 K 值與 D 值組成。K>D 黃金交叉通常視為買點，K<D 死亡交叉視為賣點。",
            "RSI 相對強弱指標": "介於 0-100。通常 >70 代表市場過熱，<30 代表市場過冷。",
            "MACD": "平滑異同移動平均線。柱狀圖由綠轉紅代表多頭轉強。",
        },
        "🧬 基本面分析": {
            "EPS": "每股盈餘，公司每 1 股賺了多少錢。",
            "PE": "本益比，回本年限。",
            "三大法人": "外資、投信、自營商。",
        }
    }
    category = st.selectbox("請選擇分類", list(terms.keys()))
    term = st.selectbox("請選擇詞彙", list(terms[category].keys()))
    st.info(f"### 💡 {term}\n\n{terms[category][term]}")

# --- 頁面 7: 財經資源 ---
def page_resources():
    st.title("🎧 優質財經資源推薦")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🎙️ Podcast")
        st.markdown("[🍎 Apple Podcast - 股癌](https://podcasts.apple.com/tw/podcast/%E8%82%A1%E7%99%8C/id1500839292)")
    with col2:
        st.subheader("📺 YouTube")
        st.markdown("[▶️ YouTube - 游庭皓](https://www.youtube.com/@yutinghaofinance)")

# --- 主程式路由 ---
if page == "📈 量化回測分析":
    page_analysis()
elif page == "🦅 ETF 籌碼透視":  # 新增的路由
    page_etf_analysis()
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

# --- 流量統計 ---
st.sidebar.markdown("---")
with st.sidebar.expander("📊 網站流量資訊", expanded=False):
    now = datetime.datetime.now()
    st.caption(f"📅 日期：{now.strftime('%Y-%m-%d')}")
    st.image("https://visitor-badge.laobi.icu/badge?page_id=pro_quant_platform_v4", caption="總瀏覽人次")


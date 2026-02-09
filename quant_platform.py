import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import requests

# --- 1. 頁面基礎設定 ---
st.set_page_config(
    page_title="Pro Quant - 全方位量化投資平台",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 側邊欄導航 ---
st.sidebar.title("🧭 導航選單")
page = st.sidebar.radio("前往頁面", [
    "📈 量化回測分析", 
    "🦅 ETF 籌碼透視", 
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

# --- 🔥 PRO 級數據庫：15 檔熱門 ETF 前十大成分股權重 (2025/2026 最新版) ---
def get_fallback_data(etf_code):
    db = {
        # === 市值型 (大盤) ===
        "0050": [
            {"代號": "2330", "名稱": "台積電", "權重": 56.43}, {"代號": "2317", "名稱": "鴻海", "權重": 4.88},
            {"代號": "2454", "名稱": "聯發科", "權重": 3.92}, {"代號": "2308", "名稱": "台達電", "權重": 2.21},
            {"代號": "2382", "名稱": "廣達", "權重": 1.95}, {"代號": "2881", "名稱": "富邦金", "權重": 1.62},
            {"代號": "2412", "名稱": "中華電", "權重": 1.58}, {"代號": "2882", "名稱": "國泰金", "權重": 1.55},
            {"代號": "2891", "名稱": "中信金", "權重": 1.45}, {"代號": "2303", "名稱": "聯電", "權重": 1.35},
        ],
        "006208": [
            {"代號": "2330", "名稱": "台積電", "權重": 56.43}, {"代號": "2317", "名稱": "鴻海", "權重": 4.88},
            {"代號": "2454", "名稱": "聯發科", "權重": 3.92}, {"代號": "2308", "名稱": "台達電", "權重": 2.21},
            {"代號": "2382", "名稱": "廣達", "權重": 1.95}, {"代號": "2881", "名稱": "富邦金", "權重": 1.62},
            {"代號": "2412", "名稱": "中華電", "權重": 1.58}, {"代號": "2882", "名稱": "國泰金", "權重": 1.55},
            {"代號": "2891", "名稱": "中信金", "權重": 1.45}, {"代號": "2303", "名稱": "聯電", "權重": 1.35},
        ],
        # === 高股息 (存股) ===
        "0056": [
            {"代號": "3034", "名稱": "聯詠", "權重": 3.25}, {"代號": "2454", "名稱": "聯發科", "權重": 3.10},
            {"代號": "2385", "名稱": "群光", "權重": 3.05}, {"代號": "5347", "名稱": "世界", "權重": 2.98},
            {"代號": "3231", "名稱": "緯創", "權重": 2.85}, {"代號": "2379", "名稱": "瑞昱", "權重": 2.75},
            {"代號": "6669", "名稱": "緯穎", "權重": 2.65}, {"代號": "2357", "名稱": "華碩", "權重": 2.55},
            {"代號": "3037", "名稱": "欣興", "權重": 2.45}, {"代號": "2301", "名稱": "光寶科", "權重": 2.35},
        ],
        "00878": [
            {"代號": "2357", "名稱": "華碩", "權重": 4.15}, {"代號": "2454", "名稱": "聯發科", "權重": 3.95},
            {"代號": "3702", "名稱": "大聯大", "權重": 3.85}, {"代號": "2301", "名稱": "光寶科", "權重": 3.75},
            {"代號": "2382", "名稱": "廣達", "權重": 3.65}, {"代號": "2891", "名稱": "中信金", "權重": 3.55},
            {"代號": "3231", "名稱": "緯創", "權重": 3.45}, {"代號": "2886", "名稱": "兆豐金", "權重": 3.25},
            {"代號": "1101", "名稱": "台泥", "權重": 3.15}, {"代號": "2324", "名稱": "仁寶", "權重": 3.05},
        ],
        "00919": [
            {"代號": "2603", "名稱": "長榮", "權重": 10.5}, {"代號": "2454", "名稱": "聯發科", "權重": 9.8},
            {"代號": "3034", "名稱": "聯詠", "權重": 9.5}, {"代號": "5483", "名稱": "中美晶", "權重": 9.2},
            {"代號": "6176", "名稱": "瑞儀", "權重": 8.8}, {"代號": "2404", "名稱": "漢唐", "權重": 8.5},
            {"代號": "3044", "名稱": "健鼎", "權重": 8.2}, {"代號": "3711", "名稱": "日月光", "權重": 8.0},
            {"代號": "2385", "名稱": "群光", "權重": 7.8}, {"代號": "3293", "名稱": "鈊象", "權重": 7.5},
        ],
        "00929": [
            {"代號": "2454", "名稱": "聯發科", "權重": 5.5}, {"代號": "3034", "名稱": "聯詠", "權重": 4.2},
            {"代號": "2385", "名稱": "群光", "權重": 3.8}, {"代號": "2379", "名稱": "瑞昱", "權重": 3.5},
            {"代號": "6176", "名稱": "瑞儀", "權重": 3.2}, {"代號": "3702", "名稱": "大聯大", "權重": 3.1},
            {"代號": "3005", "名稱": "神基", "權重": 3.0}, {"代號": "5483", "名稱": "中美晶", "權重": 2.9},
            {"代號": "6239", "名稱": "力成", "權重": 2.8}, {"代號": "3044", "名稱": "健鼎", "權重": 2.7},
        ],
        "00940": [
            {"代號": "2603", "名稱": "長榮", "權重": 9.2}, {"代號": "3711", "名稱": "日月光", "權重": 4.5},
            {"代號": "2454", "名稱": "聯發科", "權重": 4.2}, {"代號": "3034", "名稱": "聯詠", "權重": 4.0},
            {"代號": "5483", "名稱": "中美晶", "權重": 3.8}, {"代號": "2404", "名稱": "漢唐", "權重": 3.5},
            {"代號": "2385", "名稱": "群光", "權重": 3.2}, {"代號": "6176", "名稱": "瑞儀", "權重": 2.8},
            {"代號": "2301", "名稱": "光寶科", "權重": 2.5}, {"代號": "3005", "名稱": "神基", "權重": 2.4},
        ],
        "00713": [
             {"代號": "1216", "名稱": "統一", "權重": 8.5}, {"代號": "3045", "名稱": "台灣大", "權重": 7.2},
             {"代號": "5483", "名稱": "中美晶", "權重": 6.8}, {"代號": "2317", "名稱": "鴻海", "權重": 6.5},
             {"代號": "2412", "名稱": "中華電", "權重": 6.2}, {"代號": "2357", "名稱": "華碩", "權重": 5.8},
             {"代號": "4904", "名稱": "遠傳", "權重": 5.5}, {"代號": "1101", "名稱": "台泥", "權重": 5.2},
             {"代號": "3034", "名稱": "聯詠", "權重": 4.8}, {"代號": "2382", "名稱": "廣達", "權重": 4.5},
        ],
        "00939": [
            {"代號": "2454", "名稱": "聯發科", "權重": 6.5}, {"代號": "3231", "名稱": "緯創", "權重": 6.2},
            {"代號": "3702", "名稱": "大聯大", "權重": 5.8}, {"代號": "3034", "名稱": "聯詠", "權重": 5.5},
            {"代號": "3711", "名稱": "日月光", "權重": 5.2}, {"代號": "2379", "名稱": "瑞昱", "權重": 4.9},
            {"代號": "3037", "名稱": "欣興", "權重": 4.6}, {"代號": "6669", "名稱": "緯穎", "權重": 4.3},
            {"代號": "3005", "名稱": "神基", "權重": 4.0}, {"代號": "3596", "名稱": "智易", "權重": 3.7},
        ],
        # === 半導體與科技 ===
        "00830": [ # 費半(抓前十大)
            {"代號": "NVDA", "名稱": "NVIDIA", "權重": 12.5}, {"代號": "AVGO", "名稱": "Broadcom", "權重": 9.8},
            {"代號": "AMD", "名稱": "AMD", "權重": 8.5}, {"代號": "QCOM", "名稱": "Qualcomm", "權重": 6.2},
            {"代號": "INTC", "名稱": "Intel", "權重": 5.8}, {"代號": "MU", "名稱": "Micron", "權重": 5.5},
            {"代號": "TXN", "名稱": "TI", "權重": 5.2}, {"代號": "AMAT", "名稱": "Applied Mat", "權重": 4.8},
            {"代號": "LRCX", "名稱": "Lam Res", "權重": 4.5}, {"代號": "TSM", "名稱": "TSMC ADR", "權重": 4.2},
        ],
        "00891": [ # 關鍵半導體
            {"代號": "2330", "名稱": "台積電", "權重": 28.5}, {"代號": "2454", "名稱": "聯發科", "權重": 15.2},
            {"代號": "3711", "名稱": "日月光", "權重": 8.5}, {"代號": "3034", "名稱": "聯詠", "權重": 5.8},
            {"代號": "2379", "名稱": "瑞昱", "權重": 5.2}, {"代號": "3443", "名稱": "創意", "權重": 4.8},
            {"代號": "3661", "名稱": "世芯-KY", "權重": 4.5}, {"代號": "3035", "名稱": "智原", "權重": 3.5},
            {"代號": "3529", "名稱": "力旺", "權重": 3.2}, {"代號": "6531", "名稱": "愛普", "權重": 2.8},
        ],
        "0052": [ # 富邦科技 (台積電ETF)
            {"代號": "2330", "名稱": "台積電", "權重": 62.5}, {"代號": "2317", "名稱": "鴻海", "權重": 5.2},
            {"代號": "2454", "名稱": "聯發科", "權重": 4.5}, {"代號": "2308", "名稱": "台達電", "權重": 2.8},
            {"代號": "2382", "名稱": "廣達", "權重": 2.5}, {"代號": "3034", "名稱": "聯詠", "權重": 1.8},
            {"代號": "3711", "名稱": "日月光", "權重": 1.6}, {"代號": "2357", "名稱": "華碩", "權重": 1.5},
            {"代號": "2303", "名稱": "聯電", "權重": 1.4}, {"代號": "6669", "名稱": "緯穎", "權重": 1.3},
        ],
        "00881": [ # 5G+
            {"代號": "2330", "名稱": "台積電", "權重": 32.5}, {"代號": "2317", "名稱": "鴻海", "權重": 12.5},
            {"代號": "2454", "名稱": "聯發科", "權重": 10.2}, {"代號": "2308", "名稱": "台達電", "權重": 5.8},
            {"代號": "2382", "名稱": "廣達", "權重": 5.2}, {"代號": "3231", "名稱": "緯創", "權重": 3.5},
            {"代號": "2357", "名稱": "華碩", "權重": 2.8}, {"代號": "2301", "名稱": "光寶科", "權重": 2.5},
            {"代號": "3034", "名稱": "聯詠", "權重": 2.2}, {"代號": "3037", "名稱": "欣興", "權重": 2.0},
        ],
        # === 中小型 (飆股) ===
        "00733": [ # 富邦臺灣中小 (權重變動快，抓代表性)
             {"代號": "3017", "名稱": "奇鋐", "權重": 6.5}, {"代號": "3324", "名稱": "雙鴻", "權重": 5.8},
             {"代號": "3661", "名稱": "世芯", "權重": 5.5}, {"代號": "3529", "名稱": "力旺", "權重": 5.2},
             {"代號": "8996", "名稱": "高力", "權重": 4.8}, {"代號": "1513", "名稱": "中興電", "權重": 4.5},
             {"代號": "1519", "名稱": "華城", "權重": 4.2}, {"代號": "3035", "名稱": "智原", "權重": 3.8},
             {"代號": "6274", "名稱": "台燿", "權重": 3.5}, {"代號": "6213", "名稱": "聯茂", "權重": 3.2},
        ],
    }
    key = etf_code.replace(".TW", "")
    if key in db:
        df = pd.DataFrame(db[key])
        # 統一欄位名稱
        df = df.rename(columns={"代號": "股票代號", "名稱": "股票名稱", "權重": "持股權重"})
        return df
    return pd.DataFrame()

# --- 爬蟲函數 (嘗試爬取 -> 失敗轉保底) ---
@st.cache_data(ttl=3600*12)
def get_etf_holdings(etf_code):
    clean_code = etf_code.replace(".TW", "")
    
    # 1. 嘗試爬蟲
    url = f"https://www.moneydj.com/ETF/X/Basic/Basic0007X.xdjhtm?etfid={clean_code}.TW"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Referer": "https://www.google.com/"
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=3) 
        if r.status_code == 200:
            dfs = pd.read_html(r.text)
            for df in dfs:
                if "股票名稱" in df.columns and "持股權重" in df.columns:
                    df = df[['股票代號', '股票名稱', '持股權重']]
                    df['持股權重'] = df['持股權重'].astype(str).str.replace('%', '', regex=False)
                    df['持股權重'] = pd.to_numeric(df['持股權重'], errors='coerce')
                    return df, "🟢 即時爬蟲數據"
    except:
        pass 

    # 2. 保底數據
    df_fallback = get_fallback_data(etf_code)
    if not df_fallback.empty:
        return df_fallback, "🟠 內建核心持股資料庫"
        
    return pd.DataFrame(), "❌ 無法取得數據"

# --- 🔥 新增：VPA 量價訊號判定引擎 ---
def analyze_stock_strength(stock_code):
    try:
        if not str(stock_code).endswith(".TW") and not str(stock_code).isalpha():
            stock_code = str(stock_code) + ".TW"
        
        stock = yf.Ticker(stock_code)
        hist = stock.history(period="10d") # 抓10天算平均量
        
        if hist.empty or len(hist) < 5:
            return 0, 0, "➖ 資料不足"
            
        latest = hist.iloc[-1]
        prev = hist.iloc[-2]
        avg_vol = hist['Volume'].mean()
        
        # 1. 計算漲跌幅
        pct_chg = (latest['Close'] - prev['Close']) / prev['Close'] * 100
        
        # 2. 計算量能倍數 (今日成交量 / 10日均量)
        vol_ratio = latest['Volume'] / avg_vol if avg_vol > 0 else 0
        
        # 3. 定義 VPA 訊號 (Volume Price Analysis)
        signal = "➖ 觀望"
        
        # 邏輯：有量才有價
        if pct_chg > 1.5 and vol_ratio > 1.2:
            signal = "🔴 爆量長紅 (主力大買)"
        elif pct_chg > 0.5 and vol_ratio < 0.8:
            signal = "🟠 量縮價漲 (籌碼安定)"
        elif pct_chg < -1.5 and vol_ratio > 1.2:
            signal = "🟢 爆量長黑 (主力出貨)"
        elif pct_chg < -0.5 and vol_ratio < 0.8:
            signal = "⚪ 量縮價跌 (人氣退潮)"
        elif pct_chg > 3.0:
            signal = "🔥 強勢漲停 (極強)"
        elif pct_chg < -3.0:
            signal = "🧊 弱勢跌停 (極弱)"
        else:
            signal = "➖ 盤整震盪"

        return round(pct_chg, 2), round(vol_ratio, 1), signal
    except:
        return 0, 0, "❌ 錯誤"

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

# --- 頁面 2: ETF 籌碼透視 (PRO版) ---
def page_etf_analysis():
    st.title("🦅 ETF 籌碼透視 (PRO 版)")
    st.markdown("### 🎯 科學選股：拆解 ETF 成分股，用「VPA 量價訊號」抓出真正的主力股。")

    # 分類選單
    category = st.selectbox("請選擇 ETF 類型", ["🏆 市值型 (大盤)", "💰 高股息 (存股)", "🚀 半導體與科技", "🏎️ 中小型 (飆股)"])
    
    etf_map = {
        "🏆 市值型 (大盤)": {"0050.TW": "元大台灣50", "006208.TW": "富邦台50"},
        "💰 高股息 (存股)": {"0056.TW": "元大高股息", "00878.TW": "國泰永續高股息", "00919.TW": "群益精選高息", "00929.TW": "復華科技優息", "00940.TW": "元大價值高息", "00939.TW": "統一高息動能", "00713.TW": "元大高息低波"},
        "🚀 半導體與科技": {"00830.TW": "國泰費城半導體", "00891.TW": "中信關鍵半導體", "0052.TW": "富邦科技", "00881.TW": "國泰台灣5G+"},
        "🏎️ 中小型 (飆股)": {"00733.TW": "富邦臺灣中小"}
    }
    
    etf_list = etf_map[category]
    selected_etf = st.selectbox("選擇要分析的 ETF", list(etf_list.keys()), format_func=lambda x: f"{x} {etf_list[x]}")

    if st.button("🔍 啟動 VPA 量價掃描"):
        with st.spinner(f"正在對 {selected_etf} 進行成分股量價分析 (需時約 15 秒)..."):
            
            # 1. 取得成分股
            df_holdings, source_msg = get_etf_holdings(selected_etf)
            
            if not df_holdings.empty:
                st.toast(f"資料來源：{source_msg}")
                
                top_10 = df_holdings.head(10).copy()
                realtime_data = []
                
                # 統計
                bull_force = 0 # 多方力道
                bear_force = 0 # 空方力道
                
                progress_bar = st.progress(0)
                
                for i, row in top_10.iterrows():
                    code = str(row['股票代號']).strip()
                    name = row['股票名稱']
                    weight = row['持股權重']
                    
                    # 使用 VPA 分析
                    pct_chg, vol_ratio, signal = analyze_stock_strength(code)
                    
                    # 計算加權貢獻
                    contribution = weight * pct_chg
                    
                    # 判斷多空分數
                    if pct_chg > 0: bull_force += weight
                    if pct_chg < 0: bear_force += weight
                    
                    realtime_data.append({
                        "代號": code,
                        "名稱": name,
                        "權重": f"{weight}%",
                        "漲跌幅": pct_chg, 
                        "漲跌": f"{pct_chg}%",
                        "量比": f"{vol_ratio}倍",
                        "VPA 量價訊號": signal,
                        "貢獻度": contribution
                    })
                    progress_bar.progress((i + 1) / 10)
                
                st.markdown("---")
                
                # 總結儀表板
                net_force = bull_force - bear_force
                
                c1, c2, c3 = st.columns(3)
                c1.metric("🔥 多方權重", f"{bull_force:.1f}%")
                c2.metric("🧊 空方權重", f"{bear_force:.1f}%")
                
                status = "盤整"
                status_color = "gray"
                if net_force > 15: 
                    status = "全面進攻"
                    status_color = "red"
                elif net_force > 5:
                    status = "偏多操作"
                    status_color = "orange"
                elif net_force < -15:
                    status = "全面棄守"
                    status_color = "green"
                elif net_force < -5:
                    status = "偏空保守"
                    status_color = "blue"
                    
                c3.markdown(f"### 總結：<span style='color:{status_color}'>{status}</span>", unsafe_allow_html=True)

                # 詳細數據表
                res_df = pd.DataFrame(realtime_data)
                
                def color_signal(val):
                    color = 'white'
                    if "爆量長紅" in val: color = '#ff4b4b' # Red
                    elif "爆量長黑" in val: color = '#00c853' # Green
                    elif "量縮價漲" in val: color = '#ffa726' # Orange
                    return f'color: {color}; font-weight: bold;'

                st.dataframe(
                    res_df.style.map(color_signal, subset=['VPA 量價訊號']),
                    column_config={
                        "漲跌幅": st.column_config.NumberColumn(format="%.2f%%"),
                        "貢獻度": st.column_config.ProgressColumn(format="%.2f", min_value=-5, max_value=5),
                    },
                    use_container_width=True
                )
                
                st.info("💡 **VPA 訊號解讀**：\n* **🔴 爆量長紅**：價漲量增，主力積極買進，可追價。\n* **🟠 量縮價漲**：籌碼安定，惜售，適合續抱。\n* **🟢 爆量長黑**：價跌量增，主力恐慌出貨，請避開。\n* **量比**：今日成交量 / 過去10日均量。大於 1.2 代表出量。")
                
            else:
                st.error("❌ 系統忙碌中，請稍後再試。")

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
elif page == "🦅 ETF 籌碼透視": 
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
    st.image("https://visitor-badge.laobi.icu/badge?page_id=pro_quant_platform_v6", caption="總瀏覽人次")




import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

# --- 1. 頁面基礎設定 ---
st.set_page_config(
    page_title="Pro Quant - 全方位量化投資平台",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 側邊欄導航 (Navigation) ---
st.sidebar.title("🧭 導航選單")
page = st.sidebar.radio("前往頁面", ["📈 量化回測分析", "📚 新手名詞百科", "🎧 財經資源推薦"])

st.sidebar.markdown("---")
st.sidebar.info("Designed by **Gemini & 電機系大一開發者**")

# --- 核心函數區 (邏輯運算) ---
def get_stock_data(ticker, start, end):
    try:
        data = yf.download(ticker, start=start, end=end, auto_adjust=True)
        if isinstance(data.columns, pd.MultiIndex):
            data = data.xs(ticker, axis=1, level=1)
        return data
    except Exception as e:
        return pd.DataFrame()

def calculate_indicators(df, ma_short, ma_long):
    # MA
    df['MA_Short'] = df['Close'].rolling(window=ma_short).mean()
    df['MA_Long'] = df['Close'].rolling(window=ma_long).mean()
    # Bollinger
    df['BB_Mid'] = df['Close'].rolling(window=20).mean()
    df['BB_Std'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Mid'] + 2 * df['BB_Std']
    df['BB_Lower'] = df['BB_Mid'] - 2 * df['BB_Std']
    # RSI
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
        # 根據市場預設代號
        default_ticker = "2330" if "台股" in market_type else "NVDA"
        user_input = st.text_input("輸入股票代號", default_ticker)
    
    # 自動處理代號邏輯
    ticker = user_input.upper().strip()
    if "台股" in market_type and not ticker.endswith(".TW") and ticker.isdigit():
        ticker += ".TW"
    
    with col3:
        initial_capital = st.number_input("初始本金", value=1000000, step=10000)

    # 參數設定
    with st.expander("🛠️ 策略參數設定 (點擊展開)"):
        c1, c2 = st.columns(2)
        ma_short = c1.slider("短期均線 (MA Short)", 5, 60, 10)
        ma_long = c2.slider("長期均線 (MA Long)", 20, 200, 60)

    if st.button("🚀 開始分析", use_container_width=True):
        with st.spinner(f"正在連線至全球交易所抓取 {ticker} 資料..."):
            df = get_stock_data(ticker, "2023-01-01", datetime.date.today())
            
            if df.empty or len(df) < ma_long:
                st.error(f"❌ 找不到代號 **{ticker}** 或資料不足，請檢查代號是否正確。")
            else:
                df = calculate_indicators(df, ma_short, ma_long)
                
                # 簡單策略：黃金交叉
                df['Signal'] = np.where(df['MA_Short'] > df['MA_Long'], 1.0, 0.0)
                df['Position'] = df['Signal'].diff()
                
                # 計算最終績效
                market_ret = (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]
                
                # 繪圖
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.03)
                
                # K線與均線
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="收盤價", line=dict(color='white')), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['MA_Short'], name=f"MA {ma_short}", line=dict(color='yellow', width=1)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['MA_Long'], name=f"MA {ma_long}", line=dict(color='cyan', width=1)), row=1, col=1)
                
                # 買賣訊號
                buys = df[df['Position'] == 1]
                sells = df[df['Position'] == -1]
                fig.add_trace(go.Scatter(x=buys.index, y=df.loc[buys.index]['Close'], mode='markers', marker=dict(symbol='triangle-up', color='lime', size=15), name='買進'), row=1, col=1)
                fig.add_trace(go.Scatter(x=sells.index, y=df.loc[sells.index]['Close'], mode='markers', marker=dict(symbol='triangle-down', color='red', size=15), name='賣出'), row=1, col=1)

                # RSI
                fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='orange')), row=2, col=1)
                fig.add_hlines(y=[30, 70], row=2, col=1, line_dash="dot", line_color="gray")
                
                fig.update_layout(template="plotly_dark", height=600, title_text=f"{ticker} 技術分析圖")
                st.plotly_chart(fig, use_container_width=True)
                
                # 績效卡片
                st.success(f"📊 區間漲跌幅 (Buy & Hold): {market_ret*100:.2f}%")

# --- 頁面 2: 新手名詞百科 ---
def page_learn():
    st.title("📚 投資新手名詞百科")
    st.markdown("這裡整理了量化交易與財報分析常見的專有名詞，幫助你看懂數據背後的意義。")
    
    tab1, tab2, tab3 = st.tabs(["📊 技術指標", "💰 交易觀念", "📉 風險指標"])
    
    with tab1:
        st.subheader("常見技術指標")
        with st.expander("什麼是 MA (移動平均線)?"):
            st.write("""
            **Moving Average (MA)**：將過去一段時間的股價加總平均。
            * **用途**：判斷趨勢方向。
            * **範例**：MA20 (月線) 向上，代表短期趨勢看漲；MA60 (季線) 則是看中期生命線。
            """)
        with st.expander("什麼是 RSI (相對強弱指標)?"):
            st.write("""
            **Relative Strength Index (RSI)**：衡量股價漲跌的力道。
            * **範圍**：0 ~ 100。
            * **判讀**：超過 70 通常代表「超買」(可能回檔)；低於 30 代表「超賣」(可能反彈)。
            """)
            
    with tab2:
        st.subheader("核心交易觀念")
        with st.expander("什麼是 黃金交叉 / 死亡交叉?"):
            st.write("""
            * **黃金交叉 (Golden Cross)**：短天期均線(如10日) **向上突破** 長天期均線(如60日)，視為**買進訊號**。
            * **死亡交叉 (Death Cross)**：短天期均線 **向下跌破** 長天期均線，視為**賣出訊號**。
            """)
            
    with tab3:
        st.subheader("風險控管")
        with st.expander("什麼是 MDD (最大回撤)?"):
            st.write("""
            **Max Drawdown (MDD)**：資產從最高點掉下來的最大幅度。
            * **意義**：這是投資人最痛的時刻。如果 MDD 是 -50%，代表你的資產曾經腰斬。好的策略 MDD 應該要越小越好。
            """)

# --- 頁面 3: 資源推薦 ---
def page_resources():
    st.title("🎧 優質財經資源推薦")
    st.markdown("投資這條路很長，這裡有一些優質的 Podcast 與資訊來源，陪你一起成長。")
    
    st.subheader("🎙️ 必聽 Podcast")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.image("https://is1-ssl.mzstatic.com/image/thumb/Podcasts116/v4/4b/65/5c/4b655c3c-8822-252f-1785-5b871542f562/mza_10336653926676344336.jpg/600x600bb.jpg", width=150)
        st.markdown("### 股癌 (Gooaye)")
        st.write("**風格**：幽默直白、幹話多但觀念正。")
        st.write("**適合**：想了解市場大趨勢、美股動態、以及不想聽太嚴肅財經新聞的人。")
        st.markdown("[👉 Apple Podcast 連結](https://podcasts.apple.com/tw/podcast/%E8%82%A1%E7%99%8C/id1500839292)")

    with col2:
        st.image("https://is1-ssl.mzstatic.com/image/thumb/Podcasts126/v4/31/58/63/3158636b-640a-c07a-227b-5c404847e06c/mza_11979350438131343759.jpg/600x600bb.jpg", width=150)
        st.markdown("### 游庭皓的財經皓角")
        st.write("**風格**：總體經濟分析、數據流、邏輯清晰。")
        st.write("**適合**：想看懂殖利率曲線、PMI 指數、聯準會政策對股市影響的人。")
        st.markdown("[👉 YouTube 頻道連結](https://www.youtube.com/@tinghaoview)")

    st.markdown("---")
    st.subheader("📚 推薦閱讀網站")
    st.markdown("""
    * **財報狗 (Statement Dog)**：台灣最強的基本面分析網站，圖表非常直觀。[連結](https://statementdog.com/)
    * **TradingView**：全球最專業的看盤軟體，量化交易員必備。[連結](https://tw.tradingview.com/)
    """)

# --- 主程式路由 (Router) ---
if page == "📈 量化回測分析":
    page_analysis()
elif page == "📚 新手名詞百科":
    page_learn()
elif page == "🎧 財經資源推薦":

    page_resources()
    #

import yfinance as yf
import sqlite3
import matplotlib.pyplot as plt
from matplotlib import style
from tkinter import Tk, Label, Button, Frame
from tkinter import ttk
import time
from datetime import datetime, timedelta
from newsapi import NewsApiClient
from textblob import TextBlob

# Replace with your News API key from newsapi.org
NEWS_API_KEY = "HIDDEN"
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('stocks.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS prices 
                 (ticker TEXT, price REAL, timestamp REAL)''')
    conn.commit()
    conn.close()
    print("Database initialized")

# Fetch real-time stock data
def fetch_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        price = stock.info.get('regularMarketPrice', 0)
        if price == 0:
            print(f"Warning: No real-time price data for {ticker}")
        timestamp = time.time()
        return (ticker, price, timestamp)
    except Exception as e:
        print(f"Real-Time Fetch Error for {ticker}: {e}")
        return None

# Fetch historical data (weekly: 7d, 30m)
def fetch_historical_data(ticker, period, interval):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)
        if hist.empty:
            print(f"No historical data for {ticker} ({period}, {interval})")
            return []
        data = []
        for timestamp, row in hist.iterrows():
            price = row['Close']
            unix_time = time.mktime(timestamp.to_pydatetime().timetuple())
            data.append((ticker, price, unix_time))
        return data
    except Exception as e:
        print(f"Historical Fetch Error for {ticker}: {e}")
        return []

# Store in SQLite
def store_data(data):
    if not data:
        print("No data to store")
        return
    conn = sqlite3.connect('stocks.db')
    c = conn.cursor()
    if isinstance(data, list):
        c.executemany('INSERT INTO prices VALUES (?, ?, ?)', data)
    else:
        c.execute('INSERT INTO prices VALUES (?, ?, ?)', data)
    conn.commit()
    conn.close()
    print(f"Stored data for {data[0]}: {data[1]} at {data[2]}")

# Clean old data (keep last 7 days)
def clean_old_data():
    conn = sqlite3.connect('stocks.db')
    c = conn.cursor()
    seven_days_ago = time.time() - (7 * 24 * 3600)
    c.execute("DELETE FROM prices WHERE timestamp < ?", (seven_days_ago,))
    conn.commit()
    conn.close()

# Fetch news and provide single impact recommendation
def fetch_news(ticker):
    try:
        query = ticker.split('.')[0]
        articles = newsapi.get_everything(q=query, language='en', sort_by='publishedAt', page_size=3)
        if not articles['articles']:
            return [("No news available", "Neutral impact")]
        
        total_sentiment = 0
        news_items = []
        for article in articles['articles']:
            title = article['title']
            sentiment = TextBlob(title).sentiment.polarity
            total_sentiment += sentiment
            news_items.append(title)
        
        avg_sentiment = total_sentiment / len(articles['articles'])
        if avg_sentiment > 0.1:
            impact = "Stock price may increase"
        elif avg_sentiment < -0.1:
            impact = "Stock price will likely decrease"
        else:
            impact = "Neutral impact on stock price"
        
        return [(news_items, impact)]
    except Exception as e:
        print(f"News Fetch Error for {ticker}: {e}")
        return [("No news available", "Neutral impact")]

# Weekly graph (last 7 days, 30-minute intervals)
def plot_weekly(ticker, root, after_id=[None]):
    if after_id[0] is not None:
        root.after_cancel(after_id[0])

    conn = sqlite3.connect('stocks.db')
    c = conn.cursor()
    seven_days_ago = time.time() - (7 * 24 * 3600)
    c.execute("SELECT price, timestamp FROM prices WHERE ticker=? AND timestamp >= ? ORDER BY timestamp", (ticker, seven_days_ago))
    data = c.fetchall()
    conn.close()

    if not data:
        print(f"No weekly data for {ticker} yet")
        return

    prices = [d[0] for d in data]
    timestamps = [datetime.fromtimestamp(d[1]).strftime('%m-%d %H:%M') for d in data]

    style.use('dark_background')
    plt.figure(figsize=(10, 4))
    plt.clf()
    ax = plt.gca()
    
    plt.plot(timestamps, prices, color='#00b7ff', linewidth=1.5, label=f"{ticker} (7 Days)")
    plt.fill_between(timestamps, prices, min(prices), color='#00b7ff', alpha=0.1)
    
    plt.title(f'{ticker} Price - Last 7 Days', fontsize=14, color='white', pad=10)
    plt.ylabel('Price ($)', fontsize=12, color='white')
    plt.xlabel('')
    ax.tick_params(axis='both', colors='white')
    ax.set_xticklabels([])
    plt.xticks(rotation=45)
    
    plt.legend(loc='upper left', fontsize=10, facecolor='#333333', edgecolor='white', labelcolor='white')
    plt.grid(color='gray', linestyle='--', linewidth=0.5, alpha=0.3)
    plt.tight_layout()
    plt.draw()
    plt.pause(0.001)

    # Schedule next update (30 min = 1800000 ms)
    after_id[0] = root.after(1800000, lambda: plot_weekly(ticker, root, after_id))

# Live price and daily percentage update
def update_live_price(ticker, price_label, last_price=[None]):
    data = fetch_stock_data(ticker)
    if data:
        ticker, current_price, timestamp = data
        store_data(data)

        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        if not hist.empty:
            opening_price = hist['Open'][0]
            daily_change = ((current_price - opening_price) / opening_price) * 100
            change_text = f" ({daily_change:+.2f}% today)"
        else:
            change_text = " (N/A today)"

        if last_price[0] is None:
            color = "white"
        elif current_price > last_price[0]:
            color = "#00cc00"  # Green
        elif current_price < last_price[0]:
            color = "#ff3333"  # Red
        else:
            color = "white"
        last_price[0] = current_price

        price_text = f"{current_price:.2f}$"
        full_text = f"{price_text}{change_text}"
        price_label.config(text=full_text, fg=color)

    price_label.after(3000, lambda: update_live_price(ticker, price_label, last_price))

# UI
def create_ui():
    root = Tk()
    root.title("Stock Analyzer")
    root.geometry("500x600")
    root.configure(bg="#1a1a1a")

    # Style configuration for ttk widgets
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("TButton", font=("Helvetica", 11), padding=8, background="#333333", foreground="white")
    style.map("TButton", background=[('active', '#555555')], foreground=[('active', 'white')])
    style.configure("TLabel", font=("Helvetica", 12), background="#1a1a1a", foreground="white")

    # Main frame
    main_frame = Frame(root, bg="#1a1a1a", padx=20, pady=20)
    main_frame.pack(expand=True, fill="both")

    # Title
    title_label = Label(main_frame, text="Stock Analyzer", font=("Helvetica", 18, "bold"), bg="#1a1a1a", fg="#00b7ff")
    title_label.pack(pady=(0, 20))

    # Instruction label
    Label(main_frame, text="Select a Stock to Track", font=("Helvetica", 12), bg="#1a1a1a", fg="#cccccc").pack(pady=(0, 15))

    # Buttons frame
    button_frame = Frame(main_frame, bg="#1a1a1a")
    button_frame.pack(pady=10)

    def track_stock(ticker, name):
        news_label.config(text=f"Fetching data for {name}...", fg="#cccccc")
        price_label.config(text="Loading price...", fg="#cccccc")
        root.update()

        weekly_hist = fetch_historical_data(ticker, "7d", "30m")
        if weekly_hist:
            store_data(weekly_hist)
            print(f"Loaded {len(weekly_hist)} weekly points for {ticker}")

        plot_weekly(ticker, root)
        news_items = fetch_news(ticker)
        news_text = f"News for {name}:\n"
        titles, impact = news_items[0]
        if isinstance(titles, list):
            for title in titles:
                news_text += f"- {title}\n"
            news_text += f"Overall Impact: {impact}"
        else:
            news_text += f"- {titles}\nOverall Impact: {impact}"
        news_label.config(text=news_text)

        update_live_price(ticker, price_label)

    ttk.Button(button_frame, text="Tesla (TSLA)", command=lambda: track_stock('TSLA', 'Tesla')).pack(pady=8, fill="x")
    ttk.Button(button_frame, text="Apple (AAPL)", command=lambda: track_stock('AAPL', 'Apple')).pack(pady=8, fill="x")
    ttk.Button(button_frame, text="Nvidia (NVDA)", command=lambda: track_stock('NVDA', 'Nvidia')).pack(pady=8, fill="x")

    # Live price label
    price_label = Label(main_frame, text="", font=("Helvetica", 20, "bold"), bg="#1a1a1a", fg="white")
    price_label.pack(pady=20)

    # News frame
    news_frame = Frame(main_frame, bg="#1a1a1a", relief="groove", borderwidth=2)
    news_frame.pack(pady=10, fill="both", expand=True)
    news_label = Label(news_frame, text="", font=("Helvetica", 10), bg="#1a1a1a", fg="#cccccc", wraplength=450, justify="left", anchor="n")
    news_label.pack(side="top", fill="both", expand=True, padx=10, pady=10)

    root.mainloop()

if __name__ == "__main__":
    init_db()
    create_ui()
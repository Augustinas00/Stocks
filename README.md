# Stock Analyzer

A Python-based tool to track real-time stock prices, display weekly trends, and analyze news sentiment for selected stocks.

## Features

- **Real-Time Prices**: Fetches live stock prices with daily percentage change.
- **Weekly Graphs**: Plots 7-day price trends with 30-minute intervals.
- **News Sentiment**: Analyzes recent news and predicts stock price impact.
- **Database**: Stores data in SQLite, keeping the last 7 days.
- **UI**: Simple Tkinter interface with stock selection buttons.

## Requirements

- **Python**: 3.x
- **Libraries**: `yfinance`, `sqlite3`, `matplotlib`, `tkinter`, `newsapi`, `textblob`
- **News API Key**: Get one from [newsapi.org](https://newsapi.org/)

## Notes

- Data is stored in stocks.db.
- Graphs update every 30 minutes.
- News sentiment uses the last 3 articles.

## Installation

- After cloning install dependancies: `pip install yfinance matplotlib newsapi-python textblob`
- Run the script python: `stock_analyzer.py`

## Screenshots

![1](https://github.com/user-attachments/assets/075de9c0-d6ab-4d3b-bbf7-2097898842cb)
![2](https://github.com/user-attachments/assets/811d19ef-c62d-4771-8ddf-c1cf7e4adcf1)

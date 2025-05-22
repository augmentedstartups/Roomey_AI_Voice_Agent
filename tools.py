
import os
import yfinance as yf

# if not os.getenv("TAVILY_API_KEY"):
#     print("Warning: TAVILY_API_KEY environment variable not set.")

def get_stock_price(symbol: str):
    try:
        stock = yf.Ticker(symbol)
        historical_data = stock.history(period="1d")
        if not historical_data.empty:
            current_price = historical_data['Close'].iloc[-1]
            return current_price
        else:
            return None
    except Exception as e:
        print(f"Error retrieving stock price for {symbol}: {e}")
        return None



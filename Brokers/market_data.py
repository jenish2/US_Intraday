# Data Source
import yfinance as yf
import logging


class MarketData:

    @staticmethod
    def get_market_data(symbol, period, interval):
        # Interval required 5 minutes
        try:
            df = yf.download(tickers=symbol, period=period, interval=interval)
            del df['Adj Close']
            del df['Volume']
            return df

        except Exception as e:
            print("ERROR IN GETTING DATA FROM Y-FINANCE")
            print(e)


if __name__ == "__main__":
    print(MarketData.get_market_data('AAPL', '1d', "1m"))

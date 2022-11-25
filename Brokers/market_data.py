# Data Source
import yfinance as yf


class MarketData:

    @staticmethod
    def get_market_data(symbol, period, interval):
        # Interval required 5 minutes
        df = yf.download(tickers=symbol, period=period, interval=interval)
        del df['Adj Close']
        del df['Volume']
        return df


if __name__ == "__main__":
    MarketData.get_market_data('AAPL', '1d', "1m")

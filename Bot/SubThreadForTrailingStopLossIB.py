import time
from threading import Thread

from Brokers.market_data import MarketData


class TrailingStopLoss(Thread):
    def __init__(self, symbol, price_where_should_add_trailing_stop_loss, stock_purchased_price,
                 trailing_stop_percentage, side, take_profit, stop_loss, quantity, parent_order_id, api):
        Thread.__init__(self, daemon=False)
        self.SIDE = side
        self.SYMBOL = symbol
        self.THRESHOLD = price_where_should_add_trailing_stop_loss,
        self.STOCK_BOUGHT_PRICE = stock_purchased_price
        self.TRAILING_STOP_PERCENTAGE = trailing_stop_percentage
        self.TAKE_PROFIT = take_profit
        self.STOP_LOSS = stop_loss
        self.API = api
        self.QTC = quantity
        self.PARENT_ORDER_ID = parent_order_id

    def run(self) -> None:
        while True:
            time.sleep(5)
            df = MarketData.get_market_data(symbol=self.SYMBOL,
                                            interval="1m",
                                            period="1d"
                                            )

            try:
                if self.SIDE == "BUY":
                    if df.get('High').iat[-1] >= self.TAKE_PROFIT or df.get('Low').iat[-1] <= self.STOP_LOSS:
                        break

                    if df.get('High').iat[-1] > self.THRESHOLD:
                        self.API.update_order_stop_loss(symbol=self.SYMBOL, side="BUY",
                                                        quantity=self.QTC,
                                                        parent_order_id=self.PARENT_ORDER_ID,
                                                        stop_loss_price_updated=self.STOCK_BOUGHT_PRICE,
                                                        trail_percentage=self.TRAILING_STOP_PERCENTAGE)

                        break

                else:
                    if df.get('Low').iat[-1] <= self.TAKE_PROFIT or df.get('High').iat[-1] >= self.STOP_LOSS:
                        break

                    if df.get('Low').iat[-1] < self.THRESHOLD:
                        self.API.update_order_stop_loss(symbol=self.SYMBOL, side="SELL",
                                                        quantity=self.QTC,
                                                        parent_order_id=self.PARENT_ORDER_ID,
                                                        stop_loss_price_updated=self.STOCK_BOUGHT_PRICE,
                                                        trail_percentage=self.TRAILING_STOP_PERCENTAGE)

                        break
            except Exception as e:
                print(e)

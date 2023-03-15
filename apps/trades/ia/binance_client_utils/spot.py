from apps.trades.models import Trade as TradeModel
from apps.trades.binance.exceptions import BinanceAPIException
from apps.trades.ia.binance_client_utils.utils import format_decimals
import traceback

class Spot:

    def __init__(self, client, pair, stop_loss_divisor_plus, stop_loss_percent, coin1, coin2):
        self.pair = pair
        self.stop_loss_divisor_plus = stop_loss_divisor_plus
        self.stop_loss_percent = stop_loss_percent
        self.client = client
        self.coin1 = coin1
        self.coin2 = coin2
        self.money = 0

    #TODO
    def close_buy(self):
        exception = ""
        sell = None
        bought_price = 0
        traceback_str = ""
        try:
            position = self.get_coin2_balance()
            if position:
                quantity = format_decimals(abs(float(self.get_coin2_balance()['free'])))
                print("QUANTITY= ", quantity)
                if quantity > 0:
                    sell = self.client.order_market_sell(
                        symbol=self.pair,
                        quantity=quantity
                    )
                else:
                    raise Exception(f"No quantity in {self.coin2} close spot")
            else:
                raise Exception(f"Not positions opened {self.coin2}  spot")
        except Exception as e:
            exception = str(e)
            traceback_str = traceback.format_exc()
        finally:
            if bought_price > 0 and quantity > 0:
                TradeModel.objects.create(
                    pair=self.pair,
                    operation="SELL CLOSE BUY SPOT",
                    money=self.money,
                    price=bought_price,
                    quantity=quantity,
                    error=exception,
                    traceback=traceback_str
                )
        return sell


    def increase_sl(self, init_price=0):
        orders = self.get_open_orders()
        if orders:
            last_order = orders[-1]
            stop_price = format_decimals(init_price)
            if stop_price <= 0:
                stop_price = float(last_order["stopPrice"]) * (1 + float(self.stop_loss_divisor_plus))
            quantity = format_decimals(float(last_order["origQty"]))
            price = stop_price * (1 - 0.005)
            if quantity > 0:
                self.stop_loss_limit_sell(
                    stop_price,
                    price,
                    quantity
                )
                return True
            else:
                print("SPOT SL NOT INCREASED BECAUSE NOT QUANTITY")
        else:
            balance_coin2 = format_decimals(float(self.get_coin2_balance()['free']))
            if balance_coin2 > 0:
                price = format_decimals(init_price)
                if price <= 0:
                    price = format_decimals(self.get_avg_price())
                self.stop_loss_limit_sell(
                    price * ( 1 - self.stop_loss_percent ),
                    price * ( 1 - self.stop_loss_percent - 0.005 ),
                    balance_coin2
                )
        return False

    def cancel_all_open_orders(self):
        for oo in self.get_open_orders():
            if oo["symbol"] == self.pair:
                self.cancel_order(oo["orderId"])

    def cancel_order(self, order_id):
        self.client.cancel_order(
            symbol=self.pair,
            orderId=order_id
        )

    def set_money(self, _money):
        print("Money: ", _money, " Wallet money: ", self.money, "self.get_coin1_balance(): ", self.get_coin1_balance(), "Coin: ", self.coin1)
        if float(self.get_coin1_balance()['free']) >= _money:
            self.money = _money
            return True
        return False

    def buy_market(self, price, quantity=0):
        print("BUY MARKET PRICE: ", price)
        buy = None
        if price > 0:
            exception = ""
            traceback_str = ""
            try:
                if quantity == 0:
                    quantity = format_decimals(self.money / price) 
                else:
                    quantity = format_decimals(quantity)
                print("BUY MARKET: ", self.pair, quantity)
                buy = self.client.order_market_buy(
                    symbol=self.pair,
                    quantity=quantity,
                )
            except Exception as e:
                exception = str(e)
                traceback_str = traceback.format_exc()
                raise e
            finally:
                TradeModel.objects.create(
                    pair=self.pair,
                    operation="BUY MARKET",
                    money=self.money,
                    price=price,
                    quantity=quantity,
                    error=exception,
                    traceback=traceback_str
                )
        return buy

    def sell_market(self, price, quantity=0):
        print("SELL MARKET PRICE: ", price)
        sell = None
        if price > 0:
            exception = ""
            traceback_str = ""
            try:
                if quantity == 0:
                    quantity = format_decimals(self.money / price) 
                else:
                    quantity = format_decimals(quantity)
                print("SELL MARKET: ", self.pair, quantity)
                sell = self.client.order_market_sell(
                    symbol=self.pair,
                    quantity=quantity
                )
            except Exception as e:
                exception = str(e)
                traceback_str = traceback.format_exc()
                raise e
            finally:
                TradeModel.objects.create(
                    pair=self.pair,
                    operation="SELL MARKET",
                    money=self.money,
                    price=price,
                    quantity=quantity,
                    error=exception,
                    traceback=traceback_str
                )
        return sell

    def stop_loss_limit_sell(self, stop, price, quantity):
        stop = format_decimals(stop)
        price = format_decimals(price)
        self.cancel_all_open_orders()
        print("SL LIMIT PRICE: ", price)
        buy = None
        if price > 0 and stop > 0:
            exception = ""
            traceback_str = ""
            try:
                quantity = format_decimals(quantity)
                print("SL LIMIT: ", self.pair, quantity, price, stop)
                buy = self.client.order_limit_sell_stop_loss(
                    symbol=self.pair,
                    quantity=quantity,
                    price=price,
                    stopPrice=stop
                )
            except BinanceAPIException as e:
                if e.code == -2010 and e.message == "Stop price would trigger immediately.":
                        self.sell_market(
                            stop,
                            quantity
                        )
                exception = str(e)
                traceback_str = traceback.format_exc()
            except Exception as e:
                exception = str(e)
                traceback_str = traceback.format_exc()
                raise e
            finally:
                TradeModel.objects.create(
                    pair=self.pair,
                    operation="SL LIMIT",
                    money=self.money,
                    price=price,
                    quantity=quantity,
                    error=exception,
                    traceback=traceback_str
                )
        return buy

    def get_open_orders(self):
        return self.client.get_open_orders(
            symbol=self.pair
        )

    def get_coin1_balance(self):
        return self.client.get_asset_balance(
            asset=self.coin1
        )

    def get_coin1_balance(self):
        return self.client.get_asset_balance(
            asset=self.coin1
        )

    def get_coin2_balance(self):
        return self.client.get_asset_balance(
            asset=self.coin2
        )

    def get_avg_price(self):
        return float(self.client.get_avg_price(
            symbol=self.pair
        )["price"])
       
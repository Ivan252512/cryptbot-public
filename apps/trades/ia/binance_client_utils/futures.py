from turtle import position
from apps.trades.models import Trade as TradeModel
from apps.trades.binance.exceptions import BinanceAPIException
from apps.trades.ia.binance_client_utils.utils import format_decimals
import traceback


class Futures:

    def __init__(self, client, pair, stop_loss_divisor_plus, stop_loss_percent, coin1):
        self.pair = pair
        self.stop_loss_divisor_plus = stop_loss_divisor_plus
        self.stop_loss_percent = stop_loss_percent
        self.client = client
        self.coin1 = coin1
        self.money = 0

    def close_sell(self):
        exception = ""
        traceback_str = ""
        buy = None
        sold_price = 0
        try:
            position = self.get_position_information()
            if position:
                quantity = format_decimals(abs(float(position[-1]["positionAmt"])))
                if quantity > 0:
                    buy = self.client.futures_create_order(
                        symbol=self.pair,
                        positionSide="BOTH",
                        side="BUY",
                        type= "MARKET",
                        quantity=quantity
                    )
                    orderId = buy["orderId"]
                    buy = self.client.futures_get_order(
                        symbol=self.pair,
                        orderId= orderId
                    )
                    sold_price = float(buy["avgPrice"])
                else:
                    raise Exception("No quantity in positions close sell")
            else:
                raise Exception("Not positions opened close sell")
        except Exception as e:
            exception = str(e)
            traceback_str = traceback.format_exc()
        finally:
            if sold_price > 0 and quantity > 0:
                TradeModel.objects.create(
                    pair=self.pair,
                    operation="BUY CLOSE SELL FUTURES",
                    money=self.money,
                    price=sold_price,
                    quantity=quantity,
                    error=exception,
                    traceback=traceback_str
                )
        return buy

    def close_buy(self):
        exception = ""
        traceback_str = ""
        sell = None
        bought_price = 0
        try:
            position = self.get_position_information()
            if position:
                quantity = format_decimals(abs(float(position[-1]["positionAmt"])))
                if quantity > 0:
                    sell = self.client.futures_create_order(
                        symbol=self.pair,
                        positionSide="BOTH",
                        side="SELL",
                        type= "MARKET",
                        quantity=quantity
                    )
                    orderId = sell["orderId"]
                    sell = self.client.futures_get_order(
                        symbol=self.pair,
                        orderId= orderId
                    )
                    bought_price = float(sell["avgPrice"])
                else:
                    raise Exception("No quantity in positions close buy")
            else:
                raise Exception("Not positions opened close buy")
        except Exception as e:
            exception = str(e)
            traceback_str = traceback.format_exc()
        finally:
            if bought_price > 0 and quantity > 0:
                TradeModel.objects.create(
                    pair=self.pair,
                    operation="SELL CLOSE BUY FUTURES",
                    money=self.money,
                    price=bought_price,
                    quantity=quantity,
                    error=exception,
                    traceback=traceback_str
                )
        return sell



    def decrease_sl(self, init_price=0):
        orders = self.get_open_orders()
        position = float(self.get_position_information()[-1]["positionAmt"])
        position_type = "short" if position < 0 else "long"
        quantity = format_decimals(abs(position))
        if orders:
            last_order = orders[-1]
            stop_price = format_decimals(init_price)
            if stop_price <= 0:
                stop_price = float(last_order["stopPrice"]) * (1 - float(self.stop_loss_divisor_plus))
            if quantity > 0:
                self.stop_loss_limit_buy(
                    stop_price,
                    quantity
                )
                return True
            else:
                print("FUTURES SL NOT DECREASED BECAUSE NO ORDERS")
        else:
            if position_type == "short" and quantity > 0:
                stop_price = format_decimals(init_price)
                if stop_price <= 0:
                    stop_price = format_decimals(self.get_mark_price())
                self.stop_loss_limit_buy(
                    stop_price * ( 1 + self.stop_loss_percent ),
                    quantity
                )
        return False

    def increase_sl(self, init_price=0):
        orders = self.get_open_orders()
        position = float(self.get_position_information()[-1]["positionAmt"])
        position_type = "short" if position < 0 else "long"
        quantity = format_decimals(abs(position))
        if orders:
            last_order = orders[-1]
            stop_price = format_decimals(init_price)
            if stop_price <= 0:
                stop_price = float(last_order["stopPrice"]) * (1 + float(self.stop_loss_divisor_plus))
            if quantity > 0:
                self.stop_loss_limit_sell(
                    stop_price,
                    quantity
                )
                return True
            else:
                print("FUTURES SL NOT INCREASED BECAUSE NO ORDERS")
        else:
            if position_type == "long" and quantity > 0:
                stop_price = format_decimals(init_price)
                if stop_price <= 0:
                    stop_price = format_decimals(self.get_mark_price())
                self.stop_loss_limit_sell(
                    stop_price * ( 1 - self.stop_loss_percent ),
                    quantity
                )
        return False

    def cancel_all_open_orders(self):
        return self.client.futures_cancel_all_open_orders(
            symbol=self.pair
        )

    def set_money(self, _money):
        print("Money: ", _money, " Wallet money: ", self.money, "self.get_coin1_balance(): ", self.get_coin1_balance(), "Coin: ", self.coin1)
        if self.get_coin1_balance() >= _money:
            self.money = _money
            return True
        return False

    def buy_market(self, price, quantity=0):
        print("FUTURES BUY MARKET PRICE: ", price)
        buy = None
        exception = ""
        traceback_str = ""
        if price > 0:
            exception = ""
            traceback_str = ""
            try:
                if quantity == 0:
                    quantity = format_decimals(self.money / price) 
                else:
                    quantity = format_decimals(quantity)
                print("FUTURES BUY MARKET: ", self.pair, quantity)
                buy = self.client.futures_create_order(
                    symbol=self.pair,
                    positionSide="BOTH",
                    side="BUY",
                    type= "MARKET",
                    quantity=quantity
                )

                orderId = buy["orderId"]
                buy = self.client.futures_get_order(
                    symbol=self.pair,
                    orderId= orderId
                )
            except Exception as e:
                exception = str(e)
                traceback_str = traceback.format_exc()
            finally:
                TradeModel.objects.create(
                    pair=self.pair,
                    operation="BUY MARKET FUTURES",
                    money=self.money,
                    price=price,
                    quantity=quantity,
                    error=exception,
                    traceback=traceback_str
                )
        return buy

    def sell_market(self, price, quantity=0):
        print("FUTURES SELL MARKET PRICE: ", price)
        sell = None
        if price > 0:
            exception = ""
            traceback_str = ""
            try:
                if quantity == 0:
                    quantity = format_decimals(self.money / price) 
                else:
                    quantity = format_decimals(quantity)
                print("FUTURES SELL MARKET: ", self.pair, quantity)
                sell = self.client.futures_create_order(
                    symbol=self.pair,
                    positionSide="BOTH",
                    side="SELL",
                    type= "MARKET",
                    quantity=quantity
                )
                orderId = sell["orderId"]
                sell = self.client.futures_get_order(
                    symbol=self.pair,
                    orderId= orderId
                )
            except Exception as e:
                exception = str(e)
                traceback_str = traceback.format_exc()
            finally:
                TradeModel.objects.create(
                    pair=self.pair,
                    operation="SELL MARKET FUTURES",
                    money=self.money,
                    price=price,
                    quantity=quantity,
                    error=exception,
                    traceback=traceback_str
                )
        return sell


    def stop_loss_limit_sell(self, stop, quantity):
        price = format_decimals(stop)
        self.cancel_all_open_orders()
        print("FUTURES SL LIMIT PRICE SELL: ", price)
        buy = None
        if price > 0:
            exception = ""
            traceback_str = ""
            try:
                quantity = format_decimals(quantity)
                print("FUTURES SL LIMIT SELL: ", self.pair, quantity, price)
                buy = self.client.futures_create_order(
                    symbol=self.pair,
                    positionSide="BOTH",
                    side="SELL",
                    type= "STOP_MARKET",
                    stopPrice=price,
                    quantity=quantity
                )
            except BinanceAPIException as e:
                if e.code == -2021 and e.message == "Order would immediately trigger.":
                        self.sell_market(
                            price,
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
                    operation="FUTURES SL LIMIT SELL",
                    money=self.money,
                    price=price,
                    quantity=quantity,
                    error=exception,
                    traceback=traceback_str
                )
        return buy

    def stop_loss_limit_buy(self, stop, quantity):
        price = format_decimals(stop)
        self.cancel_all_open_orders()
        print("FUTURES SL LIMIT PRICE BUY: ", price)
        sell = None
        if price > 0:
            exception = ""
            traceback_str = ""
            try:
                quantity = format_decimals(quantity)
                print("FUTURES SL LIMIT BUY: ", self.pair, quantity, price)
                # Change if you need to trade with longs
                position = float(self.get_position_information()[-1]["positionAmt"])
                position_type = "short" if position < 0 else "long"
                if position_type != "short":
                    raise Exception("No short position opened to close")
                quantity_position_open = format_decimals(abs(position))
                if quantity_position_open < quantity * 0.9:
                    raise Exception("Short position to close is too low")
                # Change if you need to trade with longs
                sell = self.client.futures_create_order(
                    symbol=self.pair,
                    positionSide="BOTH",
                    side="BUY",
                    type= "STOP_MARKET",
                    stopPrice=price,
                    quantity=quantity
                )
            except BinanceAPIException as e:
                if e.code == -2021 and e.message == "Order would immediately trigger.":
                        self.buy_market(
                            price,
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
                    operation="FUTURES SL LIMIT BUY",
                    money=self.money,
                    price=price,
                    quantity=quantity,
                    error=exception,
                    traceback=traceback_str
                )
        return sell

    def get_open_orders(self):
        return self.client.futures_get_open_orders(
            symbol=self.pair
        )

    def get_position_information(self):
        return self.client.futures_position_information(
            symbol=self.pair
        )

    def get_coin1_balance(self):
        balances = self.client.futures_account_balance()
        balance = 0
        for i in balances:
            if i["asset"] == self.coin1:
                balance = float(i["balance"])
                break
        return balance

    def get_mark_price(self):
        return float(self.client.futures_mark_price(
            symbol=self.pair
        )["markPrice"])
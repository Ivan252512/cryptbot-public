from ast import If
import math


class SimulateBasicWallet:
    def __init__(self, *args, **kwargs):
        self.coin_1_balance = 0
        self.coin_2_balance = 0

    def deposit_coin_1(self, _quantity):
        if _quantity > 0:
            self.coin_1_balance += _quantity
            return True
        return False

    def buy_coin_2(self, _quantity_sell_coin_1, _quantity_buy_coin_2):
        if _quantity_sell_coin_1 > 0 and self.coin_1_balance >= _quantity_sell_coin_1:
            self.coin_1_balance -= _quantity_sell_coin_1
            self.coin_2_balance += _quantity_buy_coin_2 * (1 - 0.001)
            return True
        return False

    def sell_coin_1(self, _quantity_sell_coin_1, _quantity_buy_coin_2):
        return self. buy_coin_2(_quantity_sell_coin_1, _quantity_buy_coin_2)

    def sell_coin_2(self, _quantity_buy_coin_1, _quantity_sell_coin_2):
        if _quantity_sell_coin_2 > 0 and self.coin_2_balance >= _quantity_sell_coin_2:
            self.coin_2_balance -= _quantity_sell_coin_2
            self.coin_1_balance += _quantity_buy_coin_1 * (1 - 0.001)
            return True
        return False

    def buy_coin_1(self, _quantity_buy_coin_1, _quantity_sell_coin_2):
        return self.sell_coin_2(_quantity_buy_coin_1, _quantity_sell_coin_2)

    def get_total_balance_in_coin1(self, _change_value):
        return self.coin_1_balance + self.coin_2_balance * _change_value

    def get_total_balance_in_coin2(self, _change_value):
        return self.coin_2_balance + self.coin_1_balance * _change_value

    def get_balance_in_coin1(self):
        return self.coin_1_balance

    def get_balance_in_coin2(self):
        return self.coin_2_balance

    def get_all_balances(self):
        return {
            'coin_1': self.coin_1_balance,
            'coin_2': self.coin_2_balance
        }

    def restart(self):
        self.coin_1_balance = 0
        self.coin_2_balance = 0

class SimulateShortWallet():
    
    def __init__(self):
        self.coin_1_got = 0
        self.coin_2_sold = 0

    def deposit_coin_1(self, _quantity):
        if _quantity > 0:
            self.coin_1_got += _quantity
            return True
        return False

    def buy_coin_2(self, _quantity_buy_coin_1, _quantity_pay_coin_2, _price):
        if (
            _quantity_pay_coin_2 <= 0 or 
            _quantity_buy_coin_1 <= 0 or
            _quantity_pay_coin_2 < self.coin_2_sold
            ):
            return False
        self.coin_1_got += (self.coin_1_got - _quantity_buy_coin_1) * (1 - 0.001)
        self.coin_2_sold -= _quantity_pay_coin_2
        return True


    def sell_coin_2(self, _quantity_sell_coin_1, _quantity_debt_coin_2):
        if (
            _quantity_sell_coin_1 <= 0 or 
            _quantity_debt_coin_2 <= 0 or
            self.coin_1_got < _quantity_sell_coin_1
            ):
            return False
        self.coin_1_got = _quantity_sell_coin_1 * (1 - 0.001)
        self.coin_2_sold = _quantity_debt_coin_2
        return True

    def get_balance_in_coin1(self, price):
        return self.get_total_balance_in_coin1(price)

    def get_debt_in_coin2(self):
        return self.coin_2_sold

    def get_total_balance_in_coin1(self, _change_value):
        total = 0
        if self.coin_2_sold > 0:
            total = 2 * self.coin_1_got - self.coin_2_sold * _change_value
        else:
            total = self.coin_1_got - self.coin_2_sold * _change_value
        return total

    def get_total_balance_in_coin2(self, _change_value):
        return self.coin_2_sold  + self.coin_1_got / _change_value

    def get_all_balances(self):
        return {
            'coin_1_got': self.coin_1_got,
            'coin_2_sold': self.coin_2_sold
        }
 
    def restart(self):
        self.coin_1_got = 0
        self.coin_2_sold = 0

class SimulateMarket:
    def __init__(self, _data, type="long"):
        self.data = _data
        self.type = type

    def transaction_at_moment_buy_coin2(self, quantity, moment):
        column = "open"
        for t_price in self.data[column]:
            if moment == 0:
                return quantity / t_price, t_price
            moment -= 1
        return 0, 0

    def transaction_at_moment_sell_coin2(self, quantity, moment):
        column = "low" if self.type == "long" else "high"
        for t_price in self.data[column]:
            if moment == 0:
                return quantity * t_price, t_price
            moment -= 1
        return 0, 0

    def transaction_at_price_buy_coin2(self, quantity, price):
        return quantity * price

    def transaction_at_price_sell_coin2(self, quantity, price):
        if quantity <= 0:
            return 0
        print(quantity, price, price / quantity)
        return price / quantity

    def get_price_at_x_position(self, position):
        column = "close"
        return self.data[column][position]


class SimulateShort:
    def __init__(self):
        self.price_at_short = 0
        self.total_shorted = 0
        
    def short(self, _price_at_short, _total_shorted):
        self.restart()
        self.price_at_short = _price_at_short
        self.total_shorted = _total_shorted
        
    def close(self, _price_at_close):
        total_at_open = self.price_at_short * self.total_shorted
        total_at_close = _price_at_close * self.total_shorted
        self.restart()
        return total_at_close - total_at_open
    
    def __restart(self):
        self.price_at_short = 0
        self.total_shorted = 0
        
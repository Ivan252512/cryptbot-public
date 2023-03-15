from pickle import FALSE, TRUE
from tkinter.tix import Tree
from apps.trades.ia.utils.utils import (
    SimulateBasicWallet,
    SimulateShortWallet,
    SimulateMarket
)

from apps.trades.ia.binance_client_utils.spot import Spot
from apps.trades.ia.binance_client_utils.futures import Futures

from apps.trades.ia.genetic_algorithm.ag import GeneticAlgorithm

from apps.trades.binance.client import Client


from apps.trades.binance.exceptions import BinanceAPIException
from apps.trades.models import Individual as IndividualModel
import math

import traceback
import numpy as np

import pandas as pd
import json
from django.http import JsonResponse

from apps.trades.ia.basic_trading.trader import (
    TraderBTCBUSD,
    TraderETHBUSD,
    TraderADABUSD,
    TraderBNBBUSD,
    TraderBUSDUSDT,
    TraderSHIBBUSD
)

import time

PAIR_INFO = {
    "BTCBUSD": {
        "trader_class": TraderBTCBUSD,
        "coin1": "BUSD",
        "coin2": "BTC"
    },
    "BNBBUSD": {
        "trader_class": TraderBNBBUSD,
        "coin1": "BUSD",
        "coin2": "BNB"
    },
    "ETHBUSD": {
        "trader_class": TraderETHBUSD,
        "coin1": "BUSD",
        "coin2": "ETH"
    },
    "ADABUSD": {
        "trader_class": TraderADABUSD,
        "coin1": "BUSD",
        "coin2": "ADA"
    },
    "BUSDUSDT": {
        "trader_class": TraderBUSDUSDT,
        "coin1": "BUSD",
        "coin2": "USDT"
    },
    "SHIBBUSD": {
        "trader_class": TraderSHIBBUSD,
        "coin1": "BUSD",
        "coin2": "SHIB"
    }
}


class Individual:

    def __init__(self):
        self.relevant_info = []
        self.relevant_info_short = []
        self.money_ts = []
        self.money_ts_short = []
        self.score = 0
        self.score_long = 0
        self.score_short = 0

    def add_relevant_info(self, _info):
        self.relevant_info.append(_info)

    def add_relevant_info_short(self, _info):
        self.relevant_info_short.append(_info)


class BackTesting:
    def __init__(self,
                 _environment,
                 _stop_loss_percent,
                 _stop_loss_divisor_plus,
                 _stop_loss_percent_short,
                 _stop_loss_divisor_plus_short,
                 _keys,
                 _interval
                 ):
        self.environment = _environment
        self.periods_environment = len(_environment)
        self.stop_loss_percent = _stop_loss_percent
        self.stop_loss_divisor_plus = _stop_loss_divisor_plus
        self.stop_loss_percent_short = _stop_loss_percent_short
        self.stop_loss_divisor_plus_short = _stop_loss_divisor_plus_short
        self.keys = _keys
        self.interval = _interval
        self.ema_trend = []
        self.ema_trend_extrapolate = []
        self.low = []
        self.high = []
        self.open = []
        self.close = []
        self.ema_10 = []
        self.ema_55 = []
        self.max = []
        self.min = []
        self.max_min_trend = []
        self.sm_colors = []
        self.adx = []

    def test(self, _data):

        individual = Individual()
        market = _data['market']
        market_short = _data['market_short']
        initial_amount = _data['initial_amount']
        sl_percent = self.stop_loss_percent
        sl_divisor_plus = self.stop_loss_divisor_plus
        sl_percent_short = self.stop_loss_percent_short
        sl_divisor_plus_short = self.stop_loss_divisor_plus_short

        _wallet = SimulateBasicWallet()
        _wallet.deposit_coin_1(initial_amount)

        _short_wallet = SimulateShortWallet()
        _short_wallet.deposit_coin_1(initial_amount)

        evaluation = self.__evaluate_backward()
        for e in evaluation:
            if True:  # e["position_time"] <= self.periods_environment:
                if e["buy_open"]:
                    # Basic wallet
                    coin_1_quantity = _wallet.get_balance_in_coin1()
                    if coin_1_quantity > 10:
                        coin_2_quantity, coin_2_price = market.transaction_at_moment_buy_coin2(
                            coin_1_quantity, e['position_time'])
                        if _wallet.buy_coin_2(coin_1_quantity, coin_2_quantity):
                            individual.add_relevant_info({
                                'coin_1_sell_quantity': coin_1_quantity,
                                'coin_2_buy_quantity': coin_2_quantity,
                                'coin_2_buy_price': coin_2_price,
                                'position_time': e['position_time'],
                                'balance_coin_1': _wallet.get_balance_in_coin1(),
                                'balance_coin_2': _wallet.get_balance_in_coin2(),
                                'stop_loss': [coin_2_price * (1 - sl_percent)]
                            })
                if e["sell_close"]:
                    coin_2_quantity = _short_wallet.get_debt_in_coin2()
                    if coin_2_quantity > 0:
                        coin_1_quantity_market, coin_2_price_market = market_short.transaction_at_moment_sell_coin2(
                            coin_2_quantity, e['position_time'])
                        if _short_wallet.buy_coin_2(coin_1_quantity_market, coin_2_quantity, coin_2_price_market):
                            individual.add_relevant_info_short({
                                'coin_1_buy_quantity': coin_1_quantity_market,
                                'coin_2_sell_quantity': coin_2_quantity,
                                'coin_2_sell_price': coin_2_price_market,
                                'position_time': e['position_time'],
                                'balance_coin_1': _short_wallet.get_balance_in_coin1(coin_2_price_market),
                                'balance_coin_2': _short_wallet.get_debt_in_coin2()
                            })

                if e["buy_close"]:
                    # Basic wallet
                    coin_2_quantity = _wallet.get_balance_in_coin2()
                    if coin_2_quantity > 0:
                        coin_1_quantity_market, coin_2_price_market = market.transaction_at_moment_sell_coin2(
                            coin_2_quantity, e['position_time'])
                        if _wallet.sell_coin_2(coin_1_quantity_market, coin_2_quantity):
                            individual.add_relevant_info({
                                'coin_1_buy_quantity': coin_1_quantity_market,
                                'coin_2_sell_quantity': coin_2_quantity,
                                'coin_2_sell_price': coin_2_price_market,
                                'position_time': e['position_time'],
                                'balance_coin_1': _wallet.get_balance_in_coin1(),
                                'balance_coin_2': _wallet.get_balance_in_coin2()
                            })
                if e["sell_open"]:
                    coin_1_quantity = _short_wallet.get_balance_in_coin1(0)
                    if coin_1_quantity > 10:
                        coin_2_quantity, coin_2_price = market_short.transaction_at_moment_buy_coin2(
                            coin_1_quantity, e['position_time'])
                        if _short_wallet.sell_coin_2(coin_1_quantity, coin_2_quantity):
                            individual.add_relevant_info_short({
                                'coin_1_sell_quantity': coin_1_quantity,
                                'coin_2_buy_quantity': coin_2_quantity,
                                'coin_2_buy_price': coin_2_price,
                                'position_time': e['position_time'],
                                'balance_coin_1': _short_wallet.get_balance_in_coin1(coin_2_price),
                                'balance_coin_2': _short_wallet.get_debt_in_coin2(),
                                'stop_loss': [coin_2_price * (1 + sl_percent_short)]
                            })

                if len(individual.relevant_info) > 0 and "coin_1_sell_quantity" in individual.relevant_info[-1]:
                    _, coin_2_last_price_price = market.transaction_at_moment_sell_coin2(
                        0, e['position_time'])
                    _, coin_2_last_price_price_high = market_short.transaction_at_moment_sell_coin2(
                        0, e['position_time'])
                    sl = individual.relevant_info[-1]["stop_loss"][-1]
                    if coin_2_last_price_price <= sl:
                        coin_2_quantity = _wallet.get_balance_in_coin2()
                        if coin_2_quantity > 0:
                            coin_2_price_market = coin_2_last_price_price if sl > coin_2_last_price_price_high else sl
                            coin_1_quantity_market = market.transaction_at_price_buy_coin2(
                                coin_2_quantity, coin_2_price_market)
                            if _wallet.sell_coin_2(coin_1_quantity_market, coin_2_quantity):
                                individual.add_relevant_info({
                                    'coin_1_buy_quantity': coin_1_quantity_market,
                                    'coin_2_sell_quantity': coin_2_quantity,
                                    'coin_2_sell_price': coin_2_price_market,
                                    'position_time': e['position_time'],
                                    'balance_coin_1': _wallet.get_balance_in_coin1(),
                                    'balance_coin_2': _wallet.get_balance_in_coin2()
                                })
                    else:
                        individual.relevant_info[-1]["stop_loss"].append(
                            individual.relevant_info[-1]["stop_loss"][-1] * (1 + (sl_divisor_plus)))

                if len(individual.relevant_info_short) > 0 and "coin_1_sell_quantity" in individual.relevant_info_short[-1]:
                    _, coin_2_last_price_price = market_short.transaction_at_moment_sell_coin2(
                        0, e['position_time'])
                    _, coin_2_last_price_price_low = market.transaction_at_moment_sell_coin2(
                        0, e['position_time'])
                    sl = individual.relevant_info_short[-1]["stop_loss"][-1]
                    if coin_2_last_price_price >= sl:
                        coin_2_quantity = _short_wallet.get_debt_in_coin2()
                        if coin_2_quantity > 0:
                            coin_2_price_market = coin_2_last_price_price if sl < coin_2_last_price_price_low else sl
                            coin_1_quantity_market = market_short.transaction_at_price_buy_coin2(
                                coin_2_quantity, coin_2_price_market)
                            if _short_wallet.buy_coin_2(coin_1_quantity_market, coin_2_quantity, coin_2_price_market):
                                individual.add_relevant_info_short({
                                    'coin_1_buy_quantity': coin_1_quantity_market,
                                    'coin_2_sell_quantity': coin_2_quantity,
                                    'coin_2_sell_price': coin_2_price_market,
                                    'position_time': e['position_time'],
                                    'balance_coin_1': _short_wallet.get_balance_in_coin1(coin_2_price_market),
                                    'balance_coin_2': _short_wallet.get_debt_in_coin2()
                                })
                    else:
                        individual.relevant_info_short[-1]["stop_loss"].append(
                            individual.relevant_info_short[-1]["stop_loss"][-1] * (1 - (sl_divisor_plus_short)))

            individual.money_ts.append(_wallet.get_total_balance_in_coin1(
                market.get_price_at_x_position(e["position_time"])))
            individual.money_ts_short.append(_short_wallet.get_total_balance_in_coin1(
                market_short.get_price_at_x_position(e["position_time"])))
        individual.score_long = individual.money_ts[-1]
        individual.score_short = individual.money_ts_short[-1]
        individual.score = individual.score_long + individual.score_short
        return individual

    # TODO: MIN MIN CONDITION

    # TODO CERRAR MAX MIN COND MINIMO MINIMO MAXIMO MAXIMO

    def __evaluate_backward(self):
        to_test_2 = [
            {
                'position_time': i,
                'buy_open': False,
                'buy_close': False,
                'sell_open': False,
                'sell_close': False
            } for i in range(self.interval)
        ]
        position = self.interval
        interval = self.interval
        length_environment = len(self.environment)
        while position < length_environment:
            var = {}
            for k in range(len(self.keys)):
                var[self.keys[k]] = []
                for se in self.environment[position-interval:position]:
                    var[self.keys[k]] += [se[k]]
            buy_open, buy_close, sell_open, sell_close = self.global_condition(
                var, position)

            if buy_open and buy_close:
                buy_open = False
                buy_close = False

            if sell_open and sell_close:
                sell_open = False
                sell_close = False

            to_test_2.append(
                {
                    'position_time': position,
                    'buy_open': buy_open,
                    'buy_close': buy_close,
                    'sell_open': sell_open,
                    'sell_close': sell_close
                }
            )
            position += 1
        return to_test_2

    def global_condition(self, var, position):
        prices = {
            'low': var["low"],
            'high': var["high"],
            'open': var["open"],
            'close': var["close"]
        }
        self.upgrade_prices(prices)

        cross_ema_variables = {
            'crossing_1': var["crossing_1"],
            'crossing_2': var["crossing_2"],
            'ema_10': var["ema_10"],
            'ema_55': var["ema_55"],
            'cross_forward_1': var['cross_forward_1'],
            'cross_forward_2': var['cross_forward_2']
        }
        self.upgrade_ema_condition(cross_ema_variables)

        max_min_variables_update = {
            'max': var["max"],
            'min': var["min"],
        }
        self.upgrade_max_min_condition(max_min_variables_update)

        adx_variables_update = {
            'ADX': var["ADX"],
        }
        self.upgrade_adx_condition(adx_variables_update)

        squeeze_momentum_update = {
            'sq_colors': var["sq_colors"],
        }
        self.squeeze_momentum_update(squeeze_momentum_update)

        buy_open, buy_close, sell_open, sell_close = False, False, False, False
        if position < 50:
            return buy_open, buy_close, sell_open, sell_close

        ema_variables = {
            'ema_10': var["ema_10"],
            'ema_55': var["ema_55"]
        }

        buy_open_0, buy_close_0, sell_open_0, sell_close_0 = self.ema_condition(
            ema_variables)

        buy_open = buy_open_0
        buy_close = buy_close_0
        sell_open = sell_open_0
        sell_close = sell_close_0

        return buy_open, buy_close, sell_open, sell_close

    def upgrade_prices(self, prices):
        low = prices["low"]
        high = prices["high"]
        open = prices["open"]
        close = prices["close"]

        if low:
            self.low += [low[-1]]

        if high:
            self.high += [high[-1]]

        if open:
            self.open += [open[-1]]

        if close:
            self.close += [close[-1]]

    def upgrade_ema_condition(self, crossings):
        crossing_1 = crossings["crossing_1"]
        crossing_2 = crossings["crossing_2"]

        crossing_1_forward = crossings["cross_forward_1"]
        crossing_2_forward = crossings["cross_forward_2"]

        if len(crossing_1) > 0 and len(crossing_1) > 0:
            if not math.isnan(crossing_1[-1]):
                self.ema_trend += ["sell"]
            elif not math.isnan(crossing_2[-1]):
                self.ema_trend += ["buy"]
            else:
                if self.ema_trend:
                    self.ema_trend += [self.ema_trend[-1]]

        if len(crossing_1_forward) > 0 and len(crossing_2_forward) > 0:
            if not math.isnan(crossing_1_forward[-1]):
                self.ema_trend_extrapolate += ["sell"]
            elif not math.isnan(crossing_2_forward[-1]):
                self.ema_trend_extrapolate += ["buy"]
            else:
                if self.ema_trend_extrapolate:
                    self.ema_trend_extrapolate += [
                        self.ema_trend_extrapolate[-1]]

    def squeeze_momentum_update(self, sq_colors):
        if sq_colors["sq_colors"]:
            self.sm_colors += [sq_colors["sq_colors"][-1]]

    def upgrade_max_min_condition(self, max_min):
        max = max_min["max"]
        min = max_min["min"]

        if len(max) > 0 and not math.isnan(max[-1]):
            self.max += [max[-1]]
            self.max_min_trend += ["sell"]
        elif len(min) > 0 and not math.isnan(min[-1]):
            self.min += [min[-1]]
            self.max_min_trend += ["buy"]
        else:
            if self.max_min_trend:
                self.max_min_trend += [self.max_min_trend[-1]]

    def upgrade_adx_condition(self, adx_values):
        adx = adx_values["ADX"]
        if adx:
            self.adx += [adx[-1]]

    def detect_changes_ema_trend_period(self, ema_trend_period):
        first_value = ema_trend_period[0]
        changes = 0
        for e in ema_trend_period:
            if e != first_value:
                changes += 1
            first_value = e
        return changes > 1

    def ema_condition(self, ema_variables, activated=True):
        if not activated:
            return True, True, True, True
        ema_10 = ema_variables["ema_10"]
        ema_55 = ema_variables["ema_55"]

        backward = 20

        # CLOSE CONDITIONS
        # if len(self.ema_trend) > backward:
        #     latest_trends_ema = self.ema_trend[-backward:]
        #     changes = self.detect_changes_ema_trend_period(latest_trends_ema)
        #     if changes:
        #         return False, True, False, True
        # if len(self.ema_trend) > 2:
        #     if self.ema_trend[-1] == "buy" and "sell" == self.ema_trend[-2]:
        #         # if self.adx[-1] < 23:
        #         #    return False, False, False, True
        #         return True, False, False, True
        #     if self.ema_trend[-1] == "sell" and "buy" == self.ema_trend[-2]:
        #         # if self.adx[-1] < 23:
        #         #    return False, True, False, False
        #         return False, True, True, False

        # OPEN CONDITIONS
        if len(self.ema_trend_extrapolate) > backward :
            latest_trends_ema = self.ema_trend_extrapolate[-backward:]
            changes = self.detect_changes_ema_trend_period(latest_trends_ema)
            if not changes:
                if self.ema_trend_extrapolate[-1] == "buy" and "sell" == self.ema_trend_extrapolate[-2]:
                    return True, False, False, True
                if self.ema_trend_extrapolate[-1] == "sell" and "buy" == self.ema_trend_extrapolate[-2]:
                    return False, True, True, False


        # if len(self.min) > 2 and len(self.max) > 2 and self.ema_trend:
        #     if self.ema_trend[-1] == "buy" and self.min[-2] > self.min[-1] and self.max[-2] > self.max[-1] and self.sm_colors[-1] in ['lime', 'maroon']:
        #         return False, True, True, False
        #     if self.ema_trend[-1] == "sell" and self.min[-2] < self.min[-1] and self.max[-2] < self.max[-1] and self.sm_colors[-1] in ['green', 'red']:
        #         return True, False, False, True


        if (ema_10 and
                self.ema_trend and
                self.close and
                len(self.min) > 1
                and len(self.max) > 1
                and self.max_min_trend and
                self.low and
                self.high and
                self.adx[-1] > 23
                ):
            # ema 55
            if (  # self.ema_trend[-1] == "buy" and
                self.low[-1] <= ema_55[-1] and
                self.max_min_trend[-1] == "buy" and
                not (self.min[-2] > self.min[-1]
                     and self.max[-2] > self.max[-1])
            ):
                # if self.sm_colors[-1] in ['red', 'green']:
                #     return False, False, False, True
                return True, False, False, True
            if (  # self.ema_trend[-1] == "sell" and
                self.high[-1] >= ema_55[-1] and
                self.max_min_trend[-1] == "sell" and
                not (self.min[-2] < self.min[-1]
                     and self.max[-2] < self.max[-1])
            ):
                # if self.sm_colors[-1] in ['lime', 'maroon']:
                #     return False, True, False, False
                return False, True, True, False

            # ema 10
            if (self.ema_trend[-1] == "buy" and
                    self.low[-1] <= ema_10[-1] and
                    not (self.min[-2] > self.min[-1]
                         and self.max[-2] > self.max[-1])
                    ):
                # if self.sm_colors[-1] in ['red', 'green']:
                #     return False, False, False, True
                return True, False, False, True
            if (self.ema_trend[-1] == "sell" and
                    self.high[-1] >= ema_10[-1] and
                    not (self.min[-2] < self.min[-1]
                         and self.max[-2] < self.max[-1])
                    ):
                # if self.sm_colors[-1] in ['lime', 'maroon']:
                #     return False, True, False, False
                return False, True, True, False

        return False, False, False, False

    def fibo_condition(self, fibos):
        buy = True
        sell = True
        return buy, sell

    def profile_volume_condition(self):
        buy = True
        sell = True
        return buy, sell


class Strategy:

    def __init__(self, client):
        self.periods = ['1m', '5m', '15m', '1h', '4h', '1d']
        self.traders_per_period = []
        self.info_to_invest = {}
        self.client = client
        self.past_positions = 1

    def backtesting(self, info, origin="not_ga", klines=None):

        fields = [
            "principal_trade_period",
            "money",
            "stop_loss_percent",
            "stop_loss_divisor_plus",
            "stop_loss_percent_short",
            "stop_loss_divisor_plus_short",
            "pair",
            "periods_environment",
            "interval",
        ]

        fields_to_func = {}
        body = {}
        if type(info) == dict:
            body = info
        else:
            body = json.loads(info)
        for f in fields:
            if f not in body:
                raise Exception(f'Falta campo {f} en el body')
            fields_to_func[f"{f}"] = body[f]

        PIC = PAIR_INFO[fields_to_func["pair"]]
        fields_to_func["trader_class"] = PIC["trader_class"]
        fields_to_func["coin1"] = PIC["coin1"]
        fields_to_func["coin2"] = PIC["coin2"]

        for f in fields_to_func:
            setattr(self, f, fields_to_func[f])

        self.trader = self.trader_class(
            _trading_interval=self.principal_trade_period,
            _money=self.money,
            _origin=origin,
            _klines=klines,
            _client=self.client
        )
        self.trader.prepare_data(
            _periods=self.periods_environment,
            _graphic=False
        )
        data = self.trader.graphic.get_processed_data()
        environment = data.values.tolist()
        keys = data.keys()

        # Market info
        self.market = SimulateMarket(
            _data=data,
            type="long"
        )

        self.market_short = SimulateMarket(
            _data=data,
            type="short"
        )

        bt = BackTesting(
            _environment=environment,
            _stop_loss_percent=self.stop_loss_percent,
            _stop_loss_divisor_plus=self.stop_loss_divisor_plus,
            _stop_loss_percent_short=self.stop_loss_percent_short,
            _stop_loss_divisor_plus_short=self.stop_loss_divisor_plus_short,
            _keys=keys,
            _interval=self.interval
        )

        data = {
            "market": self.market,
            "market_short": self.market_short,
            "initial_amount": self.money,
        }

        best = bt.test(data)

        return best

    def run_klines_to_save(self, info):
        fields = [
            "principal_trade_period",
            "money",
            "periods_environment",
            "pair"
        ]

        fields_to_func = {}
        body = {}
        if type(info) == dict:
            body = info
        else:
            body = json.loads(info)
        for f in fields:
            if f not in body:
                raise Exception(f'Falta campo {f} en el body')
            fields_to_func[f"{f}"] = body[f]

        PIC = PAIR_INFO[fields_to_func["pair"]]
        fields_to_func["trader_class"] = PIC["trader_class"]
        fields_to_func["coin1"] = PIC["coin1"]
        fields_to_func["coin2"] = PIC["coin2"]

        trader = fields_to_func["trader_class"](
            _trading_interval=fields_to_func["principal_trade_period"],
            _money=fields_to_func["money"],
            _origin="ga",
            _client=self.client
        )

        trader.get_pair_klines_info(
            fields_to_func["periods_environment"]
        )

    def eval_function(self, info, ga=False):

        if ga:
            pair = info.get('pair', False)
            principal_trade_period = info.get('principal_trade_period', False)
            periods_environment = info.get('periods_environment', False)
            money = info.get('money', False)

            if pair and principal_trade_period:
                exists = IndividualModel.objects.filter(
                    pair=pair,
                    principal_trade_period=principal_trade_period
                ).exists()
                if exists:
                    info_db = IndividualModel.objects.filter(
                        pair=pair,
                        principal_trade_period=principal_trade_period
                    ).last()
                    info = json.loads(info_db.variables)
                    info["periods_environment"] = periods_environment
                    info["money"] = money

        print("---------------------INFO----------------------------------")
        print(info)
        print("---------------------INFO----------------------------------")

        best = self.backtesting(info)

        last_operation, last_operation_short = self.trader.graphic.process_data_received_not_ai(
            best.relevant_info,
            best.relevant_info_short,
            best.money_ts,
            best.money_ts_short
        )

        self.info_to_invest = {
            'score': best.score,
            'score_long': best.score_long,
            'score_short': best.score_short,
            'operations': best.relevant_info,
            'last_operation': last_operation,
            'last_operation_short': last_operation_short
        }

        self.traders_per_period.append(
            {
                'period': self.principal_trade_period,
                'trader': self.trader,
                'info': self.info_to_invest
            }
        )

    @classmethod
    def train_function_ga(cls, info, ga_info, klines):
        fields_to_optimize = {}
        principal_trade_period = info["principal_trade_period"]
        print("-----------------principal_trade_period------------------------",
              principal_trade_period)
        if principal_trade_period in ["1d", "4h"]:
            fields_to_optimize = {
                "stop_loss_percent": {
                    "min_value": 0.01,
                    "max_value": 0.1,
                    "length_dna": 32
                },
                "stop_loss_divisor_plus": {
                    "min_value": 0.001,
                    "max_value": 0.1,
                    "length_dna": 32
                },
                "stop_loss_percent_short": {
                    "min_value": 0.01,
                    "max_value": 0.1,
                    "length_dna": 32
                },
                "stop_loss_divisor_plus_short": {
                    "min_value": 0.001,
                    "max_value": 0.11,
                    "length_dna": 32
                },
                "interval": {
                    "min_value": 1,
                    "max_value": 20,
                    "length_dna": 8
                }
            }
        if principal_trade_period in ["1h", "4h"]:
            fields_to_optimize = {
                "stop_loss_percent": {
                    "min_value": 0.002,
                    "max_value": 0.02,
                    "length_dna": 32
                },
                "stop_loss_divisor_plus": {
                    "min_value": 0.001,
                    "max_value": 0.01,
                    "length_dna": 32
                },
                "stop_loss_percent_short": {
                    "min_value": 0.002,
                    "max_value": 0.02,
                    "length_dna": 32
                },
                "stop_loss_divisor_plus_short": {
                    "min_value": 0.001,
                    "max_value": 0.01,
                    "length_dna": 32
                },
                "interval": {
                    "min_value": 1,
                    "max_value": 20,
                    "length_dna": 8
                }
            }
        if principal_trade_period in ["1m", "5m", "15m"]:
            fields_to_optimize = {
                "stop_loss_percent": {
                    "min_value": 0.001,
                    "max_value": 0.005,
                    "length_dna": 32
                },
                "stop_loss_divisor_plus": {
                    "min_value": 0.0001,
                    "max_value": 0.005,
                    "length_dna": 32
                },
                "stop_loss_percent_short": {
                    "min_value": 0.005,
                    "max_value": 0.001,
                    "length_dna": 32
                },
                "stop_loss_divisor_plus_short": {
                    "min_value": 0.0001,
                    "max_value": 0.005,
                    "length_dna": 32
                },
                "interval": {
                    "min_value": 1,
                    "max_value": 20,
                    "length_dna": 8
                }
            }

        for i in fields_to_optimize.keys():
            if i in info:
                info.pop(i)

        if type(ga_info) == str:
            ga_info = json.loads(ga_info)

        client = Client()

        ga = GeneticAlgorithm(
            _population_min=ga_info["population_min"],
            _population_max=ga_info["population_max"],
            _individual_encoded_variables=fields_to_optimize,
            _individual_muatition_intensity=ga_info["individual_muatition_intensity"],
            _strategy=cls,
            _klines=klines,
            _client=client
        )

        score, score_long, score_short, variables, best_individual = ga.evolution(
            generations=ga_info["generations"],
            static_info=info
        )

        print(
            "score: ", score,
            "score_short: ", score_short,
            "score_long: ", score_long,
            "constants: ", variables,
            "best_individual: ", best_individual
        )

        strategy = cls(client=client)
        strategy.eval_function(variables)
        strategy.graph_data()

        IndividualModel.objects.create(
            score=score,
            variables=json.dumps(variables),
            principal_trade_period=strategy.principal_trade_period,
            pair=strategy.pair,
        )

        return variables

    def graph_data(self):
        for t in self.traders_per_period:
            if t['info']:
                t['trader'].graphic.graph_for_evaluated_not_ai(
                    self.money,
                    t['info']['score'],
                    t['info']['score_long'],
                    t['info']['score_short'],
                    t['info']['last_operation']
                )

    def invest_spot(self):
        spot = Spot(
            self.client,
            self.pair,
            self.stop_loss_divisor_plus,
            self.stop_loss_percent,
            self.coin1,
            self.coin2
        )

        if not spot.set_money(self.money):
            print("NOT MONEY SETTED SPOT")

        order = self.info_to_invest['last_operation']
        print("------------------SPOT-------------------------")
        print(order)
        print("-------------------------------------------")
        position_time = order['position_time']
        position_time_with_sl = order['position_with_sl']
        last_sl_price = order['last_sl_price']
        print("Position time: ", position_time,
              "Position time with sl: ", position_time_with_sl,
              "periods_environment: ",  self.periods_environment,
              "past_positions", self.past_positions
              )

        if position_time_with_sl < self.periods_environment - self.past_positions:
            spot.cancel_all_open_orders()
            spot.close_buy()
            return

        quantity = 0
        if int(position_time) >= self.periods_environment - self.past_positions:
            if 'coin_1_sell_quantity' in order:
                increase_sl = False
                buyed_price = 0
                try:
                    buy = spot.buy_market(float(order["coin_2_buy_price"]))
                    print("BUY SPOT: ", buy)
                    if buy:
                        if buy["fills"]:
                            buyed_price = float(buy["fills"][-1]["price"])
                            quantity = float(buy["origQty"])
                    print("buyed_price 1: ", buyed_price)
                except BinanceAPIException as e:
                    pass
                    # if e.code == -2010 and e.message == "Account has insufficient balance for requested action.":
                    #     print("buyed_price 2: ", buyed_price)
                    #     increase_sl = spot.increase_sl()
                    #     # increase_sl = True
                finally:
                    pass
                    # print("buyed_price 3: ", buyed_price)
                    # if not increase_sl and buyed_price > 0 and quantity > 0:
                    #     spot.stop_loss_limit_sell(
                    #         buyed_price * ( 1 - self.stop_loss_percent ),
                    #         buyed_price * ( 1 - self.stop_loss_percent - 0.005 ),
                    #         quantity
                    #     )
            if 'coin_1_buy_quantity' in order:
                spot.close_buy()
        # else:
        time.sleep(2)
        spot.increase_sl(last_sl_price)

    def invest_long(self):
        futures = Futures(
            self.client,
            self.pair,
            self.stop_loss_divisor_plus,
            self.stop_loss_percent,
            self.coin1
        )

        if not futures.set_money(self.money):
            print("NOT MONEY SETTED LONG")

        order = self.info_to_invest['last_operation']
        print("--------------------LONG-----------------------")
        print(order)
        position_time = order['position_time']
        position_time_with_sl = order['position_with_sl']
        last_sl_price = order['last_sl_price']
        print("Position time: ", position_time,
              "Position time with sl: ", position_time_with_sl,
              "periods_environment: ",  self.periods_environment,
              "past_positions", self.past_positions
              )

        if position_time_with_sl < self.periods_environment - self.past_positions:
            futures.cancel_all_open_orders()
            futures.close_buy()
            return

        quantity = 0
        if int(position_time) >= self.periods_environment - self.past_positions:
            if 'coin_1_sell_quantity' in order:
                increase_sl = False
                buyed_price = 0
                try:
                    buy = futures.buy_market(float(order["coin_2_buy_price"]))
                    print("BUY LONG: ", buy)
                    if buy:
                        if buy["avgPrice"]:
                            buyed_price = float(buy["avgPrice"])
                            quantity = float(buy["executedQty"])
                    print("buyed_price 1: ", buyed_price)
                except BinanceAPIException as e:
                    pass
                    # if ((e.code == -2010 and e.message == "Account has insufficient balance for requested action.") or
                    #     (e.code == -2019 and e.message == "Margin is insufficient.") ):
                    #     increase_sl = futures.increase_sl()
                    #     # increase_sl = True
                    #     print("buyed_price 2: ", buyed_price)
                finally:
                    pass
                    # print("buyed_price 3: ", buyed_price)
                    # if not increase_sl and buyed_price > 0 and quantity > 0:
                    #     futures.stop_loss_limit_sell(
                    #         buyed_price * ( 1 - self.stop_loss_percent ),
                    #         quantity
                    #     )
            if 'coin_1_buy_quantity' in order:
                futures.close_buy()
        # else:
        time.sleep(2)
        futures.increase_sl(last_sl_price)

    def invest_short(self):
        futures = Futures(
            self.client,
            self.pair,
            self.stop_loss_divisor_plus,
            self.stop_loss_percent,
            self.coin1
        )

        if not futures.set_money(self.money):
            print("NOT MONEY SETTED SHORT")

        order = self.info_to_invest['last_operation_short']
        print("-------------------SHORT------------------------")
        print(order)
        position_time = order['position_time']
        position_time_with_sl = order['position_with_sl']
        last_sl_price = order['last_sl_price']
        print("Position time: ", position_time,
              "Position time with sl: ", position_time_with_sl,
              "periods_environment: ",  self.periods_environment,
              "past_positions", self.past_positions
              )

        if position_time_with_sl < self.periods_environment - self.past_positions:
            futures.cancel_all_open_orders()
            futures.close_sell()
            return

        quantity = 0
        if int(position_time) >= self.periods_environment - self.past_positions:
            if 'coin_1_sell_quantity' in order:
                decrease_sl = False
                sold_price = 0
                try:
                    sell = futures.sell_market(
                        float(order["coin_2_buy_price"]))
                    print("SELL SHORT: ", sell)
                    if sell:
                        if sell["avgPrice"]:
                            sold_price = float(sell["avgPrice"])
                            quantity = float(sell["executedQty"])
                    print("sold_price 1: ", sold_price)
                except BinanceAPIException as e:
                    pass
                    # if ((e.code == -2010 and e.message == "Account has insufficient balance for requested action.") or
                    #     (e.code == -2019 and e.message == "Margin is insufficient.") ):
                    #     decrease_sl = futures.decrease_sl()
                    #     # decrease_sl = True
                    #     print("sold_price 2: ", sold_price)
                finally:
                    pass
                    # print("sold_price 3: ", sold_price)
                    # if not decrease_sl and sold_price > 0 and quantity > 0:
                    #     futures.stop_loss_limit_buy(
                    #         sold_price * ( 1 + self.stop_loss_percent ),
                    #         quantity
                    #     )
            if 'coin_1_buy_quantity' in order:
                futures.close_sell()
        # else:
        time.sleep(2)
        futures.decrease_sl(last_sl_price)

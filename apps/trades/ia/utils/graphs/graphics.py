from apps.trades.ia.binance_client_utils.utils import format_decimals
import mplfinance as fplt
import pandas as pd
import datetime

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.stats import linregress

import datetime
from pathlib import Path



# https://www.geeksforgeeks.org/plot-candlestick-chart-using-mplfinance-module-in-python/
# https://coderzcolumn.com/tutorials/data-science/candlestick-chart-in-python-mplfinance-plotly-bokeh

class Graphic:

    def __init__(self, _raw_data, _pair, _trading_interval):
        self.raw_data = _raw_data
        self.length = len(_raw_data)
        self.trading_interval = _trading_interval
        self.pair = _pair
        self.processed_data = None
        self.cross_ma = []
        self.ma = None 
        self.graphic = None 
        self.indicators = []
        self.maxs_columns = []
        self.mins_columns = []
        self.exclude_to_ag = ["open", "low", "high", "close", "volume"]
        self.graph_ag = []
        self.not_to_graph_indicators = []
        self.fibos = [0, 0.236, 0.382, 0.500, 0.618, 0.786, 1, 1.618]
        self.volume_profile = None
        self.bucket_size_mult = 0.025
        
    def process_data(self):
        
        all_data = []
        
        for data in self.raw_data:
            all_data.append(
                [
                    datetime.datetime.fromtimestamp(data[0] / 1000),
                    float(data[1]),
                    float(data[2]),
                    float(data[3]),
                    float(data[4]),
                    float(data[5]),     
                ]
            )
        
        df = pd.DataFrame(
            all_data,
            columns=[
                "date",
                "open",
                "high",
                "low",
                "close",
                "volume"
            ]
        )
        
        datetime_series = pd.to_datetime(df['date'])
        datetime_index = pd.DatetimeIndex(datetime_series.values)
        
        df2 = df.set_index(datetime_index)
        df2.drop('date', axis=1, inplace=True)
        
        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
        #     print(df2)
        
        self.processed_data = df2

        self.calculate_volume_profile()
        
    def calculate_moving_average(self, _periods):
        self.processed_data['ma_{}'.format(_periods)] = self.processed_data["close"].ewm(span=_periods, adjust=False).mean()
        self.indicators.append('ma_{}'.format(_periods))
        self.cross_ma.append('ma_{}'.format(_periods))
        # self.exclude_to_ag.append('ma_{}'.format(_periods))
        self.graph_ag.append('ma_{}'.format(_periods))

    def _calculate_next(self, values):
        range_x = len(values)
        t = [i for i in range(range_x)]
        reg = linregress(
            x=t,
            y=values
        )
        return (range_x + 1) * reg[0] + reg[1]

    def _evaluate_backward(self, interval, values):
        to_test = [
            values[i] for i in range(interval)
        ]
        position = interval
        interval = interval
        while position < len(values):
            to_test += [self._calculate_next(values[position-interval:position])]
            position += 1
        return to_test

    def process_cross(self, cross, values):
        cross = list(cross)
        values = list(values)
        y = []
        pos = 0
        for c in cross:
            if c == 1 or c == -1:
                y += [values[pos]]
            else:
                y += [np.nan]
            pos += 1
        return y
        
    def extrapolate_ema_cross(self, periods_1, periods_2, interval=3):
        self.processed_data["Differential"] = (
            np.array(self.processed_data[f"ema_{periods_1}"]) - 
            np.array(self.processed_data[f"ema_{periods_2}"])
        )
        self.processed_data["Differential_forward"] = (
            np.array(
                self._evaluate_backward(
                    interval, list(self.processed_data["Differential"])
                )
            )
        )

        df = self.processed_data.copy()
        _df = "Differential_forward"

        self.processed_data["forward_1"] = df[_df][(df[_df] < 0) & (df[_df].shift(-1) > 0)]
        self.processed_data["forward_2"] = df[_df][(df[_df] > 0) & (df[_df].shift(-1) < 0)]

        self.processed_data["cross_forward_1"]  =  self.processed_data["forward_1"]  / abs( self.processed_data["forward_1"] )
        self.processed_data["cross_forward_2"]  =  self.processed_data["forward_2"]  / abs( self.processed_data["forward_2"] )

        self.processed_data["cross_forward_1"]  =  self.process_cross(self.processed_data["cross_forward_1"], self.processed_data[f"ema_{periods_1}"])
        self.processed_data["cross_forward_2"]  =  self.process_cross(self.processed_data["cross_forward_2"], self.processed_data[f"ema_{periods_1}"])

        self.indicators.append("cross_forward_1")
        self.indicators.append("cross_forward_2")
        self.graph_ag.append("cross_forward_1")
        self.graph_ag.append("cross_forward_2")

        
    def calculate_exponential_moving_average(self, _periods, _graphic=True):
        self.processed_data['ema_{}'.format(_periods)] = self.processed_data["close"].ewm(span=_periods,adjust=False).mean()
        if _graphic:
            self.indicators.append('ema_{}'.format(_periods))
            self.graph_ag.append('ema_{}'.format(_periods))
            
    def calculate_squeeze_momentum_lazy_bear(self):
        length = 20
        mult = 2
        length_KC = 20
        mult_KC = 1.5

        m_avg = self.processed_data['close'].rolling(window=length).mean()
        m_std = self.processed_data['close'].rolling(window=length).std(ddof=0)
        self.processed_data['upper_BB'] = m_avg + mult * m_std
        self.processed_data['lower_BB'] = m_avg - mult * m_std

        # calculate true range
        self.processed_data['tr0'] = abs(self.processed_data["high"] - self.processed_data["low"])
        self.processed_data['tr1'] = abs(self.processed_data["high"] - self.processed_data["close"].shift())
        self.processed_data['tr2'] = abs(self.processed_data["low"] - self.processed_data["close"].shift())
        self.processed_data['tr'] = self.processed_data[['tr0', 'tr1', 'tr2']].max(axis=1)

            
        # calculate KC
        range_ma = self.processed_data['tr'].rolling(window=length_KC).mean()
        self.processed_data['upper_KC'] = m_avg + range_ma * mult_KC
        self.processed_data['lower_KC'] = m_avg - range_ma * mult_KC

        # calculate bar value squeeze
        highest = self.processed_data['high'].rolling(window = length_KC).max()
        lowest = self.processed_data['low'].rolling(window = length_KC).min()
        m1 = (highest + lowest)/2
        self.processed_data['squeeze'] = (self.processed_data['close'] - (m1 + m_avg)/2)
        fit_y = np.array(range(0,length_KC))
        self.processed_data['squeeze'] = self.processed_data['squeeze'].rolling(window = length_KC).apply(lambda x: 
                                np.polyfit(fit_y, x, 1)[0] * (length_KC-1) + 
                                np.polyfit(fit_y, x, 1)[1], raw=True)

        del (
            self.processed_data['tr0'],
            self.processed_data['tr1'],
            self.processed_data['tr2'],
            self.processed_data['tr'],
            self.processed_data['upper_KC'],
            self.processed_data['lower_KC'],
            self.processed_data['lower_BB'],
            self.processed_data['upper_BB']
        )

        colors = []

        for ind, val in enumerate(self.processed_data['squeeze']):
            if val >= 0:
                color = 'green'
                if val > self.processed_data['squeeze'][ind-1]:
                    color = 'lime'
            else:
                color = 'maroon'
                if val < self.processed_data['squeeze'][ind-1]:
                    color='red'
            colors.append(color)

        self.processed_data['sq_colors'] = colors

        self.indicators.append('squeeze')
        self.graph_ag.append('squeeze')

        self.indicators.append('sq_colors')
        self.graph_ag.append('sq_colors')
        
    def calculate_adx(self):
        alpha = 1/14
        # TR
        self.processed_data['H-L'] = self.processed_data['high'] - self.processed_data['low']
        self.processed_data['H-C'] = np.abs(self.processed_data['high'] - self.processed_data['close'].shift(1))
        self.processed_data['L-C'] = np.abs(self.processed_data['low'] - self.processed_data['close'].shift(1))
        self.processed_data['TR'] = self.processed_data[['H-L', 'H-C', 'L-C']].max(axis=1)
        del self.processed_data['H-L'], self.processed_data['H-C'], self.processed_data['L-C']

        # ATR
        self.processed_data['ATR'] = self.processed_data['TR'].ewm(alpha=alpha, adjust=False).mean()

        # +-DX
        self.processed_data['H-pH'] = self.processed_data['high'] - self.processed_data['high'].shift(1)
        self.processed_data['pL-L'] = self.processed_data['low'].shift(1) - self.processed_data['low']
        self.processed_data['+DX'] = np.where(
            (self.processed_data['H-pH'] > self.processed_data['pL-L']) & (self.processed_data['H-pH']>0),
            self.processed_data['H-pH'],
            0.0
        )
        self.processed_data['-DX'] = np.where(
            (self.processed_data['H-pH'] < self.processed_data['pL-L']) & (self.processed_data['pL-L']>0),
            self.processed_data['pL-L'],
            0.0
        )
        del self.processed_data['H-pH'], self.processed_data['pL-L']

        # +- DMI
        self.processed_data['S+DM'] = self.processed_data['+DX'].ewm(alpha=alpha, adjust=False).mean()
        self.processed_data['S-DM'] = self.processed_data['-DX'].ewm(alpha=alpha, adjust=False).mean()
        self.processed_data['+DMI'] = (self.processed_data['S+DM']/self.processed_data['ATR'])*100
        self.processed_data['-DMI'] = (self.processed_data['S-DM']/self.processed_data['ATR'])*100
        del self.processed_data['S+DM'], self.processed_data['S-DM']

        # ADX
        self.processed_data['DX'] = (np.abs(self.processed_data['+DMI'] - 
            self.processed_data['-DMI']
            )/(self.processed_data['+DMI'] + 
            self.processed_data['-DMI']))*100
        self.processed_data['ADX'] = self.processed_data['DX'].ewm(alpha=alpha, adjust=False).mean()
        del (
            self.processed_data['DX'], 
            self.processed_data['ATR'], 
            self.processed_data['TR'], 
            self.processed_data['-DX'], 
            self.processed_data['+DX'], 
            self.processed_data['+DMI'], 
            self.processed_data['-DMI']
        )

        self.processed_data['point_23'] = np.full((1, self.length), 23)[0]

        self.indicators.append('ADX')
        self.graph_ag.append('ADX')
        self.indicators.append('point_23')
        self.graph_ag.append('point_23')


    def calculate_volume_profile(self):
        bucket_size = self.bucket_size_mult * max(self.processed_data['close'])
        self.volume_profile = self.processed_data['volume'].groupby(
            self.processed_data['close'].apply(lambda x: bucket_size*round(x/bucket_size,0))).sum()

    def calculate_fibonacci_retracement(self):
        count = 1
        for fb in self.fibos:
            max = self.processed_data['high'].max()
            min = self.processed_data['low'].min() 
            self.processed_data['fr_{}'.format(count)] = [min + fb * (max - min) for _ in self.raw_data]
            self.indicators.append('fr_{}'.format(count))
            self.graph_ag.append('fr_{}'.format(count))
            self.exclude_to_ag.append('fr_{}'.format(count))
            count += 1

    def get_second_derivative(self, _sigma_gaussian_filter):
        # Secdond derivative
        filtered_data_low = gaussian_filter1d(self.processed_data['close'], _sigma_gaussian_filter)
        filtered_data_high = gaussian_filter1d(self.processed_data['close'], _sigma_gaussian_filter)

        self.processed_data['fd_low_{}'.format(_sigma_gaussian_filter)] = filtered_data_low
        # self.processed_data['d2_low_{}'.format(_sigma_gaussian_filter)] = filtered_data_low 
        self.indicators.append('fd_low_{}'.format(_sigma_gaussian_filter))
        self.graph_ag.append('fd_low_{}'.format(_sigma_gaussian_filter))

        self.processed_data['fd_high_{}'.format(_sigma_gaussian_filter)] = filtered_data_high
        # self.processed_data['d2_high_{}'.format(_sigma_gaussian_filter)] = np.gradient(np.gradient(filtered_data_high))
        self.indicators.append('fd_high_{}'.format(_sigma_gaussian_filter))
        self.graph_ag.append('fd_high_{}'.format(_sigma_gaussian_filter))

        self._put_min_respectly_in_data_df('close', 'fd_low_{}'.format(_sigma_gaussian_filter))
        self._put_max_respectly_in_data_df('close', 'fd_high_{}'.format(_sigma_gaussian_filter))

        # del (
        #     self.processed_data['fd_low_{}'.format(_sigma_gaussian_filter)],
        #     self.processed_data['d2_low_{}'.format(_sigma_gaussian_filter)],
        #     self.processed_data['fd_high_{}'.format(_sigma_gaussian_filter)],
        #     self.processed_data['d2_high_{}'.format(_sigma_gaussian_filter)] 
        # )

    def _put_min_respectly_in_data_df(self, _df, _df2):
        df = self.processed_data
        self.processed_data['min'] = df[_df][(df[_df2].shift(1) > df[_df2]) & (df[_df2].shift(-1) > df[_df2])]
        self.indicators.append('min')
        self.graph_ag.append('min')
    
    def _put_max_respectly_in_data_df(self, _df, _df2):
        df = self.processed_data
        self.processed_data['max'] =  df[_df][(df[_df2].shift(1) < df[_df2]) & (df[_df2].shift(-1) < df[_df2])] 
        self.indicators.append('max')
        self.graph_ag.append('max')
    
    def cross_ema(self, ema_1, ema_2):
        previous_15 = self.processed_data[ema_1].shift(1)
        previous_45 = self.processed_data[ema_2].shift(1)

        crossing_1 = ((self.processed_data[ema_1] <= self.processed_data[ema_2]) & (previous_15 >= previous_45))
        crossing_2 = ((self.processed_data[ema_1] >= self.processed_data[ema_2]) & (previous_15 <= previous_45))

        self.processed_data["crossing_1"] = self.processed_data.loc[crossing_1, ema_1]
        self.indicators.append('crossing_1')
        self.graph_ag.append('crossing_1')

        self.processed_data["crossing_2"] = self.processed_data.loc[crossing_2, ema_1]
        self.indicators.append('crossing_2')
        self.graph_ag.append('crossing_2')

    def filled_na(self, column):
        df = self.processed_data.copy()
        for c in column:
            df[c] = df[c].fillna(0)
            df[c] = df[c].mask(df[c] != 0, 1)
        return df

    def get_processed_data(self):
        return self.processed_data.copy()
    
    def get_normalized_processed_data(self):
        df = self.processed_data.copy()
        result = self.processed_data.copy()
        for feature_name in df.columns:
            max_value = df[feature_name].max()
            min_value = df[feature_name].min()
            result[feature_name] = (df[feature_name] - min_value) / (max_value - min_value)
        result = result.replace(np.nan, 0)
        return result
    
    def get_indicators(self):
        return self.indicators.copy()
        
    def graph_for_evaluated_not_ai(self, _initial, _score, _score_long, _score_short, _last_operation, _socialmedia=False):
        subplots = []
        for i in self.graph_ag:
            if "sells" in i:
                #if "short" in i:
                #    continue
                color = 'red' if not "short" in i else "gray"
                subplots.append(
                    fplt.make_addplot(
                        self.processed_data[i],
                        type='scatter',
                        markersize=10,
                        marker='v',
                        color=color,
                        
                    )
                )
            elif "buys" in i:
                # if "short" in i:
                #     continue
                color = 'green' if not "short" in i else "black"
                subplots.append(
                    fplt.make_addplot(
                        self.processed_data[i],
                        type='scatter',
                        markersize=10,
                        marker='^',
                        color=color
                    )
                )
            elif "stop_loss" in i:
                color = 'blue' if not "short" in i else "red"
                subplots.append(
                    fplt.make_addplot(
                        self.processed_data[i],
                        type='scatter',
                        markersize=2,
                        marker='*',
                        color=color
                    )
                )
            elif "money_ts" in i:
                color = 'black' if not "short" in i else "red"
                subplots.append(
                    fplt.make_addplot(
                        self.processed_data[i],
                        type='line',
                        color=color,
                        alpha=0.4
                    )
                )
            else:
                if "max" in i:
                    subplots.append(
                        fplt.make_addplot(
                            self.processed_data[i],
                            type='scatter',
                            markersize=5,
                            color="red",
                            marker='.'
                        )
                    )
                elif "min" in i:
                    subplots.append(
                        fplt.make_addplot(
                            self.processed_data[i],
                            type='scatter',
                            markersize=5,
                            color="green",
                            marker='.'
                        )
                    )
                elif "crossing" in i:
                    subplots.append(
                        fplt.make_addplot(
                            self.processed_data[i],
                            type='scatter',
                            markersize=15,
                            marker='o'
                        )
                    )
                elif "cross_forward" in i:
                    subplots.append(
                        fplt.make_addplot(
                            self.processed_data[i],
                            type='scatter',
                            markersize=10,
                            marker='o'
                        )
                    )
                elif "ema" in i:
                    subplots.append(
                        fplt.make_addplot(
                            self.processed_data[i],
                            type='line',
                        )
                    )
                elif "squeeze" in i:
                    colors = []
                    for ind, val in enumerate(self.processed_data[i]):
                        if val >= 0:
                            color = 'green'
                            if val > self.processed_data[i][ind-1]:
                                color = 'lime'
                        else:
                            color = 'maroon'
                            if val < self.processed_data[i][ind-1]:
                                color='red'
                        colors.append(color)

                    subplots.append(
                        fplt.make_addplot(
                            self.processed_data[i],
                            type='bar',
                            color=colors,
                            panel='lower'
                        )
                    )
                elif "d2_" in i:
                    continue
                    subplots.append(
                        fplt.make_addplot(
                            self.processed_data[i],
                            type='scatter',
                            markersize=5,
                            color="black",
                            marker='.'
                        )
                    )
                elif "ADX" in i:
                    subplots.append(
                        fplt.make_addplot(
                            self.processed_data[i],
                            type='line',
                            color='black',
                            panel='lower'
                        )
                    )
                elif "point_23" in i:
                    subplots.append(
                        fplt.make_addplot(
                            self.processed_data[i],
                            type='line',
                            color='black',
                            panel='lower'
                        )
                    )
                    
        current_date = datetime.datetime.now()
        name_file = current_date.strftime("%m_%d_%Y_%H_%M_%S") + ".jpg"
        ubication_file = "outputs/graphics/{}/{}/{}".format(
                self.pair,
                self.trading_interval,
                name_file
            )
        Path(
            "outputs/graphics/{}/{}/".format(
                self.pair,
                self.trading_interval
            )
        ).mkdir(parents=True, exist_ok=True)
        
        dpi = 150
        if not _socialmedia:
            dpi = 1200 

        lo = ""
        # for k in _last_operation.keys():
        #     if not "balance" in k:
        #         if not "stop_loss" in k:
        #             lo += f"{k}: {_last_operation[k]} "
                    
        lo += f"initial: {_initial}, score: {_score}, long: {_score_long}, short: {_score_short} "
        
        s = fplt.make_mpf_style(base_mpf_style='charles', rc={'font.size':2})
        
        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
        #     print(self.processed_data)

        fig, axlist = fplt.plot(
            self.processed_data,
            type='candle',
            style=s,
            title=lo,
            ylabel='Price ($)',
            ylabel_lower='Shares\nTraded',
            addplot=subplots,
            tight_layout=True,
            returnfig=True
           # savefig=save
        ) 

        bucket_size = self.bucket_size_mult  * max(self.processed_data['close'])
        vpax = fig.add_axes(axlist[0].get_position())
        vpax.set_axis_off()
        vpax.set_xlim(right=5*max(self.volume_profile.values))
        vpax.barh(self.volume_profile.keys().values, self.volume_profile.values, align='center', color='cyan', alpha=0.45)

        fig.savefig(
            ubication_file,
            dpi=dpi
        )

    def process_data_received_not_ai(self, data, data_short, money_ts, money_ts_short):
        buys = [np.nan for _ in range(self.length)]
        sells = [np.nan for _ in range(self.length)]
        count_sl = 0
        for d in data:
            if d['position_time'] < self.length:
                if 'coin_1_sell_quantity' in d:
                    buys[d['position_time']] = d['coin_2_buy_price']
                    stop_loss = [None for _ in range(self.length)]
                    count = 0
                    for sl in d['stop_loss']:
                        if d['position_time'] + count < self.length:
                            stop_loss[d['position_time'] + count] = sl
                        count += 1
                    self.processed_data['stop_loss_{}'.format(count_sl)] = stop_loss
                    self.graph_ag.append('stop_loss_{}'.format(count_sl))
                    count_sl += 1
                elif 'coin_1_buy_quantity' in d:
                    sells[d['position_time']] = d['coin_2_sell_price']

        if not self.all_nan(buys):        
            self.processed_data['buys'] = buys
            self.graph_ag.extend(["buys"])
        if not self.all_nan(sells):     
            self.processed_data['sells'] = sells
            self.graph_ag.extend(["sells"])


        buys = [np.nan for _ in range(self.length)]
        sells = [np.nan for _ in range(self.length)]
        count_sl = 0
        for d in data_short:
            if d['position_time'] < self.length:
                if 'coin_1_sell_quantity' in d:
                    buys[d['position_time']] = d['coin_2_buy_price']
                    stop_loss = [None for _ in range(self.length)]
                    count = 0
                    for sl in d['stop_loss']:
                        if d['position_time'] + count < self.length:
                            stop_loss[d['position_time'] + count] = sl
                        count += 1
                    self.processed_data['stop_loss_short_{}'.format(count_sl)] = stop_loss
                    self.graph_ag.append('stop_loss_short_{}'.format(count_sl))
                    count_sl += 1
                elif 'coin_1_buy_quantity' in d:
                    sells[d['position_time']] = d['coin_2_sell_price']

        if not self.all_nan(buys):        
            self.processed_data['buys_short'] = buys
            self.graph_ag.extend(["buys_short"])
        if not self.all_nan(sells):     
            self.processed_data['sells_short'] = sells
            self.graph_ag.extend(["sells_short"])
        

        self.processed_data['money_ts'] = money_ts
        self.graph_ag.extend(["money_ts"])

        self.processed_data['money_ts_short'] = money_ts_short
        self.graph_ag.extend(["money_ts_short"])

        # self.save_to_excel()
        last = data[-1] if data else {}
        position_with_sl = last.get("position_time", 0)
        sl_list = last.get("stop_loss", [])
        sl = len(sl_list)
        last_sl_price = format_decimals(sl_list[-1]) if sl_list else 0
        if sl > 0:
            sl -= 1
        position_with_sl += sl
        last["position_with_sl"] = position_with_sl
        last["last_sl_price"] = last_sl_price

        last_short = data_short[-1] if data_short else {}
        position_with_sl_short = last_short.get("position_time", 0)
        sl_list_short = last_short.get("stop_loss", [])
        sl_short = len(sl_list_short)
        last_sl_price_short = format_decimals(sl_list_short[-1]) if sl_list_short else 0
        if sl_short > 0:
            sl_short -= 1
        position_with_sl_short += sl_short
        last_short["position_with_sl"] = position_with_sl_short
        last_short["last_sl_price"] = last_sl_price_short
        

        return last, last_short
    
    
    def all_nan(self, arr):
        arr = pd.DataFrame(arr)
        return arr.isnull().values.all(axis=0)
    
    def get_last_ma_period(self, _period):
        return self.processed_data.get(['ma_{}'.format(_period)][-1], None)
    
    def get_fibos(self):
        fibos = []
        count = 1
        for _ in self.fibos:
            fibos.append(self.processed_data.get(['fr_{}'.format(count)][-1], None))
            count += 1
        return fibos

    def save_to_excel(self):
        df = self.filled_na(["min", "max", "crossing_1", "crossing_2"])

        current_date = datetime.datetime.now()
        name_file = current_date.strftime("%m_%d_%Y_%H_%M_%S") + ".csv"
        ubication_file = "outputs/data/{}/{}/{}".format(
                self.pair,
                self.trading_interval,
                name_file
            )
        Path(
            "outputs/data/{}/{}/".format(
                self.pair,
                self.trading_interval
            )
        ).mkdir(parents=True, exist_ok=True)
        df.to_csv(ubication_file)

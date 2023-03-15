from celery import Celery
from celery.schedules import crontab
import datetime
import traceback
from django.http import JsonResponse
import time

from apps.trades.ia.utils.strategies.strategies import Strategy
from apps.trades.models import Klines
from apps.trades.binance.client import Client

app = Celery()

money = 3500
periods_environment = 500
pair = "BTCBUSD"


@app.task
def trade(principal_trade_period):
    print("++++++++++++++++++++++++++++++++++++++++++++")
    print(datetime.datetime.now())
    # time.sleep(290)
    body = {
        "principal_trade_period": principal_trade_period,
        "money": money,
        "pair": pair,
        "periods_environment": periods_environment,
        "ga": True
    }
    try:
        btb = Strategy(client=Client())
        ga = body.pop('ga')
        btb.eval_function(body, ga)

        btb.graph_data()
        btb.invest_spot()
        btb.invest_short()
        return {'message': "Entrenamiento exitoso"}
    except Exception:
        traceback.print_exc()
        return {'message': "Entrenamiento fallido"}


@app.task
def train_ga(principal_trade_period):
    print("++++++++++++++++++++++++++++++++++++++++++++")
    print(datetime.datetime.now())
    # time.sleep(290)
    body = {
        "principal_trade_period": principal_trade_period,
        "money": money,
        "pair": pair,
        "periods_environment": periods_environment,
        "ga_info": {
            "population_min": 50,
            "population_max": 100,
            "individual_muatition_intensity": 60,
            "generations": 500
        }
    }
    try:
        Klines.objects.all().delete()
        client = Client()
        btb = Strategy(client)
        klines = btb.run_klines_to_save(body)
        ga_info = body.pop('ga_info')
        btb.train_function_ga(body, ga_info, klines)
        return {'message': "Entrenamiento exitoso"}
    except Exception:
        traceback.print_exc()
        return {'message': "Entrenamiento fallido"}

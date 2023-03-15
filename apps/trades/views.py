from django.http import JsonResponse
from apps.trades.binance.client import Client


import traceback

from django.views.decorators.csrf import csrf_exempt


import datetime

from django.utils.timezone import make_aware


from apps.trades.ia.utils.strategies.strategies import Strategy
from apps.trades.ia.binance_client_utils.futures import Futures
from apps.trades.ia.binance_client_utils.spot import Spot

from threading import Thread

from apps.trades.models import Klines

import json



def get_products(request):
    if request.method == "GET":
        client = Client()
        products = client.get_products()
        return JsonResponse({'message': products}, status=200)
    else:
        return JsonResponse({'message': 'Metodo no permitido'}, status=405)


def get_exchange_info(request):
    if request.method == "GET":
        client = Client()
        exchange_info = client.get_exchange_info()
        return JsonResponse({'message': exchange_info}, status=200)
    else:
        return JsonResponse({'message': 'Metodo no permitido'}, status=405)


def get_symbol_info(request, symbol):
    if request.method == "GET":
        client = Client()
        symbol_info = client.get_symbol_info(symbol)
        return JsonResponse({'message': symbol_info}, status=200)
    else:
        return JsonResponse({'message': 'Metodo no permitido'}, status=405)


def get_ping(request):
    if request.method == "GET":
        client = Client()
        ping = client.ping()
        return JsonResponse({'message': ping}, status=200)
    else:
        return JsonResponse({'message': 'Metodo no permitido'}, status=405)


def get_server_time(request):
    if request.method == "GET":
        client = Client()
        server_time = client.get_server_time()
        return JsonResponse({'message': server_time}, status=200)
    else:
        return JsonResponse({'message': 'Metodo no permitido'}, status=405)


# Market Data endpoints

def get_all_tickers(request):
    if request.method == "GET":
        client = Client()
        all_tickers = client.get_all_tickers()
        return JsonResponse({'message': all_tickers}, status=200)
    else:
        return JsonResponse({'message': 'Metodo no permitido'}, status=405)


def get_orderbook_tickers(request):
    if request.method == "GET":
        client = Client()
        orderbook_tickers = client.get_orderbook_tickers()
        return JsonResponse({'message': orderbook_tickers}, status=200)
    else:
        return JsonResponse({'message': 'Metodo no permitido'}, status=405)


def get_orderbook(request, symbol):
    if request.method == "GET":
        client = Client()
        orderbook = client.get_order_book(symbol=symbol)
        return JsonResponse({'message': orderbook}, status=200)
    else:
        return JsonResponse({'message': 'Metodo no permitido'}, status=405)


def get_recent_trades(request, symbol):
    if request.method == "GET":
        client = Client()
        recent_trades = client.get_recent_trades(symbol=symbol)
        return JsonResponse({'message': recent_trades}, status=200)
    else:
        return JsonResponse({'message': 'Metodo no permitido'}, status=405)


def get_historical_trades(request, symbol):
    if request.method == "GET":
        client = Client()
        historical_trades = client.get_historical_trades(symbol=symbol)
        return JsonResponse({'message': historical_trades}, status=200)
    else:
        return JsonResponse({'message': 'Metodo no permitido'}, status=405)


def get_aggregate_trades(request, symbol):
    if request.method == "GET":
        client = Client()
        aggregate_trades = client.get_aggregate_trades(symbol=symbol)
        return JsonResponse({'message': aggregate_trades}, status=200)
    else:
        return JsonResponse({'message': 'Metodo no permitido'}, status=405)


def get_klines(request, symbol, interval):
    if request.method == "GET":
        client = Client()
        klines = client.get_klines(symbol=symbol, interval=interval)
        return JsonResponse({'message': klines}, status=200)
    else:
        return JsonResponse({'message': 'Metodo no permitido'}, status=405)


def get_historical_klines(request, symbol, interval, start_str, end_str, limit):
    if request.method == "GET":
        client = Client()
        historical_klines = client.get_historical_klines(
            symbol=symbol,
            interval=interval,
            start_str=start_str,
            end_str=end_str,
            limit=limit
        )
        return JsonResponse({'message': historical_klines}, status=200)
    else:
        return JsonResponse({'message': 'Metodo no permitido'}, status=405)

# User Account


def get_account(request):
    if request.method == "GET":
        client = Client()
        account = client.get_account()
        return JsonResponse({'message': account}, status=200)
    else:
        return JsonResponse({'message': 'Metodo no permitido'}, status=405)


@csrf_exempt    
def futures_create_order(request):
    if request.method == "POST":
        futures = Futures(
            Client(),
            "BTCBUSD",
            0.004,
            "BUSD"
        )

        mb = futures.set_money(40)

        buy = False

        if mb:
            buy = futures.get_open_orders()

        return JsonResponse({'message': buy}, status=200)
    else:
        return JsonResponse({'message': 'Metodo no permitido'}, status=405)


@csrf_exempt    
def spot_create_order(request):
    if request.method == "POST":
        print("ENTRA SPOR CREATE ORDER")
        spot = Spot(
            Client(),
            "BTCBUSD",
            0.004,
            "BUSD"
        )

        client = Client()

        mb = spot.set_money(40)

        buy = False

        if mb:
            price = 22582
            buy = spot.buy_market(price)
            sl = spot.stop_loss_limit_sell(
                price * ( 1 - 0.02),
                price * ( 1 - 0.02 - 0.005 ),
                40/price
            )
            print("------------------------BUY--------------------------------------------")
            print(buy)
            print("------------------------SL--------------------------------------------")
            print(sl)
            print("------------------------SL_INCREASE--------------------------------------------")
            spot.increase_sl()

        coin2 = client.get_order(
             symbol="BTCBUSD",
             orderId=1795490356
        )

        return JsonResponse({'message': buy}, status=200)
    else:
        return JsonResponse({'message': 'Metodo no permitido'}, status=405)



@csrf_exempt    
def futures_account_balance(request):
    if request.method == "POST":
        futures = Futures(
            Client(),
            "BTCBUSD",
            0.004,
            0.001,
            "BTC",
        )

        exchange_info = futures.get_position_information()

        return JsonResponse({'message': exchange_info}, status=200)
    else:
        return JsonResponse({'message': 'Metodo no permitido'}, status=405)
    


@csrf_exempt    
def futures_exchange_info(request):
    if request.method == "POST":
        client = Client()
        
        exchange_info = client.futures_mark_price(
            symbol="BTCBUSD"
        )
        return JsonResponse({'message': exchange_info}, status=200)
    else:
        return JsonResponse({'message': 'Metodo no permitido'}, status=405)
    

@csrf_exempt
def evaluate_no_ai(request):
    print("++++++++++++++++++++++++++++++++++++++++++++")
    print(datetime.datetime.now())
    try:
        btb = Strategy(client=Client())
        body = json.loads(request.body.decode('utf-8'))
        ga = body.pop('ga')
        btb.eval_function(body, ga)
        btb.graph_data()
        btb.invest_spot()
        btb.invest_short()
        return JsonResponse({'message': "Entrenamiento exitoso"}, status=200)
    except Exception:
        traceback.print_exc()
        return JsonResponse({'message': "Entrenamiento fallido"}, status=500)

@csrf_exempt
def train_ga_function(request, klines, client):
    print("++++++++++++++++++++++++++++++++++++++++++++")
    print(datetime.datetime.now())
    try:
        btb = Strategy(client)
        body = json.loads(request.body.decode('utf-8'))
        ga_info = body.pop('ga_info')
        btb.train_function_ga(body, ga_info, klines)
        return JsonResponse({'message': "Entrenamiento exitoso"}, status=200)
    except Exception:
        traceback.print_exc()
        return JsonResponse({'message': "Entrenamiento fallido"}, status=500)

@csrf_exempt
def train_ga(request):
    if request.method == "POST":
        try:
            Klines.objects.all().delete()
            client = Client()
            body = json.loads(request.body.decode('utf-8'))
            klines = Strategy(client=client).run_klines_to_save(body)
            print(request.body)
            t = Thread(target=train_ga_function, args=(request, klines, client))
            t.start()
            return JsonResponse({'message': "Entrenamiento exitoso"}, status=200)
        except Exception:
            traceback.print_exc()
            return JsonResponse({'message': "Entrenamiento fallido"}, status=500)
    else:
        return JsonResponse({'message': 'Método no permitido'}, status=405)
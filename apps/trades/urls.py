from django.urls import path
from apps.trades import views

urlpatterns = [
    
    # Exchange Endpoints
    path('exchange/get_products/', views.get_products, name='exchange-get-products'),
    path('exchange/get_exchange_info/', views.get_exchange_info, name='exchange-get-exchange-info'),
    path('exchange/get_symbol_info/<str:symbol>', views.get_symbol_info, name='exchange-get-symbol-info'),
    
    # General Endpoints
    path('exchange/get_ping/', views.get_ping, name='exchange-get-ping'),
    path('exchange/get_server_time/', views.get_server_time, name='exchange-get-servertime'),
    
    # Market Data Endpoints
    path('exchange/get_all_tickers', views.get_all_tickers, name='exchange-get-all-tickers'),
    path('exchange/get_orderbook_tickers', views.get_orderbook_tickers, name='exchange-get-orderbook-tickers'),
    path('exchange/get_orderbook/<str:symbol>', views.get_orderbook, name='exchange-get-orderbook'),
    path('exchange/get_recent_trades/<str:symbol>', views.get_recent_trades, name='exchange-get-recent-trades'),
    path('exchange/get_historical_trades/<str:symbol>', views.get_historical_trades, name='exchange-get-historical-trades'),
    path('exchange/get_aggregate_trades/<str:symbol>', views.get_aggregate_trades, name='exchange-get-aggregate-trades'),
    path('exchange/get_klines/<str:symbol>/<str:interval>', views.get_klines, name='exchange-get-klines'),   
    path('exchange/get_historical_klines/<str:symbol>/<str:interval>/<str:start_str>/<str:end_str>', views.get_historical_klines, name='exchange-get-historical-klines'),   

    #Spot
    path('exchange/spot_create_order', views.spot_create_order, name='spot-create-order'),   

    #Futures
    path('exchange/futures_exchange_info', views.futures_exchange_info, name='futures-exchange-info'),
    path('exchange/futures_create_order', views.futures_create_order, name='futures-create-order'),   
    path('exchange/futures_account_balance', views.futures_account_balance, name='futures-account-balance'),   
    
    # User Account  
    path('exchange/get_account', views.get_account, name='exchange-get-account-info'),
    
    # Bot
    path('bot/evaluate_no_ai', views.evaluate_no_ai, name='evaluate_no_ai'),
    path('bot/train_ga', views.train_ga, name='train_ga'),
    
    
]

import os
from celery import Celery
from django.conf import settings
from celery.schedules import crontab
 
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'botentry.settings')
 
app = Celery('botentry')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

principal_trade_period = "5m"
cron_trade = crontab()
cron_train = crontab()


if principal_trade_period == "1m":
    cron_trade = crontab()
    cron_train = crontab(hour='*/8')
if principal_trade_period == "5m":
    cron_trade = crontab(minute='*/5')
    cron_train = crontab(minute=0, hour='*/8')
if principal_trade_period == "15m":
    cron_trade = crontab(minute='*/15')
    cron_train = crontab(minute=0, hour='*/12')
if principal_trade_period == "1h":
    cron_trade = crontab(minute=59)
    cron_train = crontab(minute=59, hour=0, day_of_week=6)
if principal_trade_period == "4h":
    cron_trade = crontab(minute=0, hour='*/4')
    cron_train = crontab(hour=0, day_of_week=6)


app.conf.beat_schedule = {
    'trade': {
        'task': 'apps.trades.tasks.trade',
        'schedule': cron_trade,
        'args': (principal_trade_period, )
    },
    'train': {
        'task': 'apps.trades.tasks.train',
        'schedule': cron_train,
        'args': (principal_trade_period, )
    }
}


from django.db import models

# Create your models here.


class Individual(models.Model):
    score = models.FloatField()
    variables = models.TextField()
    principal_trade_period = models.CharField(max_length=4)
    pair = models.CharField(max_length=12)
    created_date = models.DateTimeField(auto_now=True, auto_now_add=False)

class Trade(models.Model):
    pair = models.TextField()
    operation = models.TextField()
    money = models.FloatField()
    price = models.FloatField()
    quantity = models.FloatField()   
    error = models.TextField(blank=True, null=True)
    traceback = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField(auto_now=True, auto_now_add=False)

class Klines(models.Model):
    response = models.TextField()
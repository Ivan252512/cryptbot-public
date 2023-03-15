# Generated by Django 4.0.6 on 2022-07-29 05:09

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Individual',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.FloatField()),
                ('variables', models.TextField()),
                ('principal_trade_period', models.CharField(max_length=4)),
                ('pair', models.CharField(max_length=12)),
                ('created_date', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Klines',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('response', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Trade',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pair', models.TextField()),
                ('operation', models.TextField()),
                ('money', models.FloatField()),
                ('price', models.FloatField()),
                ('quantity', models.FloatField()),
                ('error', models.TextField(blank=True, null=True)),
                ('traceback', models.TextField(blank=True, null=True)),
                ('created_date', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]

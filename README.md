# cryptbot
Binance api

Instructions to up the project:

    1. First you need to save those environment variables in .wnv files

    2. Build your project in docker
        docker-compose build

    3. Up your project in docker
        docker-compose up

    4. Sometime the migrations for django runs before the db starts runnning, you can stop docker and run it again to solve this problem.
    
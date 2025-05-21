@echo off
title TeamSync Fullstack

echo Make sure Redis is running in WSL! 

echo Starting Django server...
start cmd /k "cd /d C:\Users\ASWIN\ANT\Brototype\week24\TEAMSYNC\Backend\teamsync && ..\venv\Scripts\activate && daphne teamsync.asgi:application"

echo Starting Celery worker...
start cmd /k "cd /d C:\Users\ASWIN\ANT\Brototype\week24\TEAMSYNC\Backend\teamsync && ..\venv\Scripts\activate && celery -A teamsync worker --loglevel=info --pool=solo"

echo Starting Stripe webhook listener...
start cmd /k "cd /d C:\Users\ASWIN\ANT\Brototype\week24\TEAMSYNC\Backend\teamsync && ..\venv\Scripts\activate && stripe listen --forward-to 127.0.0.1:8000/api/v1/workspace/webhook/stripe/"

echo Starting React frontend...
start cmd /k "cd /d C:\Users\ASWIN\ANT\Brototype\week24\TEAMSYNC\Frontend\teamsync && npm run dev"

echo All services started!
exit

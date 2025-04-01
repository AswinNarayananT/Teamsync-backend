@echo off
title TeamSync Backend

echo Make sure Redis is running in WSL! 

echo Starting Django server...
start cmd /k "cd /d C:\Users\ASWIN\ANT\Brototype\week24\TEAMSYNC\Backend\teamsync && ..\venv\Scripts\activate && python manage.py runserver"

echo Starting Celery worker...
start cmd /k "cd /d C:\Users\ASWIN\ANT\Brototype\week24\TEAMSYNC\Backend\teamsync && ..\venv\Scripts\activate && celery -A teamsync worker --loglevel=info --pool=solo"

echo All services started!
exit



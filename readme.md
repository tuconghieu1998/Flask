install python

pip install flask
pip install pyodbc
pip install dotenv
pip install requests

pip install waitress

Run dev:
python main.py

Run deploy
waitress-serve --port=5000 wsgi:app > waitress.log 2>&1

Check log:
Get-Content waitress.log -Wait

2. Add to Task Scheduler
Open Task Scheduler (Win + R → type taskschd.msc → Enter).

Click Create Basic Task.

Name: FlaskApp

Trigger: Select "When the computer starts".

Action: Choose "Start a Program" → Browse → Select start_flask.bat.

Click Finish.
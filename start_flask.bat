@echo off
cd /d C:\ESP32\Flask
waitress-serve --port=5000 wsgi:app > waitress.log 2>&1
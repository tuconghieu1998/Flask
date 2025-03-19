@echo off
cd /d D:\ESP32\Flask
waitress-serve --port=5000 wsgi:app
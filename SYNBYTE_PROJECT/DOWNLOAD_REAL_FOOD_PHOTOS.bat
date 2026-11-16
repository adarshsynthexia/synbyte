@echo off
cd /d "%~dp0"
py -m pip install -r requirements.txt
py DOWNLOAD_REAL_FOOD_PHOTOS.py
pause

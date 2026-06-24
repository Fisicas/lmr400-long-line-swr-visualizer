@echo off
setlocal
cd /d "%~dp0"
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
pyinstaller --onefile --windowed --name LMR400_Long_Line_SWR_Visualizer lmr400_long_line_swr_visualizer.py
pause

@echo off
cd /d "%~dp0"
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo Installing packages...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
echo Running pipeline...
python run_pipeline.py
if errorlevel 1 (
    echo Pipeline failed. See the message above.
    pause
    exit /b 1
)
echo Opening the Power BI project. Click Refresh in Power BI Desktop to load the data.
start "" "powerbi\Phoenix_Suns_Strategy_Hub.pbip"
start "" "outputs\Phoenix_Suns_Fan_Revenue_Strategy_Report.pdf"
pause

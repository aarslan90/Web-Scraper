@echo off
echo ========================================
echo LONDON WHOLESALE SCRAPER - QUICK START
echo ========================================
echo.
echo This will install required packages and run the scraper
echo.
pause

echo.
echo [1/2] Installing required packages...
pip install -r requirements.txt

echo.
echo [2/2] Starting scraper...
echo.
python london_wholesale_selenium_scraper.py

echo.
echo ========================================
echo Scraping complete!
echo Check for London_Wholesale_Complete.xlsx
echo ========================================
pause

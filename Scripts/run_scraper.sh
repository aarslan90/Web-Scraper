#!/bin/bash

echo "========================================"
echo "LONDON WHOLESALE SCRAPER - QUICK START"
echo "========================================"
echo ""
echo "This will install required packages and run the scraper"
echo ""
read -p "Press ENTER to continue..."

echo ""
echo "[1/2] Installing required packages..."
pip3 install -r requirements.txt

echo ""
echo "[2/2] Starting scraper..."
echo ""
python3 london_wholesale_selenium_scraper.py

echo ""
echo "========================================"
echo "Scraping complete!"
echo "Check for London_Wholesale_Complete.xlsx"
echo "========================================"
read -p "Press ENTER to close..."

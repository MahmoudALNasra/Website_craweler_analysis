readme_content = """# 🚀 Master Website Analysis & Extraction Toolkit

A blazing-fast, multi-threaded Python suite designed to run entirely within [Google Colab](https://colab.research.google.com/). It connects directly to your Google Sheets to perform high-speed email extraction and deep technical analysis on thousands of business websites concurrently. 

Built as a massive upgrade from Google Apps Script, this toolkit bypasses execution timeouts and processes up to 10 websites simultaneously.

## ✨ Core Features
* **Multi-Threading:** Uses Python's `concurrent.futures` to analyze up to 10 websites at the exact same time.
* **Smart Row Skipping:** Reads the sheet into memory first, instantly skipping already-processed rows without making redundant API calls.
* **Direct Sheets Integration:** Authenticates and writes directly to your live Google Spreadsheet in massive batch updates (`gspread`).
* **Two Powerful Modules:**
  1. **Email Extractor:** Hunts down email addresses using robust Regex and BeautifulSoup.
  2. **Technical Analyzer:** Scans site headers and HTML to detect Google Analytics (GA4/UA), Google Tag Manager, Facebook Pixel, Google Ads, Meta Tags, Live Chats, and tech stacks (WordPress, Shopify, Wix, etc.).

## 📋 Prerequisites
1. A Google Account.
2. A Google Sheet formatted with your target business URLs.
3. [Google Colab](https://colab.research.google.com/) (Free tier).

## 🚀 Setup & Usage

### 1. Sheet Configuration
Ensure your Google Sheet is formatted correctly. The scripts expect the following column indices (1-based):
* **Column D (Index 4):** Website URLs
* **Column L (Index 12):** Extracted Emails (Target for Module 1)
* **Column N (Index 14):** Detailed Analysis (Target for Module 2)

*Make sure your tab names match the `SHEET_NAMES` array in the scripts (e.g., 'RESTAURANT', 'GYM', 'HOTEL').*

### 2. Colab Authentication (Cell 1)
Create a new notebook in Google Colab. In the **first cell**, paste the following to connect to your Google Drive and Sheets:

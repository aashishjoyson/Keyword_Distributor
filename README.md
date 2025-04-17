# keyword_distributor
 
# 📦 Keyword Distributor

This Streamlit app merges and distributes Amazon and eBay keyword CSVs into daily account-based folders. It dynamically splits rows based on a selected start date and visualizes data insights.

## 🚀 Features

- Upload and merge Amazon/eBay keyword files
- Visual dashboards with row insights
- Distribute rows into 20 accounts per day (50 rows each)
- Auto-detects how many full days are possible
- Exports results in a zip file by month
- Shows undistributed leftover keywords

## 📊 Dashboards

- Row distribution summaries
- Visual breakdown (bar/pie charts)
- Leftover keyword tracker

## 📁 Output Structure

```plaintext
📦 Keyword_Distributor.zip
├── 2025-04-17/
│   ├── Account_01/
│   │   ├── amazon_us_04-17.csv
│   │   └── ebay_04-17.csv
│   └── ...
├── 2025-04-18/
└── ...

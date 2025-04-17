import pandas as pd
import os
from pathlib import Path
import zipfile
from datetime import timedelta
from calendar import monthrange
import streamlit as st
import matplotlib.pyplot as plt

def distribute_keywords(start_date):
    amazon_path = os.path.join("merged", "amazon_merged.csv")
    ebay_path = os.path.join("merged", "ebay_merged.csv")

    if not os.path.exists(amazon_path) or not os.path.exists(ebay_path):
        return False

    amazon_df = pd.read_csv(amazon_path)
    ebay_df = pd.read_csv(ebay_path)

    amazon_total = len(amazon_df)
    ebay_total = len(ebay_df)

    max_days_amazon = amazon_total // 1000
    max_days_ebay = ebay_total // 1000
    max_days_data = min(max_days_amazon, max_days_ebay)

    total_days_in_month = monthrange(start_date.year, start_date.month)[1]
    days_remaining_in_month = total_days_in_month - start_date.day + 1
    distributable_days = min(max_days_data, days_remaining_in_month)

    amazon_pointer = 0
    ebay_pointer = 0

    base_folder = Path("distributed") / f"{start_date.strftime('%Y-%m')}_distribution"
    base_folder.mkdir(parents=True, exist_ok=True)

    for day_offset in range(distributable_days):
        current_date = start_date + timedelta(days=day_offset)
        day_str = current_date.strftime("%Y-%m-%d")
        day_folder = base_folder / day_str
        day_folder.mkdir(parents=True, exist_ok=True)

        for account in range(1, 21):
            account_folder = day_folder / f"account_{account}"
            account_folder.mkdir(parents=True, exist_ok=True)

            amazon_sample = amazon_df.iloc[amazon_pointer:amazon_pointer + 50]
            ebay_sample = ebay_df.iloc[ebay_pointer:ebay_pointer + 50]

            amazon_pointer += 50
            ebay_pointer += 50

            amazon_file = account_folder / f"amazon_us_{current_date.strftime('%m-%d')}.csv"
            ebay_file = account_folder / f"ebay_{current_date.strftime('%m-%d')}.csv"

            amazon_sample.to_csv(amazon_file, index=False)
            ebay_sample.to_csv(ebay_file, index=False)

    # Zip the whole month's folder
    zip_filename = f"distributed/{start_date.strftime('%Y-%m')}_distribution.zip"
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for root, _, files in os.walk(base_folder):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, start=base_folder.parent))

    # Remove the unzipped folder after zipping
    import shutil
    shutil.rmtree(base_folder)

    remaining_amazon_df = amazon_df.iloc[amazon_pointer:]
    remaining_ebay_df = ebay_df.iloc[ebay_pointer:]

    os.makedirs("leftover", exist_ok=True)
    if not remaining_amazon_df.empty:
        remaining_amazon_df.to_csv("leftover/undistributed_amazon.csv", index=False)
    if not remaining_ebay_df.empty:
        remaining_ebay_df.to_csv("leftover/undistributed_ebay.csv", index=False)

    # --- Visualization Summary ---
    st.subheader("📊 Distribution Summary")
    st.write(f"Total Amazon Keywords: {amazon_total}")
    st.write(f"Total eBay Keywords: {ebay_total}")
    st.write(f"Days Distributed: {distributable_days}")
    st.write(f"Undistributed Amazon Keywords: {amazon_total - amazon_pointer}")
    st.write(f"Undistributed eBay Keywords: {ebay_total - ebay_pointer}")

    labels = ['Distributed', 'Undistributed']
    amazon_sizes = [amazon_pointer, amazon_total - amazon_pointer]
    ebay_sizes = [ebay_pointer, ebay_total - ebay_pointer]

    fig, axs = plt.subplots(1, 2, figsize=(10, 4))
    axs[0].pie(amazon_sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#4CAF50', '#FFC107'])
    axs[0].set_title('Amazon Keywords')
    axs[1].pie(ebay_sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#2196F3', '#FF5722'])
    axs[1].set_title('eBay Keywords')

    st.pyplot(fig)

    return {
        "days_distributed": distributable_days,
        "remaining_amazon": amazon_total - amazon_pointer,
        "remaining_ebay": ebay_total - ebay_pointer,
        "amazon_download": "leftover/undistributed_amazon.csv" if not remaining_amazon_df.empty else None,
        "ebay_download": "leftover/undistributed_ebay.csv" if not remaining_ebay_df.empty else None
    }

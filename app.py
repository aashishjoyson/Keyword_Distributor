import streamlit as st
from utils.merge import merge_amazon_files, merge_ebay_files
from utils.distribute import distribute_keywords
import os

# Set up Streamlit app
st.title("📦 Keyword Distributor")

st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Choose a page:", ["Merge Files", "Distribute Keywords"])

# Create folders if they don't exist
for folder in ["uploads", "merged", "distributed", "leftover"]:
    os.makedirs(folder, exist_ok=True)

if page == "Merge Files":
    st.header("🛠️ Merge Amazon and eBay Files")

    st.subheader("Upload Amazon Files")
    amazon_files = st.file_uploader("Upload Amazon CSV files", accept_multiple_files=True, key="amazon")

    st.subheader("Upload eBay Files")
    ebay_files = st.file_uploader("Upload eBay CSV files", accept_multiple_files=True, key="ebay")

    if st.button("Merge Files"):
        if amazon_files:
            amazon_rows = merge_amazon_files(amazon_files)
            st.success(f"✅ Amazon files merged with {amazon_rows} total rows.")
        else:
            st.warning("⚠️ Please upload Amazon files.")

        if ebay_files:
            ebay_rows = merge_ebay_files(ebay_files)
            st.success(f"✅ eBay files merged with {ebay_rows} total rows.")
        else:
            st.warning("⚠️ Please upload eBay files.")

if page == "Distribute Keywords":
    st.header("📦 Distribute Merged Keywords")
    start_date = st.date_input("Select Start Date")

    if st.button("Distribute"):
        # Verify the merged files exist
        amazon_file = os.path.join("merged", "amazon_merged.csv")
        ebay_file = os.path.join("merged", "ebay_merged.csv")

        if os.path.exists(amazon_file) and os.path.exists(ebay_file):
            # Call the updated distribution function
            result = distribute_keywords(start_date)
            if result:
                st.success(f"✅ Distributed keywords into {result['days_distributed']} day(s) of ZIP files.")
                
                # The distribution function already displays visual insights.
                # Now offer download options for leftover keywords.
                st.subheader("Download Leftover Files")
                if result["amazon_download"]:
                    with open(result["amazon_download"], "rb") as file:
                        st.download_button("⬇️ Download Undistributed Amazon Keywords", file, file_name="undistributed_amazon.csv")
                if result["ebay_download"]:
                    with open(result["ebay_download"], "rb") as file:
                        st.download_button("⬇️ Download Undistributed eBay Keywords", file, file_name="undistributed_ebay.csv")
            else:
                st.warning("⚠️ Distribution failed.")
        else:
            st.warning("⚠️ Please upload and merge the files first.")

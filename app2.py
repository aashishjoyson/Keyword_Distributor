import streamlit as st
import pandas as pd
import plotly.express as px
import os
from utils.merge import save_uploaded_file, merge_uploaded_files
from utils.distribute import distribute_keywords
from PIL import Image

st.set_page_config(page_title="Keyword Distributor", layout="wide")

# --- Header ---
logo = Image.open(os.path.join("utils", "logo.png"))
col1, col2 = st.columns([1, 5])
with col1:
    st.image(logo, width=120)
with col2:
    st.markdown("# 📦 Keyword Distributor", unsafe_allow_html=True)

st.markdown(
    """
    Welcome to **Keyword Distributor**! 🚀

    **Features:**
    - 🔄 Upload multiple keyword CSV files (Amazon & eBay - US, DE, UK, CA, AU)
    - 📊 Visualize keyword counts
    - 🗂️ Distribute into 23 accounts daily folders
    - 📦 Download monthly ZIP
    - 💾 Download leftover keywords
    """
)

st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Go to", ["Merge Files", "Distribute Keywords"])

for folder in ["uploads", "merged", "distributed", "leftover"]:
    os.makedirs(folder, exist_ok=True)

if page == "Merge Files":
    st.header("🛠️ Merge Multiple Platform Files")
    st.write("Upload CSVs named as `amazon_us`, `ebay`, `amazon_de`, `amazon_uk`, `amazon_ca`, `amazon_au`.")

    uploaded_files = st.file_uploader("Upload Multiple Files", accept_multiple_files=True)

    if st.button("Merge Files"):
        if not uploaded_files:
            st.warning("Please upload at least one file.")
        else:
            merged_counts = merge_uploaded_files(uploaded_files)
            st.success("✅ Files merged successfully!")
            for platform, count in merged_counts.items():
                st.write(f"{platform}: {count} rows")

            # Visualization
            platforms = list(merged_counts.keys())
            counts = [merged_counts[platform] for platform in platforms]
            fig = px.bar(x=platforms, y=counts, labels={'x': 'Platform', 'y': 'Row Count'}, title="Merged Keyword Counts")
            st.plotly_chart(fig, use_container_width=True)

            # Download buttons
            for platform in platforms:
                merged_path = f"merged/{platform}.csv"
                with open(merged_path, "rb") as f:
                    st.download_button(f"📥 Download {platform} CSV", f, file_name=f"{platform}.csv")

if page == "Distribute Keywords":
    st.header("📦 Distribute Keywords")
    st.write("Select a start date to generate your distribution.")
    start_date = st.date_input("Start Date")

    if st.button("Distribute"):
        result = distribute_keywords(start_date)
        if result:
            st.success(f"✅ Distributed for {result['days_distributed']} days.")

            col1, col2 = st.columns(2)
            with col1:
                st.write("### Distribution Counts")
                for key in result.keys():
                    if key.endswith("_distributed"):
                        st.write(f"{key.replace('_distributed','').upper()}: {result[key]} rows distributed")
            with col2:
                st.write("### Leftovers")
                for key in result.keys():
                    if key.startswith("remaining_"):
                        st.write(f"{key.replace('remaining_','').upper()}: {result[key]} rows remaining")

            # Daily Distribution Trend
            df_daily = pd.DataFrame(result['daily_distribution'])
            st.subheader("📈 Daily Distribution Trend")
            st.dataframe(df_daily)

            # Line Chart
            line = px.line(df_daily, x='date', y=[col for col in df_daily.columns if col != 'date'],
                           title="Daily Distribution Per Platform")
            st.plotly_chart(line, use_container_width=True)

            # Download ZIP
            with open(result['zip_path'], "rb") as f:
                st.download_button("📥 Download Distribution ZIP", f, file_name=os.path.basename(result['zip_path']))

            # Download leftover files
            st.subheader("💾 Leftover Files")
            for platform in ["amazon_us", "ebay", "amazon_de", "amazon_uk", "amazon_ca", "amazon_au"]:
                leftover_path = result.get(f"{platform}_download")
                if leftover_path:
                    with open(leftover_path, "rb") as f:
                        st.download_button(f"Download leftover {platform}.csv", f, file_name=os.path.basename(leftover_path))
        else:
            st.warning("❌ Distribution failed. Please ensure merged files exist.")

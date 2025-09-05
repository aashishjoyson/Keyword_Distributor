import streamlit as st
import pandas as pd
import plotly.express as px
import os
from utils.merge import merge_uploaded_files
from utils.distribute import distribute_keywords
from utils.generator import detect_columns, generate_keywords_for_df, DOMAIN_OPTIONS
from PIL import Image
from pathlib import Path
from io import BytesIO
import time 


st.set_page_config(page_title="KEY GEN AI", layout="wide")

# --- Header ---
logo_path = os.path.join("utils", "logo.png")
if os.path.exists(logo_path):
    logo = Image.open(logo_path)
else:
    logo = None

col1, col2 = st.columns([1, 5])
with col1:
    if logo:
        st.image(logo, width=120)
with col2:
    st.markdown("# 📦 Keyword Distributor")

st.caption("Upload marketplace keyword CSVs, merge by platform, and distribute across N accounts with 100 rows per account.")

# Sidebar nav
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Go to", ["Merge Files", "Distribute Keywords", "Keyword Generator"])
# Ensure folders
for folder in ["uploads", "merged", "distributed", "leftover"]:
    os.makedirs(folder, exist_ok=True)

# Utility: discover merged platforms dynamically
def get_available_platforms():
    merged_dir = Path("merged")
    if not merged_dir.exists():
        return []
    platforms = []
    for p in merged_dir.glob("*.csv"):
        platforms.append(p.stem)  # filename without extension
    return sorted(platforms)

# --- Merge Files Page ---
if page == "Merge Files":
    st.header("🛠️ Merge Files")
    st.write("Upload any subset of these (case-insensitive in filename): `amazon_us`, `amazon_uk`, `amazon_de`, `amazon_ca`, `amazon_au`, `ebay`.")
    st.write("You can upload multiple files per platform — we’ll merge them together.")

    uploaded_files = st.file_uploader("Upload CSV files", accept_multiple_files=True, type=["csv"])

    if st.button("Merge Files", type="primary"):
        if not uploaded_files:
            st.warning("Please upload at least one CSV.")
        else:
            merged_counts = merge_uploaded_files(uploaded_files)
            if not merged_counts:
                st.error("No recognizable platform files found. Please check filenames.")
            else:
                st.success("✅ Merged successfully!")

                # Minimal stats
                platforms = list(merged_counts.keys())
                counts = [merged_counts[p] for p in platforms]

                # Dashboard (2 cards): table + pie
                c1, c2 = st.columns(2)

                with c1:
                    st.subheader("Merged Counts")
                    df_counts = pd.DataFrame({"platform": platforms, "rows": counts})
                    st.dataframe(df_counts, use_container_width=True, hide_index=True)

                with c2:
                    st.subheader("Share of Merged Rows")
                    pie = px.pie(df_counts, names="platform", values="rows", hole=0.35, title=None)
                    st.plotly_chart(pie, use_container_width=True)

                # Downloads for each merged file
                st.subheader("Downloads")
                for platform in platforms:
                    merged_path = f"merged/{platform}.csv"
                    if os.path.exists(merged_path):
                        with open(merged_path, "rb") as f:
                            st.download_button(f"📥 Download {platform}.csv", f, file_name=f"{platform}.csv")

# --- Distribute Page ---
if page == "Distribute Keywords":
    st.header("📦 Distribute Keywords")

    available_platforms = get_available_platforms()
    if not available_platforms:
        st.info("No merged files detected. Please go to **Merge Files** first.")
    else:
        st.write(f"Detected platforms: `{', '.join(available_platforms)}`")

    # Inputs
    st.write("Select a start date and how many accounts to distribute into.")
    colA, colB = st.columns(2)
    with colA:
        start_date = st.date_input("Start Date")
    with colB:
        # Dual control: slider + number input
        slider_val = st.slider("Accounts (slider)", min_value=1, max_value=50, value=23)
        number_val = st.number_input("Accounts (type exact)", min_value=1, max_value=50, value=slider_val, step=1)
        accounts = int(number_val)  # use typed value as the source of truth

    if st.button("Distribute", type="primary"):
        result = distribute_keywords(start_date, accounts=accounts, rows_per_account=100)
        if not result:
            st.warning("Distribution failed — ensure at least one merged CSV exists in the `merged/` folder.")
        else:
            st.success(f"✅ Distributed for **{result['days_distributed']}** day(s) across **{accounts}** account(s).")

            # Stats row (metrics)
            st.markdown("### Key Stats")
            metrics_cols = st.columns(4)
            total_platforms = len(result["platforms"])
            total_distributed = sum(result.get(f"{p}_distributed", 0) for p in result["platforms"])
            total_leftover = sum(result.get(f"remaining_{p}", 0) for p in result["platforms"])
            metrics_cols[0].metric("Platforms", total_platforms)
            metrics_cols[1].metric("Days", result["days_distributed"])
            metrics_cols[2].metric("Total Distributed", total_distributed)
            metrics_cols[3].metric("Total Leftover", total_leftover)

            # Prepare data for charts
            platforms = result["platforms"]
            dist_counts = [result.get(f"{p}_distributed", 0) for p in platforms]
            rem_counts = [result.get(f"remaining_{p}", 0) for p in platforms]

            df_summary = pd.DataFrame({
                "platform": platforms,
                "distributed": dist_counts,
                "leftover": rem_counts
            })
            df_long = df_summary.melt(id_vars="platform", value_vars=["distributed", "leftover"], var_name="type", value_name="rows")

            # Daily distribution (per platform)
            df_daily = pd.DataFrame(result["daily_distribution"])  # columns: date, platform columns with daily counts
            # Ensure date is string for chart x-axis
            if "date" in df_daily.columns:
                df_daily["date"] = df_daily["date"].astype(str)

            # Sunburst data: build (Date -> Platform -> Account) hierarchy using daily per-platform counts
            # We simulate per-account rows from the day counts, splitting evenly (last account may be partial).
            sun_rows = []
            rows_per_account = result["rows_per_account"]
            acc_n = result["accounts"]
            for _, row in df_daily.iterrows():
                date_str = row["date"]
                for p in platforms:
                    day_count = int(row.get(p, 0))
                    if day_count <= 0:
                        continue
                    full_accounts = day_count // rows_per_account
                    remainder = day_count % rows_per_account
                    # Add full accounts
                    for a in range(1, min(acc_n, full_accounts) + 1):
                        sun_rows.append({"Date": date_str, "Platform": p, "Account": f"Account_{a:02d}", "Rows": rows_per_account})
                    # Add remainder (if any) to next account
                    next_acc = full_accounts + 1
                    if remainder > 0 and next_acc <= acc_n:
                        sun_rows.append({"Date": date_str, "Platform": p, "Account": f"Account_{next_acc:02d}", "Rows": remainder})

            df_sun = pd.DataFrame(sun_rows) if sun_rows else pd.DataFrame(columns=["Date", "Platform", "Account", "Rows"])

            # 2x2 dashboard
            t1, t2 = st.columns(2)
            with t1:
                st.subheader("Distribution vs Leftover (Pie)")
                pie2 = px.pie(df_long, names="platform", values="rows", color="type", hole=0.35)
                st.plotly_chart(pie2, use_container_width=True)

            with t2:
                st.subheader("Sunburst: Date → Platform → Account")
                if not df_sun.empty:
                    sunb = px.sunburst(df_sun, path=["Date", "Platform", "Account"], values="Rows")
                    st.plotly_chart(sunb, use_container_width=True)
                else:
                    st.info("No sunburst data to show (no distributed rows).")

            b1, b2 = st.columns(2)
            with b1:
                st.subheader("Daily Trend by Platform")
                if not df_daily.empty:
                    # Line chart: one series per platform
                    y_cols = [c for c in df_daily.columns if c != "date"]
                    if y_cols:
                        line = px.line(df_daily, x="date", y=y_cols, labels={"value": "Rows", "variable": "Platform"})
                        st.plotly_chart(line, use_container_width=True)
                    else:
                        st.info("No platform columns found in daily distribution.")
                else:
                    st.info("No daily distribution data.")

            with b2:
                st.subheader("Platform Summary")
                st.dataframe(df_summary, use_container_width=True, hide_index=True)

            # ZIP download
            if result.get("zip_path") and os.path.exists(result["zip_path"]):
                with open(result["zip_path"], "rb") as f:
                    st.download_button("📦 Download Distribution ZIP", f, file_name=os.path.basename(result["zip_path"]))

            # Leftover downloads (only those that exist)
            st.subheader("💾 Leftover Files")
            for p in platforms:
                leftover_path = result.get(f"{p}_download")
                if leftover_path and os.path.exists(leftover_path):
                    with open(leftover_path, "rb") as f:
                        st.download_button(f"Download leftover {p}.csv", f, file_name=os.path.basename(leftover_path))
        


# =========================
# Keyword Generator Page
# =========================
if page == "Keyword Generator":
    st.header("🤖 Keyword Generator (Groq Llama 4 Maverick)")
    st.write("Upload a CSV/XLSX that contains **Product Title(s)** and optionally **Link(s)**. The app will generate keywords, drop the product title column, and let you download a Distributor-ready file.")

    uploaded_file = st.file_uploader(
        "Upload Excel (.xlsx) or CSV (.csv)",
        type=["xlsx", "csv"],
        key="kg_upload"
    )

    # If a new file is uploaded, clear previous generation results
    if uploaded_file is not None:
        if st.session_state.get("kg_uploaded_name") != uploaded_file.name:
            st.session_state["kg_uploaded_name"] = uploaded_file.name
            for k in ("kg_final_df", "kg_stats", "kg_time_taken", "kg_perf"):
                if k in st.session_state:
                    del st.session_state[k]

    # Read file if uploaded
    df = None
    if uploaded_file:
        name = uploaded_file.name.lower()
        try:
            if name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
        except Exception as e:
            st.error(f"Failed to read file: {e}")
            df = None

    # Show file info + preview
    if df is not None:
        st.subheader("📊 File Information")
        col1, col2, col3 = st.columns([1, 1, 3])
        col1.metric("Rows", len(df))
        col2.metric("Columns", len(df.columns))
        col3.markdown("**Columns:** " + ", ".join([f"`{c}`" for c in df.columns]))

        st.subheader("🔍 Preview (first 5 rows)")
        st.dataframe(df.head(), use_container_width=True)

        # Detect columns
        cols = list(df.columns)
        title_col, link_col, keywords_col = detect_columns(cols)

        if not title_col:
            st.error("❌ Could not find a Product Title/Product Titles column (case-insensitive). Please include one.")
        else:
            api_key = st.secrets.get("GROQ_API_KEY")
            if not api_key:
                st.warning("⚠️ GROQ_API_KEY is missing. Add it in Streamlit Secrets to enable generation.")

            # Trigger generation
            if st.button("🚀 Generate Keywords", key="kg_generate"):
                if not api_key:
                    st.stop()

                start_time = time.time()
                progress = st.progress(0, text="Generating keywords...")

                def _cb(done, total):
                    # progress expects fraction in [0,1]
                    try:
                        progress.progress(min(max(done / total, 0.0), 1.0))
                    except Exception:
                        # fallback in case total==0
                        progress.progress(1.0)

                final_df, stats = generate_keywords_for_df(
                    df=df.copy(),
                    api_key=api_key,
                    title_col=title_col,
                    link_col=link_col,
                    keywords_col=keywords_col,
                    progress_cb=_cb,
                    delay_seconds=1.5,
                    retries=3
                )

                time_taken = time.time() - start_time
                api_calls = stats.get("generated", 0) + stats.get("failed", 0)
                rows_total = len(df)
                rows_per_sec_total = rows_total / time_taken if time_taken > 0 else 0.0
                api_rows_per_sec = api_calls / time_taken if time_taken > 0 else 0.0
                avg_ms_per_api_call = (time_taken / api_calls * 1000.0) if api_calls > 0 else None
                success_rate = (stats.get("generated", 0) / api_calls * 100.0) if api_calls > 0 else 0.0

                # Persist results in session_state so dropdowns / reruns won't clear them
                st.session_state["kg_final_df"] = final_df
                st.session_state["kg_stats"] = stats
                st.session_state["kg_time_taken"] = time_taken
                st.session_state["kg_perf"] = {
                    "rows_total": rows_total,
                    "api_calls": api_calls,
                    "rows_per_sec_total": rows_per_sec_total,
                    "api_rows_per_sec": api_rows_per_sec,
                    "avg_ms_per_api_call": avg_ms_per_api_call,
                    "success_rate": success_rate
                }

    # If we have generated results (persisted), render the performance dashboard + preview + download
    if "kg_final_df" in st.session_state:
        final_df = st.session_state["kg_final_df"]
        stats = st.session_state["kg_stats"]
        time_taken = st.session_state["kg_time_taken"]
        perf = st.session_state["kg_perf"]

        st.success(f"✅ Keywords ready — generated {stats['generated']} items (failed: {stats['failed']}, skipped: {stats['skipped']}).")

        # Performance metrics (clean, dashboard-like)
        st.subheader("📈 Performance Summary")
        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Total rows", perf["rows_total"])
        a2.metric("API calls (gen+fail)", perf["api_calls"])
        a3.metric("Total time (s)", f"{perf['rows_per_sec_total'] and time_taken:.2f}" if time_taken else f"{time_taken:.2f}")
        a4.metric("Rows/sec (total)", f"{perf['rows_per_sec_total']:.2f}")

        b1, b2 = st.columns(2)
        b1.metric("Rows/sec (API)", f"{perf['api_rows_per_sec']:.2f}")
        b2.metric("Avg ms / API call", f"{perf['avg_ms_per_api_call']:.0f} ms" if perf["avg_ms_per_api_call"] else "N/A")

        c1, c2 = st.columns([2, 3])
        with c1:
            st.metric("Success rate (API)", f"{perf['success_rate']:.1f}%")
            st.metric("Generated", stats["generated"])
            st.metric("Failed", stats["failed"])
            st.metric("Skipped", stats["skipped"])
        with c2:
            # Pie chart: Generated / Failed / Skipped
            pie_df = pd.DataFrame({
                "status": ["Generated", "Failed", "Skipped"],
                "count": [stats["generated"], stats["failed"], stats["skipped"]]
            })
            pie = px.pie(pie_df, names="status", values="count", hole=0.4, title="Generation outcomes")
            st.plotly_chart(pie, use_container_width=True)

        # Output preview + domain selection + download
        st.subheader("📄 Final Output (Distributor-ready)")
        st.dataframe(final_df.head(20), use_container_width=True)

        domain_label = st.selectbox("🌍 Save file for marketplace:", list(DOMAIN_OPTIONS.keys()), key="kg_domain")
        filename = DOMAIN_OPTIONS[domain_label]

        csv_bytes = final_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=f"📥 Download for {domain_label}",
            data=csv_bytes,
            file_name=filename,
            mime="text/csv",
            key="kg_download"
        )

        # Allow clearing results
        if st.button("🧹 Clear generated results", key="kg_clear"):
            for k in ("kg_final_df", "kg_stats", "kg_time_taken", "kg_perf", "kg_uploaded_name"):
                if k in st.session_state:
                    del st.session_state[k]
            st.experimental_rerun()

    st.info("Tip: If your input includes a Links column, the output will be **Keywords | Links**. If not, the output will be **Keywords** only. The **Product Title** column is always dropped in the final file.")

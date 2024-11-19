import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz



# Set page config
st.set_page_config(
    page_title="Weekly Options Trade Analysis",
    page_icon="📈",
    layout="wide"
)

# Add title
st.title("Weekly Options Trade Analysis")

# Read the CSV file
et_timezone = pytz.timezone('US/Eastern')
et_now = datetime.now(et_timezone)
today = et_now.strftime("%Y-%m-%d")
coming_friday = (et_now + timedelta(days=(4 - et_now.weekday()))).strftime("%Y-%m-%d")

# Add a note about timezone
st.caption("All dates are in Eastern Time (ET)")

today_data_link=f"https://ugwxqrmxqtcvicxhcnla.supabase.co/storage/v1/object/public/option-analytics/weekly_options_trade{today}_exp{coming_friday}_sorted_by_return.csv"

# today_data_link="https://ugwxqrmxqtcvicxhcnla.supabase.co/storage/v1/object/public/option-analytics/weekly_options_trade2024-11-13_exp2024-11-15_sorted_by_return.csv"
# @st.cache_data  # This caches the data to improve performance
def load_data():
    df = pd.read_csv(today_data_link)
    return df

# After timezone setup and before loading data
et_now = datetime.now(et_timezone)
current_time = et_now.time()
market_close_time = datetime.strptime("16:00", "%H:%M").time()

if current_time < market_close_time:
    st.warning("⚠️ Daily options data will be available after 4:00 PM ET. Data shown may be from the previous trading day.")

try:
    # Load the data
    df = load_data()
    
    # Add filters in the sidebar
    st.sidebar.header("Filters")
    
    # Symbol filter
    symbols = []  # Initialize symbols as empty list
    if 'Symbol' in df.columns:
        symbols = st.sidebar.multiselect(
            "Select Symbols",
            options=df['Symbol'].unique()
        )
    
    # Volume filter
    min_volume = int(df['volume'].min())
    max_volume = int(df['volume'].max())
    volume_input_method = st.sidebar.radio(
        "Volume Filter Input Method",
        ["Slider", "Text Input"]
    )
    
    if volume_input_method == "Slider":
        volume_threshold = st.sidebar.slider(
            "Minimum Volume",
            min_value=min_volume,
            max_value=max_volume,
            value=min_volume
        )
    else:
        volume_threshold = st.sidebar.number_input(
            "Enter Minimum Volume",
            min_value=min_volume,
            max_value=max_volume,
            value=min_volume,
            step=1
        )
    
    # Put/Call filter
    right_options = []  # Initialize right_options as empty list
    if 'right' in df.columns:
        right_options = st.sidebar.multiselect(
            "Option Type (P/C)",
            options=df['right'].unique(),
            default=df['right'].unique()
        )
    
    # Apply filters
    filtered_df = df.copy()
    if symbols:
        filtered_df = filtered_df[filtered_df['Symbol'].isin(symbols)]
    filtered_df = filtered_df[filtered_df['volume'] >= volume_threshold]
    if right_options:
        filtered_df = filtered_df[filtered_df['right'].isin(right_options)]
    
    # Display data statistics
    st.subheader("Dataset Overview")
    st.write(f"Total Records: {len(filtered_df)}")
    
    # Display the filtered dataframe
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True
    )

    # Update download button to use filtered data
    st.download_button(
        label="Download Data as CSV",
        data=filtered_df.to_csv(index=False).encode('utf-8'),
        file_name="filtered_options_data.csv",
        mime="text/csv"
    )

except Exception as e:
    st.error(f"Error loading the data: {str(e)}") 

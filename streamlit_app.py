import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import requests

def get_available_market_date(current_date, timezone):
    """
    Get the most recent available market date.
    Handles weekends and tries previous days until valid data is found.
    """
    def is_weekend(date):
        return date.weekday() > 4
    
    def get_data_url(date, exp_friday):
        return f"https://ugwxqrmxqtcvicxhcnla.supabase.co/storage/v1/object/public/option-analytics/weekly_options_trade{date.strftime('%Y-%m-%d')}_exp{exp_friday}_sorted_by_return.csv"
    
    def is_data_available(url):
        try:
            response = requests.head(url)
            return response.status_code == 200
        except:
            return False
    
    current_date = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
    test_date = current_date
    max_attempts = 10  # Prevent infinite loop
    attempts = 0
    
    while attempts < max_attempts:
        # Skip weekends
        while is_weekend(test_date):
            test_date -= timedelta(days=1)
            
        # Calculate coming Friday for the test date
        coming_friday = (test_date + timedelta(days=(4 - test_date.weekday())))
        data_url = get_data_url(test_date, coming_friday.strftime('%Y-%m-%d'))
        
        if is_data_available(data_url):
            return test_date.strftime('%Y-%m-%d'), coming_friday.strftime('%Y-%m-%d'), data_url
            
        test_date -= timedelta(days=1)
        attempts += 1
    
    raise Exception("No available market data found in the last 10 business days")

# Set page config
st.set_page_config(
    page_title="Weekly Options Trade Analysis",
    page_icon="📈",
    layout="wide"
)

# Add title
st.title("Weekly Options Trade Analysis")

# Initialize timezone
et_timezone = pytz.timezone('US/Eastern')
et_now = datetime.now(et_timezone)
current_time = et_now.time()
market_close_time = datetime.strptime("16:00", "%H:%M").time()

# Get appropriate market date and data URL
try:
    market_date, coming_friday, today_data_link = get_available_market_date(et_now, et_timezone)
    
    if et_now.strftime('%Y-%m-%d') != market_date:
        st.warning(f"⚠️ Showing data from {market_date} (most recent available market day)")
    elif current_time < market_close_time:
        st.warning("⚠️ Daily options data will be available after 4:00 PM ET. Data shown may be from the previous trading day.")

    # Add a note about timezone
    st.caption("All dates are in Eastern Time (ET)")

    @st.cache_data  # This caches the data to improve performance
    def load_data():
        df = pd.read_csv(today_data_link)
        return df

    # Load the data
    df = load_data()
    
    # Add filters in the sidebar
    st.sidebar.header("Filters")
    
    # Symbol filter
    symbols = []
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
    right_options = []
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

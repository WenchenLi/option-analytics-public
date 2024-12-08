import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import requests

def get_data_url(date, exp_friday):
    return f"https://ugwxqrmxqtcvicxhcnla.supabase.co/storage/v1/object/public/option-analytics/weekly_options_trade{date.strftime('%Y-%m-%d')}_exp{exp_friday}_sorted_by_return.csv"

def is_data_available(url):
    try:
        response = requests.head(url)
        return response.status_code == 200
    except:
        return False

def is_weekend(date):
    return date.weekday() > 4

# Set page config
st.set_page_config(
    page_title="Weekly Options Trade Analysis",
    page_icon="📈",
    layout="wide"
)

st.title("Weekly Options Trade Analysis")

# Initialize timezone
et_timezone = pytz.timezone('US/Eastern')
et_now = datetime.now(et_timezone)

# Add session state for cache clearing
if "last_selected_date" not in st.session_state:
    st.session_state.last_selected_date = None

if "cache_cleared" not in st.session_state:
    st.session_state.cache_cleared = False

# Date selection
selected_date = st.date_input(
    "Select Date",
    value=et_now.date(),
    max_value=et_now.date()
)

# Clear cache when the date changes
if st.session_state.last_selected_date != selected_date:
    st.cache_data.clear()  # Clear Streamlit cache
    st.session_state.last_selected_date = selected_date
    st.session_state.cache_cleared = True
    # st.info("Cache cleared due to date change.")

# Convert selected date to datetime with ET timezone
selected_datetime = datetime.combine(selected_date, datetime.min.time())
selected_datetime = et_timezone.localize(selected_datetime)

# Calculate coming Friday for the selected date
coming_friday = (selected_datetime + timedelta(days=(4 - selected_datetime.weekday())))
data_url = get_data_url(selected_datetime, coming_friday.strftime('%Y-%m-%d'))

if is_weekend(selected_datetime):
    st.error("Selected date is a weekend. Please select a weekday.")
elif not is_data_available(data_url):
    st.error(f"No data available for {selected_date}. Please select another date.")
else:
    st.caption("All dates are in Eastern Time (ET)")

    @st.cache_data
    def load_data(url):
        df = pd.read_csv(url)
        return df

    try:
        df = load_data(data_url)
        
        # Sidebar filters
        st.sidebar.header("Filters")
        
        symbols = []
        if 'Symbol' in df.columns:
            symbols = st.sidebar.multiselect(
                "Select Symbols",
                options=df['Symbol'].unique()
            )
        
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
        
        st.subheader("Dataset Overview")
        st.write(f"Total Records: {len(filtered_df)}")
        
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True
        )
        
        st.download_button(
            label="Download Data as CSV",
            data=filtered_df.to_csv(index=False).encode('utf-8'),
            file_name=f"options_data_{selected_date}.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"Error loading the data: {str(e)}")

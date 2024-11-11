import streamlit as st
import pandas as pd

# Set page config
st.set_page_config(
    page_title="Weekly Options Trade Analysis",
    page_icon="📈",
    layout="wide"
)

# Add title
st.title("Weekly Options Trade Analysis")

# Read the CSV file
@st.cache_data  # This caches the data to improve performance
def load_data():
    df = pd.read_csv('https://ugwxqrmxqtcvicxhcnla.supabase.co/storage/v1/object/public/option-analytics/weekly_options_trade2024-11-11_exp2024-11-15_20241111_173551_sorted_by_return.csv')
    return df

try:
    # Load the data
    df = load_data()
    
    # Add filters in the sidebar
    st.sidebar.header("Filters")
    
    # You can customize these filters based on your CSV columns
    if 'Symbol' in df.columns:
        symbols = st.sidebar.multiselect(
            "Select Symbols",
            options=df['Symbol'].unique()
        )
    
    # Display data statistics
    st.subheader("Dataset Overview")
    st.write(f"Total Records: {len(df)}")
    
    # Display the dataframe with sorting and filtering capabilities
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
    
    # Add download button
    st.download_button(
        label="Download Data as CSV",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name="",
        mime="text/csv"
    )

except Exception as e:
    st.error(f"Error loading the data: {str(e)}") 
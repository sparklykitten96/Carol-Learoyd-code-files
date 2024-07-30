import streamlit as st
import yfinance as yf
import pandas as pd
import math
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time

st.title ('Stock Comparison Tool')

# Stock symbol input
primary_ticker = st.text_input("Enter Stock Symbol (e.g., AAPL, GOOGL, MSFT, NVDA):", value="NVDA")

# Stock symbol input to compare
ticker_comparison = st.text_input("Enter Stock Symbol to Compare against {ticker}:", value="AAPL")

# Define the current date
curr_date = datetime.now()

# Calculate the prior day
end_date = curr_date - relativedelta(days=1)

# Calculate the start date (5 years of history)
start_date = end_date - relativedelta(years=5)

# Drop time stamp to convert to dates
start_date_date = start_date.date()
end_date_date = end_date.date()

# Create two columns
col1, col2 = st.columns(2)

# Place the KPI card for open price change
with col1:
    # Date picker for selecting start date
    selected_start_date = st.date_input('Select Start Date:',
                                        value=start_date_date,
                                        min_value=start_date_date, # - timedelta(days=365),  # Example: allow selecting up to 1 year back
                                        max_value=end_date_date)
with col2:
    # Date picker for selecting end date
    selected_end_date = st.date_input('Select End Date:',
                                      value=end_date_date,
                                      min_value=start_date_date,
                                      max_value=end_date_date)


# Convert selected dates back to datetime objects for further processing if needed
selected_start_datetime = datetime.combine(selected_start_date, datetime.min.time())
selected_end_datetime = datetime.combine(selected_end_date, datetime.max.time())



# Format the dates to be printed in Streamlit
formatted_selected_strt = selected_start_datetime.strftime("%b %Y")
formatted_selected_end = selected_end_datetime.strftime("%b %Y")



# Calculate the last day of the prior month
end_date_last_month = (datetime(curr_date.year, curr_date.month, 1) - relativedelta(days=1)).replace(hour=23, minute=59, second=59)

# Calculate the first day of the month 2 months ago
start_date_prior_month = (datetime(end_date_last_month.year, end_date_last_month.month, 1) - relativedelta(months=1)).replace(hour=0, minute=0, second=0)

# Function to fetch company name from Yahoo Finance
def get_company_name(symbol):
    try:
        stock = yf.Ticker(symbol)
        company_name = stock.info['longName']
        return company_name
    except:
        return None

# Display company name based on stock symbol input
#if ticker:
 #   company_name = get_company_name(ticker.upper())
  #  if company_name:
   #     st.write(f'Company Name: {company_name}')
    #else:
     #   st.write('Please enter a valid stock symbol.')

# Initialize an empty list
user_list = []

# Add the inputs to the list if they are not empty
if primary_ticker:
    user_list.append(primary_ticker)
if ticker_comparison:
    user_list.append(ticker_comparison)



# initialize empty data frame
all_data = pd.DataFrame()

# cap retry at 5 retries in case of network failure
max_retries = 20

for ticker in user_list:
    success = False
    attempts = 0
    
    while not success and attempts < max_retries:
        try:
            data = yf.download(ticker, start=start_date, end=end_date)
            data['Ticker'] = ticker  # Add a column for the ticker
            all_data = pd.concat([all_data, data])
            success = True
        except Exception as e:
            attempts += 1
            time.sleep(1)  # Wait for 1 second before retrying
    
    if not success:
        st.write(f"Failed to download data for {ticker} after {max_retries} attempts.")
        


# Attempt to download data for the last 5 years
monthly_comparison = all_data[(all_data.index >= start_date_prior_month) & (all_data.index <= end_date_last_month)]
monthly_comparison = monthly_comparison[monthly_comparison['Ticker'] == primary_ticker]

# Resample data on a monthly basis with custom aggregation functions (dictionary)
custom_aggregation = {
    'Open': 'first',
    'High': 'max',
    'Low': 'min',
    'Close': 'last',
    'Adj Close': 'last',
    'Volume': 'sum'
}

# Resample data on a monthly basis, applying custom aggregate functions from above
monthly_comparison_resampled = monthly_comparison.resample('M').agg(custom_aggregation)



# Sort the DataFrame by index (dates) in ascending order (if not already sorted)
monthly_comparison_resampled = monthly_comparison_resampled.sort_index()



# Get the row indices for the most recent and prior months
latest_index = -1  # Index of the latest month (last row after sorting)
prior_index = -2   # Index of the prior month (second last row after sortin

ticker_name = get_company_name(primary_ticker)
comparison_name = get_company_name(ticker_comparison)

# Format the dates to be printed in Streamlit
formatted_strt = start_date_prior_month.strftime("%b %Y")
formatted_end = end_date_last_month.strftime("%b %Y")

st.header(f"Monthly \u0394 for {ticker_name}: {formatted_strt} - {formatted_end}", divider='gray')

# Create column structure and adjust the number of empty columns on each side to center the main content
left_empty_col, col1, col2, col3, col4, right_empty_col = st.columns([0.5, 2, 2, 2, 2, 0.5])

# Place the KPI card for open price change
with col1:

    # Extract the values for Open, High, Low, Close for the most recent month
    open_recent = monthly_comparison_resampled.iloc[latest_index]['Open']
    # Extract the values for Open, High, Low, Close for the prior month
    open_prior = monthly_comparison_resampled.iloc[prior_index]['Open']
        
    if math.isnan(open_prior):
                open_growth = 'n/a'
                open_delta_color = 'off'
    else:
        open_growth = f'{((open_recent / open_prior) - 1)*100:,.2f}%'
        open_delta_color = 'normal'
    
    st.metric(
            label=f'{primary_ticker} Open Price',
            value=f'{open_recent:,.2f}',
            delta=open_growth,
            delta_color=open_delta_color
        )
   
# Place the KPI card for low price change
with col2:

    # Extract the values for Open, High, Low, Close for the most recent month
    low_recent = monthly_comparison_resampled.iloc[latest_index]['Low']
    # Extract the values for Open, High, Low, Close for the prior month
    low_prior = monthly_comparison_resampled.iloc[prior_index]['Low']
       
    if math.isnan(low_prior):
                low_growth = 'n/a'
                low_delta_color = 'off'
    else:
        low_growth = f'{((low_recent / low_prior) - 1)*100:,.2f}%'
        low_delta_color = 'normal'
    
    st.metric(
            label=f'{primary_ticker} Low Price',
            value=f'{low_recent:,.2f}',
            delta=low_growth,
            delta_color=low_delta_color
        )

# Place the KPI card for high price change
with col3:

    # Extract the values for Open, High, High, Close for the most recent month
    high_recent = monthly_comparison_resampled.iloc[latest_index]['High']
    # Extract the values for Open, High, High, Close for the prior month
    high_prior = monthly_comparison_resampled.iloc[prior_index]['High']
      
    if math.isnan(high_prior):
                high_growth = 'n/a'
                high_delta_color = 'off'
    else:
        high_growth = f'{((high_recent / high_prior) - 1)*100:,.2f}%'
        high_delta_color = 'normal'
    
    st.metric(
            label=f'{primary_ticker} High Price',
            value=f'{high_recent:,.2f}',
            delta=high_growth,
            delta_color=high_delta_color
        )

# Place the KPI card for close price change
with col4:

    # Extract the values for Open, Close, Close, Close for the most recent month
    close_recent = monthly_comparison_resampled.iloc[latest_index]['Close']
    # Extract the values for Open, Close, Close, Close for the prior month
    close_prior = monthly_comparison_resampled.iloc[prior_index]['Close']
        
    if math.isnan(close_prior):
                close_growth = 'n/a'
                close_delta_color = 'off'
    else:
        close_growth = f'{((close_recent / close_prior) - 1)*100:,.2f}%'
        close_delta_color = 'normal'
    
    st.metric(
            label=f'{primary_ticker} Close Price',
            value=f'{close_recent:,.2f}',
            delta=close_growth,
            delta_color=close_delta_color
        )

# Ensure start date is before end date
if selected_start_date > selected_end_date:
    st.error('Error: End date must be after start date.')
else:
    # Fetch historical data based on selected date range
    sub_data = all_data[(all_data.index >= selected_start_datetime) & (all_data.index <= selected_end_datetime)]


st.header(f"Price History for {ticker_name} and {comparison_name}: {formatted_selected_strt} - {formatted_selected_end}", divider='gray')

''

st.line_chart(
    sub_data,
    y='Close',
    color='Ticker',
)





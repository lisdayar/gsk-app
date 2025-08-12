import streamlit as st
import pandas as pd
import numpy as np
from io import StringIO
import time

uploaded_file = st.file_uploader("Choose a file")
if uploaded_file is not None:
    # To read file as bytes:
    bytes_data = uploaded_file.getvalue()
    st.write(bytes_data)

    # To convert to a string based IO:
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
    st.write(stringio)

    # To read file as string:
    string_data = stringio.read()
    st.write(string_data)

    # Can be used wherever a "file-like" object is accepted:
    data = pd.read_excel(uploaded_file, "GSK Gross Cost Report")
    st.write(data)

# PIB
excl_middle_df = data[data['Break Position'] != 'Middle']
excl_middle_results = excl_middle_df.groupby('Brand')['TVR'].sum().reset_index()
# Rename the 'TVR' column to 'PIB_Total_TVR'
excl_middle_results = excl_middle_results.rename(columns={'TVR': 'PIB_Total_TVR'})

# Filter and sum GRP based on subbrand per month
prime_df = data[(data['DayPart'] == '16:00-18:00') | (data['DayPart'] == '18:00-20:00') | (data['DayPart'] == '20:00-22:00')]
prime_results = prime_df.groupby('Brand')['TVR'].sum().reset_index()

# Rename the 'TVR' column to 'Prime_Total_TVR'
prime_results = prime_results.rename(columns={'TVR': 'Prime_Total_TVR'})

# Map the total TVR results to the original data DataFrame
data = pd.merge(data, excl_middle_results, on=['Brand'], how='left')
data = pd.merge(data, prime_results, on=['Brand'], how='left')

# Perform the calculations
data['PIB'] = data['TVR'] / data['PIB_Total_TVR']

# Use np.where for vectorized conditional assignment
data['Prime Time'] = np.where(
    (data['DayPart'] == '16:00-18:00') |
    (data['DayPart'] == '18:00-20:00') |
    (data['DayPart'] == '20:00-22:00'),
    data['TVR'] / data['Prime_Total_TVR'],
    'N/A'
)

# Handle potential division by zero or NaN values
data['PIB'] = data['PIB'].replace([float('inf'), float('-inf')], pd.NA)
data['Prime Time'] = data['Prime Time'].replace([float('inf'), float('-inf')], pd.NA)

# Replace NaN values resulting from the merge with 'N/A' if desired (optional, based on how you want to represent missing data)
data['PIB'] = data['PIB'].fillna('N/A')
data['Prime Time'] = data['Prime Time'].fillna('N/A')

# DATA STANDARDISATION

# Replace multiple values using a dictionary (mapping) --> Categories, Products (Subcategory)
# Intent with this is to make it scalable if there are others that need to be added on, we just add it to this dictionary.
replacement_map = {'Analgesics': 'Systemics', 'Cough & Cold Remedies': 'Respiratory', 'Dental Other': 'Toothpaste', 'Vitamin Supplements':'Vitamins'}
data['Subcategory'].replace(replacement_map, inplace = True)
data['Category'].replace('Dental', 'OHC', inplace = True)

# Replace values in 'Category' column where the product is 'Vitamin Supplements/Vitamins
data.loc[data['Subcategory'] == 'Vitamins', 'Category'] = 'Wellness'
data.loc[data['Subcategory'] == 'Indigestion Remedies', 'Category'] = 'OTC'
data.loc[data['Subcategory'] == 'Respiratory', 'Category'] = 'OTC'
data.loc[data['Subcategory'] == 'Liniment/Ointment/Salve', 'Category'] = 'OTC'
data.loc[data['Subcategory'] == 'Medical Other', 'Category'] = 'Other'

data_load_state = st.text('Starting computation...')
# Add a placeholder
latest_iteration = st.empty()
bar = st.progress(0)

for i in range(10):
  # Update the progress bar with each iteration.
  latest_iteration.text(f'Iteration {i+1}')
  bar.progress(i + 1)
  time.sleep(0.1)

data_load_state.text('...and now we\'re done!')

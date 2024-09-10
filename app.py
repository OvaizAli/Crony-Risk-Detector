import streamlit as st
import pandas as pd
import pickle
from datetime import datetime

# Load the saved LabelEncoder and Prophet model
with open('label_encoder.pkl', 'rb') as f:
    label_encoder = pickle.load(f)

with open('unified_prophet_model.pkl', 'rb') as f:
    loaded_model = pickle.load(f)

# Streamlit app
st.title('Anomaly Detection for Void Transactions')

# User input form
with st.form(key='input_form'):
    cashier_name = st.text_input('Cashier Name', 'Arif')
    void_amount = st.number_input('Void Amount', min_value=0.0, value=5000.0)
    void_count = st.number_input('Void Count', min_value=0, value=10)
    test_date = st.date_input('Date', value=datetime.now())

    submit_button = st.form_submit_button(label='Submit')

if submit_button:
    # Create the test data as a pandas DataFrame
    test_data = pd.DataFrame({
        'Date': [test_date],
        'Cashier Name': [cashier_name],
        'Void Amount': [void_amount],
        'Void Count': [void_count],
        'Rolling Void Amount': [void_amount]  # Simplified for demo
    })

    # Convert 'Date' to the correct format
    test_data['Date'] = pd.to_datetime(test_data['Date']).dt.date

    # Encode the 'Cashier Name' using the loaded LabelEncoder
    test_data['Cashier Name Encoded'] = label_encoder.transform(test_data['Cashier Name'])

    # Prepare the data for Prophet prediction
    test_data_prophet = test_data[['Date', 'Void Amount', 'Cashier Name Encoded', 'Void Count', 'Rolling Void Amount']].rename(columns={'Date': 'ds', 'Void Amount': 'y'})

    # Convert 'ds' to datetime64[ns] in test_data_prophet
    test_data_prophet['ds'] = pd.to_datetime(test_data_prophet['ds'])

    # Create a DataFrame for Prophet prediction with the exact test date
    future = pd.DataFrame({
        'ds': test_data_prophet['ds'],
        'Cashier Name Encoded': test_data['Cashier Name Encoded'],
        '7d_rolling_void_count': test_data_prophet['Void Count'],
        '7d_rolling_void_amount': test_data_prophet['Rolling Void Amount']
    })

    # Make predictions for the test data using the actual test date
    forecast = loaded_model.predict(future)

    # Detect anomalies by comparing actual value and predicted value
    anomalies = pd.merge(test_data_prophet, forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']], on='ds')

    # Function to calculate probability of being an anomaly
    def calculate_anomaly_probability(row):
        if row['y'] < row['yhat_lower']:  # Actual value is below lower bound
            return abs(row['y'] - row['yhat_lower']) / abs(row['yhat_upper'] - row['yhat_lower']) * 100
        elif row['y'] > row['yhat_upper']:  # Actual value is above upper bound
            return abs(row['y'] - row['yhat_upper']) / abs(row['yhat_upper'] - row['yhat_lower']) * 100
        else:
            return 0  # No anomaly

    # Apply the anomaly probability calculation
    anomalies['prob_anomaly'] = anomalies.apply(calculate_anomaly_probability, axis=1)

    # Unencode the cashier name for final output
    anomalies['Cashier Name'] = label_encoder.inverse_transform(anomalies['Cashier Name Encoded'])

    # Display the results
    st.write("Prediction, Anomaly Detection, Void Frequency, and Probability for the Test Instance:")
    st.write(anomalies[['ds', 'Cashier Name', 'y', 'Void Count', 'yhat', 'yhat_lower', 'yhat_upper', 'prob_anomaly']])

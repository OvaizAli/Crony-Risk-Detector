import streamlit as st
import joblib
import pandas as pd
from datetime import datetime

# Load the saved LabelEncoder and Prophet model
label_encoder = joblib.load('label_encoder.joblib')
loaded_model = joblib.load('unified_prophet_model.joblib')

# Streamlit app
st.title('Anomaly Detection with Prophet')

# User input
test_cashier_name = st.text_input('Cashier Name', 'Arif')
test_date = st.date_input('Date', datetime.now())
test_void_amount = st.number_input('Void Amount', min_value=0.0, value=47.01)
test_void_count = st.number_input('Void Count', min_value=0, value=2)

# Button to trigger prediction
if st.button('Predict'):
    # Prepare the test data
    test_data = pd.DataFrame({
        'Date': [test_date],
        'Cashier Name': [test_cashier_name],
        'Void Amount': [test_void_amount],
        'Void Count': [test_void_count],
        'Rolling Void Amount': [test_void_amount]  # Simplified for demo
    })

    # Convert 'Date' to the correct format
    test_data['Date'] = pd.to_datetime(test_data['Date']).dt.date

    # Encode the 'Cashier Name'
    test_data['Cashier Name Encoded'] = label_encoder.transform(test_data['Cashier Name'])

    # Prepare the data for Prophet prediction
    test_data_prophet = test_data[['Date', 'Void Amount', 'Cashier Name Encoded', 'Void Count', 'Rolling Void Amount']].rename(columns={'Date': 'ds', 'Void Amount': 'y'})

    # Convert 'ds' to datetime64[ns] for Prophet
    test_data_prophet['ds'] = pd.to_datetime(test_data_prophet['ds'])

    # Create a DataFrame for Prophet prediction
    future = pd.DataFrame({
        'ds': test_data_prophet['ds'],
        'Cashier Name Encoded': test_data['Cashier Name Encoded'],
        '7d_rolling_void_count': test_data_prophet['Void Count'],
        '7d_rolling_void_amount': test_data_prophet['Rolling Void Amount']
    })

    # Make predictions
    forecast = loaded_model.predict(future)

    # Detect anomalies
    anomalies = pd.merge(test_data_prophet, forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']], on='ds')

    def calculate_anomaly_probability(row):
        if row['y'] < row['yhat_lower']:  # Actual value is below lower bound
            return min(abs(row['y'] - row['yhat_lower']) / abs(row['yhat_upper'] - row['yhat_lower']) * 100, 100)
        elif row['y'] > row['yhat_upper']:  # Actual value is above upper bound
            return min(abs(row['y'] - row['yhat_upper']) / abs(row['yhat_upper'] - row['yhat_lower']) * 100, 100)
        else:
            return 0  # No anomaly


    anomalies['prob_anomaly'] = anomalies.apply(calculate_anomaly_probability, axis=1)
    anomalies['Cashier Name'] = label_encoder.inverse_transform(anomalies['Cashier Name Encoded'])

    # Display the probability of anomaly
    anomaly_probability = anomalies['prob_anomaly'].iloc[0]
    st.write(f"The probability that this transaction is an anomaly is {anomaly_probability:.2f}%")

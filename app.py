import streamlit as st
import joblib
import pandas as pd
import sklearn
from sklearn.preprocessing import StandardScaler
from datetime import datetime


# Load the saved model, label encoders, and scaler
iso_forest = joblib.load('isolation_forest_model.joblib')
label_encoder = joblib.load('label_encoder.joblib')
register_encoder = joblib.load('register_encoder.joblib')
scaler = joblib.load('scaler.joblib')

# Streamlit app title
st.title('Anomaly Detection for Void Transactions')

# User inputs for the transaction
test_cashier_name = st.text_input('Cashier Name', 'Arif')
test_register_id = st.number_input('Register ID', min_value=1, value=2)
test_date = st.date_input('Date', datetime.now())
test_total_amount = st.number_input('Total Amount', min_value=0.0, value=190.4)
test_total_items = st.number_input('Total Items', min_value=1, value=28)
test_void_amount = st.number_input('Void Amount', min_value=0.0, value=47.01)
test_void_count = st.number_input('Void Count', min_value=0, value=2)
test_return_amount = st.number_input('Return Amount', min_value=0.0, value=0.0)
test_return_count = st.number_input('Return Count', min_value=0, value=0)

# Button to trigger prediction
if st.button('Predict'):
    try:
        # Ensure correct data types for each input
        test_transaction = {
            'Receipt#': [1],  # Assuming a placeholder value
            'Total Amount': [float(test_total_amount)],  # Convert to float
            'Total Items': [int(test_total_items)],  # Convert to integer
            'Date': [pd.to_datetime(test_date)],  # Convert to datetime
            'Void Count': [int(test_void_count)],  # Convert to integer
            'Void Amount': [float(test_void_amount)],  # Convert to float
            'Return Count': [int(test_return_count)],  # Convert to integer
            'Return Amount': [float(test_return_amount)],  # Convert to float
            'Cashier Name': [str(test_cashier_name)],  # Ensure string
            'Register ID': [int(test_register_id)]  # Convert to integer
        }

        # Convert the dictionary to a DataFrame
        test_data = pd.DataFrame(test_transaction)

        # Prepare the rolling void features
        test_data['7d_rolling_void_count'] = test_data['Void Count']  # Simplified for testing
        test_data['7d_rolling_void_amount'] = test_data['Void Amount']  # Simplified for testing

        # Create additional feature ratios
        test_data['Void_to_Total_Amount_Ratio'] = test_data['Void Amount'] / test_data['Total Amount']
        test_data['Void_to_Items_Ratio'] = test_data['Void Count'] / test_data['Total Items']
        test_data['Return_to_Total_Amount_Ratio'] = test_data['Return Amount'] / test_data['Total Amount']

        # Encode the 'Cashier Name' and 'Register ID'
        test_data['Cashier Name Encoded'] = label_encoder.transform(test_data['Cashier Name'])
        test_data['Register ID Encoded'] = register_encoder.transform(test_data['Register ID'])

        # Select the relevant features for prediction
        test_features = test_data[['Void Amount', '7d_rolling_void_count', '7d_rolling_void_amount', 
                                   'Void_to_Total_Amount_Ratio', 'Void_to_Items_Ratio', 'Return_to_Total_Amount_Ratio', 
                                   'Cashier Name Encoded', 'Register ID Encoded']]

        # Scale the features
        scaled_test_features = scaler.transform(test_features)

        # Predict using the Isolation Forest model
        anomaly_score = iso_forest.predict(scaled_test_features)

        # Get the anomaly score (decision function)
        anomaly_probability = iso_forest.decision_function(scaled_test_features)
        probability_of_anomaly = 1 - (anomaly_probability[0] + 1) / 2  # Convert to a [0, 1] range

        # Display the result
        if anomaly_score[0] == -1:
            st.write(f"Transaction is an anomaly.")
            st.write(f"The probability of this transaction being an anomaly is {probability_of_anomaly * 100:.2f}%.")
        else:
            st.write(f"Transaction is normal.")
            st.write(f"The probability of this transaction being an anomaly is {probability_of_anomaly * 100:.2f}%.")
    
    except Exception as e:
        st.error(f"An error occurred: {e}")

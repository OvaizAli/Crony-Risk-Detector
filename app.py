import streamlit as st
import joblib
import pandas as pd
import shap
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from datetime import datetime

# Load the saved model, label encoders, and scaler
iso_forest = joblib.load('isolation_forest_model.joblib')
label_encoder = joblib.load('label_encoder.joblib')
register_encoder = joblib.load('register_encoder.joblib')
scaler = joblib.load('scaler.joblib')

# Load the dataset
data_path = 'retail_store_data.csv'  
df = pd.read_csv(data_path)

# Extract unique values for dropdowns
cashier_names = df['Cashier Name'].unique().tolist()
register_ids = df['Register ID'].unique().tolist()

# Streamlit app title
st.title('Anomaly Detection of Void Transactions')

# User inputs for the transaction
test_cashier_name = st.selectbox('Cashier Name', cashier_names)
test_register_id = st.selectbox('Register ID', register_ids)
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
        # Prepare the test data
        test_transaction = {
            'Receipt#': [1], 
            'Total Amount': [float(test_total_amount)],
            'Total Items': [int(test_total_items)],  
            'Date': [pd.to_datetime(test_date)],  
            'Void Count': [int(test_void_count)],  
            'Void Amount': [float(test_void_amount)],  
            'Return Count': [int(test_return_count)],  
            'Return Amount': [float(test_return_amount)],  
            'Cashier Name': [str(test_cashier_name)],  
            'Register ID': [int(test_register_id)]  
        }

        test_data = pd.DataFrame(test_transaction)

        # Prepare the rolling void features
        test_data['7d_rolling_void_count'] = test_data['Void Count']  
        test_data['7d_rolling_void_amount'] = test_data['Void Amount']  

        # Create additional feature ratios
        test_data['Void_to_Total_Amount_Ratio'] = test_data['Void Amount'] / test_data['Total Amount']
        test_data['Void_to_Items_Ratio'] = test_data['Void Count'] / test_data['Total Items']
        test_data['Return_to_Total_Amount_Ratio'] = test_data['Return Amount'] / test_data['Total Amount']

        # Encode 'Cashier Name' and 'Register ID'
        test_data['Cashier Name Encoded'] = label_encoder.transform(test_data['Cashier Name'])
        test_data['Register ID Encoded'] = register_encoder.transform(test_data['Register ID'])

        test_features = test_data[['Void Amount', '7d_rolling_void_count', '7d_rolling_void_amount',
                                   'Void_to_Total_Amount_Ratio', 'Void_to_Items_Ratio', 'Return_to_Total_Amount_Ratio',
                                   'Cashier Name Encoded', 'Register ID Encoded']]

        scaled_test_features = scaler.transform(test_features)

        # Predict using the Isolation Forest model
        anomaly_score = iso_forest.predict(scaled_test_features)

        # Get the anomaly score (decision function)
        anomaly_probability = iso_forest.decision_function(scaled_test_features)
        probability_of_anomaly = 1 - (anomaly_probability[0] + 1) / 2

        # Display the result with success and warning messages
        if anomaly_score[0] == -1:
            st.warning(f"Transaction is flagged as an anomaly with the probability of {probability_of_anomaly * 100:.2f}%.")
        else:
            st.success(f"Transaction is classified as normal with the probability of {(1 - probability_of_anomaly) * 100:.2f}%.")

        # Explain the prediction using SHAP
        explainer = shap.TreeExplainer(iso_forest)
        shap_values = explainer.shap_values(scaled_test_features)

        # Provide textual explanation of SHAP values
        feature_descriptions = {
            'Void Amount': 'high void amount',
            '7d_rolling_void_count': 'frequent void transactions in the last 7 days',
            '7d_rolling_void_amount': 'high value of voids in the last 7 days',
            'Void_to_Total_Amount_Ratio': 'high ratio of void amount to total transaction amount',
            'Void_to_Items_Ratio': 'high ratio of void count to total items in the transaction',
            'Return_to_Total_Amount_Ratio': 'high ratio of return amount to total transaction amount',
            'Cashier Name Encoded': 'cashier involved in the transaction',
            'Register ID Encoded': 'register used for the transaction'
        }

        shap_explanations = sorted(zip(feature_descriptions.keys(), shap_values[0]), key=lambda x: abs(x[1]), reverse=True)

        if anomaly_score[0] == -1:
            features_contributing_to_anomaly = ', '.join([f"{feature_descriptions[feature]}" for feature, importance in shap_explanations if importance > 0])
            st.warning(f"Features contributing to the anomaly: {features_contributing_to_anomaly}.")
        else:
            st.success("No significant features contributed to making this transaction anomalous.")

    except Exception as e:
        st.error(f"An error occurred: {e}")

import joblib
import pandas as pd
from datetime import datetime

# Load the saved LabelEncoder and Prophet model
label_encoder = joblib.load('label_encoder.joblib')
loaded_model = joblib.load('unified_prophet_model.joblib')

# Example test inputs
test_cashier_name = 'Arif'
test_date = datetime.now()
test_void_amount = 5000
test_void_count = 10

# Prepare the test data
test_data = pd.DataFrame({
    'Date': [test_date],
    'Cashier Name': [test_cashier_name],
    'Void Amount': [test_void_amount],
    'Void Count': [test_void_count],
    'Rolling Void Amount': [test_void_amount]
})

# Convert 'Date' to the correct format
test_data['Date'] = pd.to_datetime(test_data['Date']).dt.date

# Encode the 'Cashier Name'
test_data['Cashier Name Encoded'] = label_encoder.transform(test_data['Cashier Name'])

# Prepare the data for Prophet prediction
test_data_prophet = test_data[['Date', 'Void Amount', 'Cashier Name Encoded', 'Void Count', 'Rolling Void Amount']].rename(columns={'Date': 'ds', 'Void Amount': 'y'})

# Convert 'ds' to datetime64[ns]
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

# Function to calculate anomaly probability
def calculate_anomaly_probability(row):
    if row['y'] < row['yhat_lower']:
        return abs(row['y'] - row['yhat_lower']) / abs(row['yhat_upper'] - row['yhat_lower']) * 100
    elif row['y'] > row['yhat_upper']:
        return abs(row['y'] - row['yhat_upper']) / abs(row['yhat_upper'] - row['yhat_lower']) * 100
    else:
        return 0

anomalies['prob_anomaly'] = anomalies.apply(calculate_anomaly_probability, axis=1)
anomalies['Cashier Name'] = label_encoder.inverse_transform(anomalies['Cashier Name Encoded'])

# Display the results
print("Prediction, Anomaly Detection, Void Frequency, and Probability for the Test Instance:")
print(anomalies[['ds', 'Cashier Name', 'y', 'Void Count', 'yhat', 'yhat_lower', 'yhat_upper', 'prob_anomaly']])

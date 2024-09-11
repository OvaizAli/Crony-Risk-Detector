import streamlit as st
import pandas as pd

# Define the Streamlit app
def main():
    st.title('Receipt Data Processor')

    # Upload the file (supports CSV and Excel)
    uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xls", "xlsx"])

    if uploaded_file is not None:
        try:
            # Check the file extension and read accordingly
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            st.success("File uploaded successfully!")

            # Display the DataFrame
            st.dataframe(df.head())

            # Check if the required columns are present
            required_columns = [
                'Receipt#', 'Total Amount', 'Total Items', 'Date', 
                'Void Count', 'Void Amount', 'Return Count', 
                'Return Amount', 'Cashier Name', 'Register ID'
            ]

            if all(col in df.columns for col in required_columns):
                st.success("The file contains all the required columns!")

                # Calculate means for the four attributes
                void_count_mean = df['Void Count'].mean()
                void_amount_mean = df['Void Amount'].mean()
                return_count_mean = df['Return Count'].mean()
                return_amount_mean = df['Return Amount'].mean()

                # Display calculated means in separate lines using markdown with escaped dollar sign
                st.markdown(
                    f"**Calculated Mean Values:**  \n"
                    f"• **Mean Void Count**: {void_count_mean:.2f}  \n"
                    f"• **Mean Void Amount**: \${void_amount_mean:.2f}  \n"
                    f"• **Mean Return Count**: {return_count_mean:.2f}  \n"
                    f"• **Mean Return Amount**: \${return_amount_mean:.2f}"
                )

                # Create a new column to count how often each attribute exceeds the mean
                df['Exceeds Void Count'] = (df['Void Count'] > void_count_mean).astype(int)
                df['Exceeds Void Amount'] = (df['Void Amount'] > void_amount_mean).astype(int)
                df['Exceeds Return Count'] = (df['Return Count'] > return_count_mean).astype(int)
                df['Exceeds Return Amount'] = (df['Return Amount'] > return_amount_mean).astype(int)

                # 1. Calculate the Risk for Cashiers

                # Group by Cashier Name and count the number of risky attributes
                cashier_stats = df.groupby('Cashier Name').agg(
                    total_transactions=('Receipt#', 'count'),
                    exceeds_void_count=('Exceeds Void Count', 'sum'),
                    exceeds_void_amount=('Exceeds Void Amount', 'sum'),
                    exceeds_return_count=('Exceeds Return Count', 'sum'),
                    exceeds_return_amount=('Exceeds Return Amount', 'sum')
                ).reset_index()

                # Calculate the normalized risk score (how often they exceed per transaction)
                cashier_stats['Risk Score'] = (
                    (cashier_stats['exceeds_void_count'] + 
                     cashier_stats['exceeds_void_amount'] + 
                     cashier_stats['exceeds_return_count'] + 
                     cashier_stats['exceeds_return_amount']) / 
                    cashier_stats['total_transactions']
                )

                # Find the cashier with the highest normalized risk score
                most_risky_cashier = cashier_stats.sort_values(by='Risk Score', ascending=False).iloc[0]

                # Display the most risky cashier with risk details
                st.markdown(
                    f"**Most Risky Cashier**:  \n"
                    f"• **Cashier Name**: {most_risky_cashier['Cashier Name']}  \n"
                    f"• **Risk Score**: {most_risky_cashier['Risk Score']:.2f}  \n"
                    f"• **Total Transactions**: {most_risky_cashier['total_transactions']}"
                )

                # Display all cashier risk scores
                st.success("Risk Scores for All Cashiers:")
                st.dataframe(cashier_stats[['Cashier Name', 'total_transactions', 'Risk Score']])

                # 2. Calculate the Risk for Receipts

                # Group by Receipt# and count the number of risky attributes
                receipt_stats = df.groupby('Receipt#').agg(
                    exceeds_void_count=('Exceeds Void Count', 'sum'),
                    exceeds_void_amount=('Exceeds Void Amount', 'sum'),
                    exceeds_return_count=('Exceeds Return Count', 'sum'),
                    exceeds_return_amount=('Exceeds Return Amount', 'sum')
                ).reset_index()

                # Calculate the risk score for each receipt
                receipt_stats['Risk Score'] = (
                    receipt_stats['exceeds_void_count'] + 
                    receipt_stats['exceeds_void_amount'] + 
                    receipt_stats['exceeds_return_count'] + 
                    receipt_stats['exceeds_return_amount']
                )

                # Find the receipt with the highest risk score
                most_risky_receipt = receipt_stats.sort_values(by='Risk Score', ascending=False).iloc[0]

                # Display the most risky receipt number with risk details
                st.markdown(
                    f"**Most Risky Receipt**:  \n"
                    f"• **Receipt Number**: {most_risky_receipt['Receipt#']}  \n"
                    f"• **Risk Score**: {most_risky_receipt['Risk Score']}"
                )

                # Display all receipt risk scores
                st.success("Risk Scores for All Receipts:")
                st.dataframe(receipt_stats[['Receipt#', 'Risk Score']])

            else:
                st.error("The file does not contain all the required columns.")
        except Exception as e:
            st.error(f"An error occurred while processing the file: {e}")

if __name__ == "__main__":
    main()

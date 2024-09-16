import streamlit as st
import pandas as pd

# Define the Streamlit app
def main():
    st.title('Crony Risk Detector')

    # Upload the file (supports CSV and Excel)
    uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xls", "xlsx"])

    if uploaded_file is not None:
        try:
            # Check the file extension and read accordingly
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            # Check if the required columns are present
            required_columns = [
                'Receipt#', 'Total Amount', 'Total Items', 'Date', 
                'Void Count', 'Void Amount', 'Return Count', 
                'Return Amount', 'Cashier Name', 'Register ID'
            ]

            if all(col in df.columns for col in required_columns):
                # Convert 'Date' column to datetime and handle parsing errors
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

                # Check if any NaT values are present after date parsing
                if df['Date'].isnull().any():
                    st.warning("Date timestamps could not be parsed, so day-wise analysis will be skipped.")
                    df.drop(columns='Date', inplace=True)

                    # 1. Calculate overall means for key attributes
                    overall_void_count_mean = df['Void Count'].mean()
                    overall_void_amount_mean = df['Void Amount'].mean()
                    overall_return_count_mean = df['Return Count'].mean()
                    overall_return_amount_mean = df['Return Amount'].mean()
                    overall_total_amount_mean = df['Total Amount'].mean()
                    overall_total_items_mean = df['Total Items'].mean()

                    # Create new columns to compare values with overall means
                    df['Exceeds Overall Mean Void Count'] = (df['Void Count'] > overall_void_count_mean).astype(int)
                    df['Exceeds Overall Mean Void Amount'] = (df['Void Amount'] > overall_void_amount_mean).astype(int)
                    df['Exceeds Overall Mean Return Count'] = (df['Return Count'] > overall_return_count_mean).astype(int)
                    df['Exceeds Overall Mean Return Amount'] = (df['Return Amount'] > overall_return_amount_mean).astype(int)
                    df['Below Overall Mean Total Amount'] = (df['Total Amount'] < overall_total_amount_mean).astype(int)
                    df['Below Overall Mean Total Items'] = (df['Total Items'] < overall_total_items_mean).astype(int)

                    # Display the DataFrame with overall comparisons
                    st.dataframe(df)

                                      # Create a DataFrame for overall means
                    overall_means_data = {
                        'Metric': [
                            'Overall Mean Void Count',
                            'Overall Mean Void Amount',
                            'Overall Mean Return Count',
                            'Overall Mean Return Amount',
                            'Overall Mean Total Amount',
                            'Overall Mean Total Items'
                        ],
                        'Value': [
                            overall_void_count_mean,
                            f"${overall_void_amount_mean:.2f}",
                            overall_return_count_mean,
                            f"${overall_return_amount_mean:.2f}",
                            f"${overall_total_amount_mean:.2f}",
                            overall_total_items_mean
                        ]
                    }

                    overall_means_df = pd.DataFrame(overall_means_data)

                    st.success("Overall Mean Calulations")

                    # Display the DataFrame in Streamlit
                    st.dataframe(overall_means_df)

                    # 2. Calculate Risk Scores for Cashiers
                    cashier_stats = df.groupby('Cashier Name').agg(
                        total_transactions=('Receipt#', 'count'),
                        exceeds_overall_void_count=('Exceeds Overall Mean Void Count', 'sum'),
                        exceeds_overall_void_amount=('Exceeds Overall Mean Void Amount', 'sum'),
                        exceeds_overall_return_count=('Exceeds Overall Mean Return Count', 'sum'),
                        exceeds_overall_return_amount=('Exceeds Overall Mean Return Amount', 'sum'),
                        below_overall_total_amount=('Below Overall Mean Total Amount', 'sum'),
                        below_overall_total_items=('Below Overall Mean Total Items', 'sum')
                    ).reset_index()

                    # Calculate the risk score for cashiers based on overall means
                    cashier_stats['Risk Score'] = (
                        (cashier_stats['exceeds_overall_void_count'] +
                         cashier_stats['exceeds_overall_void_amount'] +
                         cashier_stats['exceeds_overall_return_count'] +
                         cashier_stats['exceeds_overall_return_amount'] +
                         cashier_stats['below_overall_total_amount'] +
                         cashier_stats['below_overall_total_items']) / 
                         cashier_stats['total_transactions']
                    )

                    # Find the cashier with the highest risk score
                    most_risky_cashier = cashier_stats.sort_values(by='Risk Score', ascending=False).iloc[0]

                    # Display cashier risk scores
                    st.success("Risk Scores for Cashiers (Overall):")
                    st.dataframe(cashier_stats[['Cashier Name', 'total_transactions', 'Risk Score']].sort_values(by='Risk Score', ascending=False, ignore_index=True))

                    # Display the most risky cashier
                    st.markdown(
                        f"**Most Risky Cashier**:  \n"
                        f"• **Cashier Name**: {most_risky_cashier['Cashier Name']}  \n"
                        f"• **Risk Score**: {most_risky_cashier['Risk Score']:.2f}  \n"
                        f"• **Total Transactions**: {most_risky_cashier['total_transactions']}"
                    )

                    # 3. Calculate Risk Scores for Receipts
                    receipt_stats = df.groupby('Receipt#').agg(
                        total_transactions=('Receipt#', 'count'),
                        exceeds_overall_void_count=('Exceeds Overall Mean Void Count', 'sum'),
                        exceeds_overall_void_amount=('Exceeds Overall Mean Void Amount', 'sum'),
                        exceeds_overall_return_count=('Exceeds Overall Mean Return Count', 'sum'),
                        exceeds_overall_return_amount=('Exceeds Overall Mean Return Amount', 'sum'),
                        below_overall_total_amount=('Below Overall Mean Total Amount', 'sum'),
                        below_overall_total_items=('Below Overall Mean Total Items', 'sum')
                    ).reset_index()

                    # Calculate the risk score for receipts based on overall means
                    receipt_stats['Risk Score'] = (
                        (receipt_stats['exceeds_overall_void_count'] +
                         receipt_stats['exceeds_overall_void_amount'] +
                         receipt_stats['exceeds_overall_return_count'] +
                         receipt_stats['exceeds_overall_return_amount'] +
                         receipt_stats['below_overall_total_amount'] +
                         receipt_stats['below_overall_total_items']) / 
                         receipt_stats['total_transactions']
                    )

                    # Find the receipt with the highest risk score
                    max_risk_score = receipt_stats['Risk Score'].max()
                    most_risky_receipt = receipt_stats[receipt_stats['Risk Score'] == max_risk_score][['Receipt#', 'Risk Score']]

                    # Display receipt risk scores
                    st.success("Risk Scores for Top 10 Receipts (Overall):")
                    st.dataframe(receipt_stats[['Receipt#', 'Risk Score']].sort_values(by='Risk Score', ascending=False, ignore_index=True))

                    # Display the most risky receipt
                    most_risky_receipt_numbers = most_risky_receipt['Receipt#'][:10].tolist()
                    st.markdown(
                        f"**Most Risky Receipt Number(s)**:  \n"
                        f"• **Receipt Numbers**: {', '.join(map(str, most_risky_receipt_numbers))}  \n"
                        f"• **Risk Score**: {max_risk_score:.2f}"
                    )

                else:
                    st.success("Calculations for the Risk Analysis - Both day-wise and overall analysis.")

                    # Extract the day of the week
                    df['Day'] = df['Date'].dt.day_name()

                    # 1. Calculate overall means for key attributes
                    overall_void_count_mean = df['Void Count'].mean()
                    overall_void_amount_mean = df['Void Amount'].mean()
                    overall_return_count_mean = df['Return Count'].mean()
                    overall_return_amount_mean = df['Return Amount'].mean()
                    overall_total_amount_mean = df['Total Amount'].mean()
                    overall_total_items_mean = df['Total Items'].mean()

                    # 2. Group data by day of the week and calculate daily means
                    day_wise_means = df.groupby('Day').agg(
                        mean_void_count=('Void Count', 'mean'),
                        mean_void_amount=('Void Amount', 'mean'),
                        mean_return_count=('Return Count', 'mean'),
                        mean_return_amount=('Return Amount', 'mean'),
                        mean_total_amount=('Total Amount', 'mean'),
                        mean_total_items=('Total Items', 'mean')
                    ).reset_index()

                    # Merge daily means back to the main dataframe
                    df = pd.merge(df, day_wise_means, on='Day', how='left')

                    # 3. Create new columns to compare values with both day-wise and overall means
                    df['Exceeds Day Mean Void Count'] = (df['Void Count'] > df['mean_void_count']).astype(int)
                    df['Exceeds Day Mean Void Amount'] = (df['Void Amount'] > df['mean_void_amount']).astype(int)
                    df['Exceeds Day Mean Return Count'] = (df['Return Count'] > df['mean_return_count']).astype(int)
                    df['Exceeds Day Mean Return Amount'] = (df['Return Amount'] > df['mean_return_amount']).astype(int)
                    df['Below Day Mean Total Amount'] = (df['Total Amount'] < df['mean_total_amount']).astype(int)
                    df['Below Day Mean Total Items'] = (df['Total Items'] < df['mean_total_items']).astype(int)

                    # Compare with overall means
                    df['Exceeds Overall Mean Void Count'] = (df['Void Count'] > overall_void_count_mean).astype(int)
                    df['Exceeds Overall Mean Void Amount'] = (df['Void Amount'] > overall_void_amount_mean).astype(int)
                    df['Exceeds Overall Mean Return Count'] = (df['Return Count'] > overall_return_count_mean).astype(int)
                    df['Exceeds Overall Mean Return Amount'] = (df['Return Amount'] > overall_return_amount_mean).astype(int)
                    df['Below Overall Mean Total Amount'] = (df['Total Amount'] < overall_total_amount_mean).astype(int)
                    df['Below Overall Mean Total Items'] = (df['Total Items'] < overall_total_items_mean).astype(int)

                    # Display the DataFrame with both day-wise and overall comparisons
                    st.dataframe(df)

                    # Create a DataFrame for overall means
                    overall_means_data = {
                        'Metric': [
                            'Overall Mean Void Count',
                            'Overall Mean Void Amount',
                            'Overall Mean Return Count',
                            'Overall Mean Return Amount',
                            'Overall Mean Total Amount',
                            'Overall Mean Total Items'
                        ],
                        'Value': [
                            overall_void_count_mean,
                            f"${overall_void_amount_mean:.2f}",
                            overall_return_count_mean,
                            f"${overall_return_amount_mean:.2f}",
                            f"${overall_total_amount_mean:.2f}",
                            overall_total_items_mean
                        ]
                    }

                    overall_means_df = pd.DataFrame(overall_means_data)

                    st.success("Overall Mean Calulations")

                    # Display the DataFrame in Streamlit
                    st.dataframe(overall_means_df)

                    st.success("Day-Wise Mean Calulations")

                    st.dataframe(day_wise_means)

                    # 4. Calculate Risk Scores for Cashiers
                    cashier_stats = df.groupby('Cashier Name').agg(
                        total_transactions=('Receipt#', 'count'),
                        exceeds_day_void_count=('Exceeds Day Mean Void Count', 'sum'),
                        exceeds_day_void_amount=('Exceeds Day Mean Void Amount', 'sum'),
                        exceeds_day_return_count=('Exceeds Day Mean Return Count', 'sum'),
                        exceeds_day_return_amount=('Exceeds Day Mean Return Amount', 'sum'),
                        below_day_total_amount=('Below Day Mean Total Amount', 'sum'),
                        below_day_total_items=('Below Day Mean Total Items', 'sum'),
                        exceeds_overall_void_count=('Exceeds Overall Mean Void Count', 'sum'),
                        exceeds_overall_void_amount=('Exceeds Overall Mean Void Amount', 'sum'),
                        exceeds_overall_return_count=('Exceeds Overall Mean Return Count', 'sum'),
                        exceeds_overall_return_amount=('Exceeds Overall Mean Return Amount', 'sum'),
                        below_overall_total_amount=('Below Overall Mean Total Amount', 'sum'),
                        below_overall_total_items=('Below Overall Mean Total Items', 'sum')
                    ).reset_index()

                    # Calculate the risk score for cashiers (including both day-wise and overall means)
                    cashier_stats['Risk Score'] = (
                        (cashier_stats['exceeds_day_void_count'] +
                         cashier_stats['exceeds_day_void_amount'] +
                         cashier_stats['exceeds_day_return_count'] +
                         cashier_stats['exceeds_day_return_amount'] +
                         cashier_stats['below_day_total_amount'] +
                         cashier_stats['below_day_total_items'] +
                         cashier_stats['exceeds_overall_void_count'] +
                         cashier_stats['exceeds_overall_void_amount'] +
                         cashier_stats['exceeds_overall_return_count'] +
                         cashier_stats['exceeds_overall_return_amount'] +
                         cashier_stats['below_overall_total_amount'] +
                         cashier_stats['below_overall_total_items']) /
                         cashier_stats['total_transactions']
                    )

                    # Find the cashier with the highest risk score
                    most_risky_cashier = cashier_stats.sort_values(by='Risk Score', ascending=False).iloc[0]

                    # Display cashier risk scores
                    st.success("Risk Scores for Cashiers (Day-wise and Overall):")
                    st.dataframe(cashier_stats[['Cashier Name', 'total_transactions', 'Risk Score']].sort_values(by='Risk Score', ascending=False, ignore_index=True))

                    # Display the most risky cashier
                    st.markdown(
                        f"**Most Risky Cashier**:  \n"
                        f"• **Cashier Name**: {most_risky_cashier['Cashier Name']}  \n"
                        f"• **Risk Score**: {most_risky_cashier['Risk Score']:.2f}  \n"
                        f"• **Total Transactions**: {most_risky_cashier['total_transactions']}"
                    )

                    # 5. Calculate Risk Scores for Receipts
                    receipt_stats = df.groupby('Receipt#').agg(
                        total_transactions=('Receipt#', 'count'),
                        exceeds_day_void_count=('Exceeds Day Mean Void Count', 'sum'),
                        exceeds_day_void_amount=('Exceeds Day Mean Void Amount', 'sum'),
                        exceeds_day_return_count=('Exceeds Day Mean Return Count', 'sum'),
                        exceeds_day_return_amount=('Exceeds Day Mean Return Amount', 'sum'),
                        below_day_total_amount=('Below Day Mean Total Amount', 'sum'),
                        below_day_total_items=('Below Day Mean Total Items', 'sum'),
                        exceeds_overall_void_count=('Exceeds Overall Mean Void Count', 'sum'),
                        exceeds_overall_void_amount=('Exceeds Overall Mean Void Amount', 'sum'),
                        exceeds_overall_return_count=('Exceeds Overall Mean Return Count', 'sum'),
                        exceeds_overall_return_amount=('Exceeds Overall Mean Return Amount', 'sum'),
                        below_overall_total_amount=('Below Overall Mean Total Amount', 'sum'),
                        below_overall_total_items=('Below Overall Mean Total Items', 'sum')
                    ).reset_index()

                    # Calculate the risk score for receipts (including both day-wise and overall means)
                    receipt_stats['Risk Score'] = (
                        (receipt_stats['exceeds_day_void_count'] +
                         receipt_stats['exceeds_day_void_amount'] +
                         receipt_stats['exceeds_day_return_count'] +
                         receipt_stats['exceeds_day_return_amount'] +
                         receipt_stats['below_day_total_amount'] +
                         receipt_stats['below_day_total_items'] +
                         receipt_stats['exceeds_overall_void_count'] +
                         receipt_stats['exceeds_overall_void_amount'] +
                         receipt_stats['exceeds_overall_return_count'] +
                         receipt_stats['exceeds_overall_return_amount'] +
                         receipt_stats['below_overall_total_amount'] +
                         receipt_stats['below_overall_total_items']) /
                         receipt_stats['total_transactions']
                    )

                    # Find the receipt with the highest risk score
                    max_risk_score = receipt_stats['Risk Score'].max()
                    most_risky_receipt = receipt_stats[receipt_stats['Risk Score'] == max_risk_score][['Receipt#', 'Risk Score']]

                    # Display receipt risk scores
                    st.success("Risk Scores for Top 10 Receipts (Day-wise and Overall):")
                    st.dataframe(receipt_stats[['Receipt#', 'Risk Score']].sort_values(by='Risk Score', ascending=False, ignore_index=True))

                    # Display the most risky receipt
                    most_risky_receipt_numbers = most_risky_receipt['Receipt#'][:10].tolist()
                    st.markdown(
                        f"**Most Risky Receipt Number(s)**:  \n"
                        f"• **Receipt Numbers**: {', '.join(map(str, most_risky_receipt_numbers))}  \n"
                        f"• **Risk Score**: {max_risk_score:.2f}"
                    )

            else:
                st.error("The file does not contain all the required columns.")
        except Exception as e:
            st.error(f"An error occurred while processing the file: {e}")

if __name__ == "__main__":
    main()

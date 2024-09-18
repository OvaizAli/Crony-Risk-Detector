import streamlit as st
import pandas as pd

# Function to calculate means
def calculate_overall_means(df):
    return {
        'overall_void_count_mean': df['Void Count'].mean(),
        'overall_void_amount_mean': df['Void Amount'].mean(),
        'overall_return_count_mean': df['Return Count'].mean(),
        'overall_return_amount_mean': df['Return Amount'].mean(),
        'overall_total_amount_mean': df['Total Amount'].mean(),
        'overall_total_items_mean': df['Total Items'].mean(),
    }

# Function to create comparison columns
def create_comparison_columns(df, means, day_wise_means=None):
    if day_wise_means is not None:
        df = pd.merge(df, day_wise_means, on='Day', how='left')
        df['Exceeds Day Mean Void Count'] = (df['Void Count'] > df['mean_void_count']).astype(int)
        df['Exceeds Day Mean Void Amount'] = (df['Void Amount'] > df['mean_void_amount']).astype(int)
        df['Exceeds Day Mean Return Count'] = (df['Return Count'] > df['mean_return_count']).astype(int)
        df['Exceeds Day Mean Return Amount'] = (df['Return Amount'] > df['mean_return_amount']).astype(int)
        df['Below Day Mean Total Amount'] = (df['Total Amount'] < df['mean_total_amount']).astype(int)
        df['Below Day Mean Total Items'] = (df['Total Items'] < df['mean_total_items']).astype(int)

    df['Exceeds Overall Mean Void Count'] = (df['Void Count'] > means['overall_void_count_mean']).astype(int)
    df['Exceeds Overall Mean Void Amount'] = (df['Void Amount'] > means['overall_void_amount_mean']).astype(int)
    df['Exceeds Overall Mean Return Count'] = (df['Return Count'] > means['overall_return_count_mean']).astype(int)
    df['Exceeds Overall Mean Return Amount'] = (df['Return Amount'] > means['overall_return_amount_mean']).astype(int)
    df['Below Overall Mean Total Amount'] = (df['Total Amount'] < means['overall_total_amount_mean']).astype(int)
    df['Below Overall Mean Total Items'] = (df['Total Items'] < means['overall_total_items_mean']).astype(int)
    return df

# Function to display overall means
def display_overall_means(means):
    overall_means_data = {
        'Metric': [
            'Overall Mean Void Count', 'Overall Mean Void Amount',
            'Overall Mean Return Count', 'Overall Mean Return Amount',
            'Overall Mean Total Amount', 'Overall Mean Total Items'
        ],
        'Value': [
            means['overall_void_count_mean'],
            f"${means['overall_void_amount_mean']:.2f}",
            means['overall_return_count_mean'],
            f"${means['overall_return_amount_mean']:.2f}",
            f"${means['overall_total_amount_mean']:.2f}",
            means['overall_total_items_mean']
        ]
    }
    overall_means_df = pd.DataFrame(overall_means_data)
    st.success("Overall Mean Calculations")
    st.dataframe(overall_means_df)

# Function to calculate risk scores
def calculate_risk_scores(df, group_by_column, metrics_columns):
    stats = df.groupby(group_by_column).agg(
        total_transactions=('Receipt#', 'count'),
        **{metric: (metric, 'sum') for metric in metrics_columns}
    ).reset_index()

    stats['Risk Score'] = stats[metrics_columns].sum(axis=1) / stats['total_transactions']
    return stats

# Function to display the most risky cashier in a descriptive sentence with detailed factors
def display_most_risky_cashier(cashier_risk_scores, day_wise=False):
    most_risky = cashier_risk_scores.sort_values(by='Risk Score', ascending=False).iloc[0]
    if day_wise:
        st.error(
            f"The most risky cashier is **{most_risky['Cashier Name']}**, with a calculated risk score of **{most_risky['Risk Score']:.2f}**. "
            f"This score is based on multiple factors such as the cashier exceeding day-wise averages for void counts, void amounts, return counts, and return amounts. "
            f"It also includes factors where the cashier performed below day-wise averages for total transaction amounts and total items sold. "
            f"Additionally, the cashier's performance was compared to overall averages, considering void counts, void amounts, return counts, return amounts, "
            f"and total transaction amounts and items. In total, **{most_risky['Cashier Name']}** handled **{most_risky['total_transactions']}** transactions."
        )
    else:
        st.error(
            f"The most risky cashier is **{most_risky['Cashier Name']}**, with a calculated risk score of **{most_risky['Risk Score']:.2f}**. "
            f"This score is based on the cashier exceeding overall averages for void counts, void amounts, return counts, and return amounts. "
            f"Additionally, it includes factors where the cashier performed below overall averages for total transaction amounts and total items sold. "
            f"**{most_risky['Cashier Name']}** handled **{most_risky['total_transactions']}** transactions in total."
        )


# Function to display the most risky receipt in a descriptive sentence with detailed factors
def display_most_risky_receipt(receipt_risk_scores, day_wise=False):
    max_risk_score = receipt_risk_scores['Risk Score'].max()
    most_risky_receipts = receipt_risk_scores[receipt_risk_scores['Risk Score'] == max_risk_score]
    receipt_numbers = ', '.join(map(str, most_risky_receipts['Receipt#'].tolist()))
    
    if day_wise:
        st.error(
            f"The receipt(s) with the highest risk score of **{max_risk_score:.2f}** is/are **Receipt Number(s): {receipt_numbers}**. "
            f"This score is based on exceeding day-wise averages for void counts, void amounts, return counts, and return amounts. "
            f"Additionally, the risk score considers receipts where the total transaction amount and total items were below day-wise averages. "
            f"Furthermore, these receipts also exceeded or fell below overall averages for void counts, return counts, void amounts, "
            f"return amounts, total amounts, and total items, adding to their risk."
        )
    else:
        st.error(
            f"The receipt(s) with the highest risk score of **{max_risk_score:.2f}** is/are **Receipt Number(s): {receipt_numbers}**. "
            f"This score is based on exceeding overall averages for void counts, void amounts, return counts, and return amounts. "
            f"The score also considers receipts where the total transaction amount and total items were below overall averages, which contributed to the risk."
        )

# Define the Streamlit app
def main():
    st.title('Crony Risk Detector')

    uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xls", "xlsx"])

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            required_columns = [
                'Receipt#', 'Total Amount', 'Total Items', 'Date', 
                'Void Count', 'Void Amount', 'Return Count', 
                'Return Amount', 'Cashier Name', 'Register ID'
            ]

            if all(col in df.columns for col in required_columns):
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

                if df['Date'].isnull().any():
                    st.warning("Date timestamps could not be parsed, so day-wise analysis will be skipped.")
                    df.drop(columns='Date', inplace=True)

                    overall_means = calculate_overall_means(df)
                    df = create_comparison_columns(df, overall_means)

                    st.dataframe(df)
                    display_overall_means(overall_means)

                    # Cashier risk scores (Overall)
                    cashier_risk_scores = calculate_risk_scores(df, 'Cashier Name', [
                        'Exceeds Overall Mean Void Count', 'Exceeds Overall Mean Void Amount',
                        'Exceeds Overall Mean Return Count', 'Exceeds Overall Mean Return Amount',
                        'Below Overall Mean Total Amount', 'Below Overall Mean Total Items'
                    ])
                    st.success("Risk Scores for Cashiers (Overall):")
                    st.dataframe(cashier_risk_scores[['Cashier Name', 'total_transactions', 'Risk Score']])
                    display_most_risky_cashier(cashier_risk_scores)

                    # Receipt risk scores (Overall)
                    receipt_risk_scores = calculate_risk_scores(df, 'Receipt#', [
                        'Exceeds Overall Mean Void Count', 'Exceeds Overall Mean Void Amount',
                        'Exceeds Overall Mean Return Count', 'Exceeds Overall Mean Return Amount',
                        'Below Overall Mean Total Amount', 'Below Overall Mean Total Items'
                    ])
                    st.success("Risk Scores for Receipts (Overall):")
                    st.dataframe(receipt_risk_scores[['Receipt#', 'Risk Score']].sort_values(by='Risk Score', ascending=False))

                    display_most_risky_receipt(receipt_risk_scores)

                else:
                    st.success("Risk Analysis for the Uploaded - Both day-wise and overall analysis.")
                    df['Day'] = df['Date'].dt.day_name()

                    overall_means = calculate_overall_means(df)
                    day_wise_means = df.groupby('Day').agg(
                        mean_void_count=('Void Count', 'mean'),
                        mean_void_amount=('Void Amount', 'mean'),
                        mean_return_count=('Return Count', 'mean'),
                        mean_return_amount=('Return Amount', 'mean'),
                        mean_total_amount=('Total Amount', 'mean'),
                        mean_total_items=('Total Items', 'mean')
                    ).reset_index()

                    df = create_comparison_columns(df, overall_means, day_wise_means)

                    st.dataframe(df)
                    display_overall_means(overall_means)
                    st.success("Day-Wise Mean Calculations")
                    st.dataframe(day_wise_means)

                    # Cashier risk scores (Day-wise and Overall)
                    cashier_risk_scores = calculate_risk_scores(df, 'Cashier Name', [
                        'Exceeds Day Mean Void Count', 'Exceeds Day Mean Void Amount',
                        'Exceeds Day Mean Return Count', 'Exceeds Day Mean Return Amount',
                        'Below Day Mean Total Amount', 'Below Day Mean Total Items',
                        'Exceeds Overall Mean Void Count', 'Exceeds Overall Mean Void Amount',
                        'Exceeds Overall Mean Return Count', 'Exceeds Overall Mean Return Amount',
                        'Below Overall Mean Total Amount', 'Below Overall Mean Total Items'
                    ])
                    st.success("Risk Scores for Cashiers (Day-wise and Overall):")
                    st.dataframe(cashier_risk_scores[['Cashier Name', 'total_transactions', 'Risk Score']])
                    display_most_risky_cashier(cashier_risk_scores, day_wise=True)

                    # Receipt risk scores (Day-wise and Overall)
                    receipt_risk_scores = calculate_risk_scores(df, 'Receipt#', [
                        'Exceeds Day Mean Void Count', 'Exceeds Day Mean Void Amount',
                        'Exceeds Day Mean Return Count', 'Exceeds Day Mean Return Amount',
                        'Below Day Mean Total Amount', 'Below Day Mean Total Items',
                        'Exceeds Overall Mean Void Count', 'Exceeds Overall Mean Void Amount',
                        'Exceeds Overall Mean Return Count', 'Exceeds Overall Mean Return Amount',
                        'Below Overall Mean Total Amount', 'Below Overall Mean Total Items'
                    ])
                    st.success("Risk Scores for Receipts (Day-wise and Overall):")
                    st.dataframe(receipt_risk_scores[['Receipt#', 'Risk Score']].sort_values(by='Risk Score', ascending=False))

                    display_most_risky_receipt(receipt_risk_scores, day_wise=True)

            else:
                st.error("The file does not contain all the required columns.")
        except Exception as e:
            st.error(f"An error occurred while processing the file: {e}")

if __name__ == "__main__":
    main()

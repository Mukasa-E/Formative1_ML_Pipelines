import pandas as pd
import os

def preprocess(input_path, output_path):
    df = pd.read_csv(input_path)

    # Fix column names
    df.columns = df.columns.str.strip()

    # Convert date column
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])

    # Sort
    df = df.sort_values('date')

    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)

    print("✅ Data cleaned and saved.")

if __name__ == "__main__":
    preprocess(
        "data/raw/stock_data.csv",
        "data/processed/cleaned_data.csv"
    )
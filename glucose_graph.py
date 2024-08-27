import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline
from tkinter import Tk, filedialog
import os

def read_csv(file_path):
    try:
        df = pd.read_csv(file_path, skiprows=1, parse_dates=['Gerätezeitstempel'], dayfirst=True)
        return df
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None

def preprocess_data(df):
    # Combine glucose columns
    df['Blood Glucose (mg/dL)'] = df['Glukosewert-Verlauf mg/dL'].fillna(df['Glukose-Scan mg/dL'])
    
    # Handle missing values
    df.dropna(subset=['Blood Glucose (mg/dL)'], inplace=True)
    
    # Convert to numeric
    df['Blood Glucose (mg/dL)'] = pd.to_numeric(df['Blood Glucose (mg/dL)'], errors='coerce')
    df.dropna(subset=['Blood Glucose (mg/dL)'], inplace=True)
    
    return df

def remove_outliers(df):
    Q1 = df['Blood Glucose (mg/dL)'].quantile(0.25)
    Q3 = df['Blood Glucose (mg/dL)'].quantile(0.75)
    IQR = Q3 - Q1
    df = df[(df['Blood Glucose (mg/dL)'] >= (Q1 - 1.5 * IQR)) & (df['Blood Glucose (mg/dL)'] <= (Q3 + 1.5 * IQR))]
    return df

def calculate_daily_averages(df):
    df.set_index('Gerätezeitstempel', inplace=True)
    daily_avg = df['Blood Glucose (mg/dL)'].resample('D').mean()
    return daily_avg

def calculate_weekly_moving_average(daily_avg):
    weekly_moving_avg = daily_avg.rolling(window=7).mean()
    return weekly_moving_avg

def calculate_monthly_trend(daily_avg):
    # Calculate monthly average
    monthly_avg = daily_avg.resample('M').mean()
    
    # Drop NaN values
    monthly_avg.dropna(inplace=True)
    
    # Check if there's enough data for interpolation
    if len(monthly_avg) < 2:
        print("Not enough data to calculate a monthly trend.")
        return None, None

    # Prepare x and y for cubic spline interpolation
    x = np.arange(len(monthly_avg))
    cs = CubicSpline(x, monthly_avg)
    x_new = np.linspace(x.min(), x.max(), 500)
    y_new = cs(x_new)
    
    return x_new, y_new

def plot_data(daily_avg, weekly_moving_avg, x_new, y_new):
    plt.figure(figsize=(12, 8))
    
    plt.plot(daily_avg.index, daily_avg, label='Daily Average Blood Glucose', color='blue', linestyle='-', linewidth=1)
    plt.plot(daily_avg.index, weekly_moving_avg, label='Weekly Moving Average', color='orange', linestyle='-', linewidth=2)
    plt.plot(pd.date_range(start=daily_avg.index.min(), end=daily_avg.index.max(), periods=len(x_new)), y_new, label='Monthly Trend', color='red', linestyle='--', linewidth=2)
    
    plt.xlabel('Date')
    plt.ylabel('Blood Glucose (mg/dL)')
    plt.title('Blood Glucose Levels Over Time')
    plt.legend()
    plt.grid(True)
    plt.show()

def main():
    # Create Tkinter root window and hide it
    root = Tk()
    root.withdraw()
    
    # Ask the user to select a CSV file
    file_path = filedialog.askopenfilename(title="Select Blood Glucose CSV File", filetypes=[("CSV files", "*.csv")])
    
    if not file_path or not os.path.isfile(file_path):
        print("No valid file selected. Exiting.")
        return
    
    df = read_csv(file_path)
    if df is None:
        return
    
    df = preprocess_data(df)
    df = remove_outliers(df)
    
    daily_avg = calculate_daily_averages(df)
    weekly_moving_avg = calculate_weekly_moving_average(daily_avg)
    x_new, y_new = calculate_monthly_trend(daily_avg)
    
    plot_data(daily_avg, weekly_moving_avg, x_new, y_new)

if __name__ == "__main__":
    main()

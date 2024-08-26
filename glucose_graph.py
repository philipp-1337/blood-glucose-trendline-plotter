import matplotlib
matplotlib.use('TkAgg')  # Set the backend before importing pyplot
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tkinter import Tk, filedialog, simpledialog
from scipy.interpolate import CubicSpline

# Hide the toolbar
plt.rcParams['toolbar'] = 'None'

# Function to calculate daily average
def calculate_daily_average(data):
    try:
        numeric_data = pd.to_numeric(data, errors='coerce')
        return numeric_data.resample('D').mean()
    except:
        return pd.Series(index=data.index)  # Return NaN series if conversion fails

# Function to calculate weekly moving average
def calculate_weekly_moving_average(data):
    try:
        return data.rolling(window=7, min_periods=1).mean()
    except:
        return pd.Series(index=data.index)  # Return NaN series if calculation fails

# Function to calculate monthly trendline
def calculate_monthly_trendline(data, start_date, end_date):
    try:
        extended_data = data.reindex(pd.date_range(start=start_date, end=end_date, freq='D')).interpolate(method='linear')
        return extended_data.resample('ME').mean()
    except:
        return pd.Series(index=extended_data.index)  # Return NaN series if calculation fails

# Function to remove outliers using IQR method
def remove_outliers_iqr(data):
    try:
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        return data[(data >= lower_bound) & (data <= upper_bound)]
    except:
        return data  # Return original data if calculation fails

# Create a Tkinter window
root = Tk()
root.withdraw()  # Hide the root window

# Ask the user to select a file
file_path = filedialog.askopenfilename(title="Select CSV file", filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))

# Ask the user to select the CSV type
csv_type = simpledialog.askstring("Input", "Enter CSV type (Libre or Health):")

if csv_type.lower() == 'libre':
    # Read CSV file with specifying column data types and low_memory=False
    df = pd.read_csv(file_path, skiprows=1, parse_dates=['Gerätezeitstempel'], dtype={'Glukosewert-Verlauf mg/dL': 'object', 'Glukose-Scan mg/dL': 'object'}, low_memory=False)
    # Set index to datetime column
    df.set_index('Gerätezeitstempel', inplace=True)
    df.index = pd.to_datetime(df.index, format='%d-%m-%Y %H:%M')  # Adjust date format
    # Combine "Glukosewert-Verlauf mg/dL" and "Glukose-Scan mg/dL" into a single column
    df['Blood Glucose (mg/dL)'] = df['Glukosewert-Verlauf mg/dL'].combine_first(df['Glukose-Scan mg/dL'])
    # Drop original columns
    df.drop(columns=['Glukosewert-Verlauf mg/dL', 'Glukose-Scan mg/dL'], inplace=True)
elif csv_type.lower() == 'health':
    # Read CSV file with specifying column data types and low_memory=False
    df = pd.read_csv(file_path, skiprows=1, parse_dates=['endDate'], dtype={'value': 'object'}, low_memory=False)
    # Set index to datetime column
    df.set_index('endDate', inplace=True)
    df.index = pd.to_datetime(df.index, format='%d-%m-%Y %H:%M')  # Adjust date format
    # Use "value" column as blood glucose
    df['Blood Glucose (mg/dL)'] = df['value']
else:
    print("Invalid CSV type entered.")
    exit()

# Convert "Blood Glucose (mg/dL)" column to numeric
df['Blood Glucose (mg/dL)'] = pd.to_numeric(df['Blood Glucose (mg/dL)'], errors='coerce')

# Sort index
df.sort_index(inplace=True)

# Calculate daily average for the combined glucose data
daily_avg = df['Blood Glucose (mg/dL)'].resample('D').mean()

# Remove outliers from daily average using IQR method
daily_avg_cleaned = remove_outliers_iqr(daily_avg)

# Define start and end date for extended range
start_date = daily_avg_cleaned.index.min()
end_date = daily_avg_cleaned.index.max()

# Calculate weekly moving average based on cleaned daily averages
weekly_moving_avg = calculate_weekly_moving_average(daily_avg_cleaned)

# Fit a cubic spline to the weekly moving average
spline_weekly = CubicSpline(weekly_moving_avg.index.astype(np.int64) // 10**9, weekly_moving_avg.values)

# Generate more points for a smoother weekly curve
smoothed_index_weekly = pd.date_range(start=start_date, end=end_date, freq='D')
smoothed_weekly_curve = spline_weekly(smoothed_index_weekly.astype(np.int64) // 10**9)

# Calculate monthly trendline over the same extended date range as weekly
monthly_avg = calculate_monthly_trendline(daily_avg_cleaned, start_date, end_date)

# Fit a cubic spline to the monthly trendline
spline_monthly = CubicSpline(monthly_avg.index.astype(np.int64) // 10**9, monthly_avg.values)

# Generate more points for a smoother monthly curve
smoothed_index_monthly = pd.date_range(start=start_date, end=end_date, freq='D')
smoothed_monthly_curve = spline_monthly(smoothed_index_monthly.astype(np.int64) // 10**9)

# Plot
plt.figure(figsize=(10, 6))
plt.plot(smoothed_index_weekly, smoothed_weekly_curve, label='Weekly Trendline', color='green')
plt.plot(smoothed_index_monthly, smoothed_monthly_curve, label='Monthly Trendline', linestyle='--', color='blue')
plt.xlabel('Date')
plt.ylabel('Blood Glucose (mg/dL)')
plt.title('Smoothed Trendlines of Blood Glucose')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show(block=True)  # Show the plot and block execution

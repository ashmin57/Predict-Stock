import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from statsmodels.tsa.arima.model import ARIMA

def arima_model(company):
    # Read the CSV file
    df = pd.read_csv(company)

    # Convert the Date column to a datetime object
    df['Date'] = pd.to_datetime(df['Date'])

    # Sort the dataframe by date
    df = df.sort_values('Date')

    # Convert '--' to 0 in the 'Percent Change' column
    df['Percent Change'] = df['Percent Change'].replace('--', 0)

    # Convert columns to float
    df['Open'] = df['Open'].astype(float)
    df['High'] = df['High'].astype(float)
    df['Low'] = df['Low'].astype(float)
    df['Close'] = df['Close'].astype(float)
    df['Percent Change'] = df['Percent Change'].astype(float)

    # Extract the 'Close' column for prediction
    data = df['Close'].values

    # Scale the data using Min-Max Scaler
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data.reshape(-1, 1))

    # Define the training and testing data sizes
    train_size = int(len(scaled_data) * 0.8)
    test_size = len(scaled_data) - train_size

    # Split the data into training and testing sets
    train_data = scaled_data[:train_size]
    test_data = scaled_data[train_size:]

    # Train the ARIMA model
    model = ARIMA(train_data, order=(3, 1, 0))  # Modify the order as per your requirements
    model_fit = model.fit()

    # Forecast future values
    forecast = model_fit.forecast(steps=7)  # Change the number of steps as per your requirements
    predicted_close_prices = forecast[0]

    # Inverse scale the predicted values
    predicted_close_prices = scaler.inverse_transform(predicted_close_prices.reshape(-1, 1))

    last_date = df['Date'].iloc[-1]
    forecast_dates = pd.date_range(start=last_date + pd.DateOffset(days=1), periods=7, freq='D')
    df_predictions = pd.DataFrame({'close_price': predicted_close_prices.flatten(), 'date': forecast_dates})

    print(df_predictions)
    return df_predictions


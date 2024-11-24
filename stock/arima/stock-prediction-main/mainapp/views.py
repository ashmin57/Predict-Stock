from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.conf import settings
import subprocess
import os
import time
import statistics
import csv
import pandas as pd
from django.http import JsonResponse
from .forms import CSVUploadForm
import plotly.graph_objs as go
from plotly.offline import plot
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from django.utils.dateparse import parse_date
from .models import News, Prediction  

def auto_download(request):
    if request.method == 'POST':
        company = request.POST.get('company')

        brave_path = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"  # Update this path if different
        chrome_driver_path = 'D:\\stock\\arima\\chromedriver\\chromedriver.exe'

        chrome_options = Options()
        chrome_options.binary_location = brave_path
        chrome_options.add_argument("--headless")  # Update if you want to use headless browser

        service = Service(chrome_driver_path)
        driver = None

        try:
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.get('https://nepsealpha.com/nepse-data')

            wait = WebDriverWait(driver, 10)

            # Locate and interact with the elements
            select_click = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#vue_app_content > div.page.page_margin_top > div > div > div > form > div > div > div:nth-child(4) > span > span.selection > span')))
            select_click.click()

            start_date = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#vue_app_content > div.page.page_margin_top > div > div > div > form > div > div > div:nth-child(2) > input')))
            start_date.send_keys("07/01/2013")

            select_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > span > span > span.select2-search.select2-search--dropdown > input')))
            select_input.send_keys(company)
            select_input.send_keys(Keys.ENTER)

            filter_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#vue_app_content > div.page.page_margin_top > div > div > div > form > div > div > div:nth-child(5) > button')))
            filter_button.click()

            time.sleep(3)  # Adjust as needed for file download to complete

            csv_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#result-table_wrapper > div.dt-buttons > button.dt-button.buttons-csv.buttons-html5.btn.btn-outline-secondary.btn-sm')))
            csv_button.click()

            # Allow time for file download to complete
            time.sleep(20)  # Adjust as needed for file download to complete

        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            if driver:
                driver.quit()

        # Check for downloaded files and open download folder
        download_folder = os.path.expanduser("~\\Downloads\\nepse")
        downloaded_files = os.listdir(download_folder)

        if downloaded_files:
            print(f"Downloaded files: {downloaded_files}")
        else:
            print("No files were downloaded.")

        # Open download folder if file(s) found
        subprocess.Popen(f'explorer "{download_folder}"')

        return render(request, 'data.html')

def predict(request):
    predictions = []  # Initialize predictions to avoid UnboundLocalError
    
    if request.method == 'POST' and request.FILES.get('csv_file'):
        model = request.POST.get('model')
        csv_file = request.FILES['csv_file']

        # Extract the symbol from the CSV file
        file_data = csv_file.read().decode('utf-8').splitlines()
        csv_reader = csv.DictReader(file_data)
        symbol = next(csv_reader).get('Symbol')  # Get the symbol from the first row

        if not symbol:
            return JsonResponse({'error': 'Symbol not found in CSV file'}, status=400)

        # Reload the CSV data for prediction
        csv_file.seek(0)  # Reset the file pointer after reading the symbol

        # Perform prediction based on the selected model
        if model == 'LSTM':
            from .lstm import lstm_model
            result = lstm_model(csv_file)
        elif model == 'BLSTM':
            from .bilstm import bilstm_model
            result = bilstm_model(csv_file)
        elif model == 'GRU':
            from .gru import gru_model
            result = gru_model(csv_file)
        else:
            return JsonResponse({'error': 'Invalid model selected'}, status=400)

        # Convert the result DataFrame to a list of dictionaries
        result_dict = result.to_dict(orient='records')

        # Save or update each prediction in the database
        for row in result_dict:
            date = row.get('date')
            if isinstance(date, pd.Timestamp):
                date = date.date()  # Convert Timestamp to date

            close_price = row.get('close_price')

            if date and close_price is not None:
                # Try to find an existing prediction
                prediction = Prediction.objects.filter(symbol=symbol, date=date).first()
                
                if prediction:
                    # If it exists, update the close price
                    prediction.close_price = close_price
                    prediction.save()
                else:
                    # If it doesn't exist, create a new prediction
                    Prediction.objects.create(symbol=symbol, date=date, close_price=close_price)

    return render(request, 'predict.html')

def results_view(request, symbol):
    predictions = Prediction.objects.filter(symbol=symbol)
    context = {
        'data': predictions,
        'symbol': symbol
    }
    return render(request, 'results.html', context)


def select_symbol(request):
    # Fetch unique stock symbols from the Prediction model (or adjust to your actual model)
    symbols = Prediction.objects.values_list('symbol', flat=True).distinct()
    selected_symbol = None
    data = None

    if request.method == 'POST':
        selected_symbol = request.POST.get('symbol')
        if selected_symbol:
            # Fetch prediction data for the selected symbol (case-insensitive)
            data = Prediction.objects.filter(symbol__iexact=selected_symbol)

    return render(request, 'select_symbol.html', {
        'symbols': symbols,
        'selected_symbol': selected_symbol,
        'data': data,
    })

def data_download(request):
    return render(request, 'data.html')


def visualize_csv_form(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            reader = csv.reader(csv_file.read().decode('utf-8').splitlines())
            header = next(reader)  # Skip the header row
            data = list(reader)

            # Extract column data
            dates = [row[1] for row in data]  # Assuming the date column is at index 1
            close_prices = [float(row[5]) for row in data]  # Assuming the close price column is at index 5

            # Calculate statistical data
            minimum = min(close_prices)
            maximum = max(close_prices)
            average = statistics.mean(close_prices)
            variance = statistics.variance(close_prices)
            median = statistics.median(close_prices)

            chart_data = go.Scatter(x=dates, y=close_prices, mode='lines', name='Close Prices')
            layout = go.Layout(title='Close Prices Over Time', xaxis=dict(title='Date'), yaxis=dict(title='Close Price'))
            fig = go.Figure(data=[chart_data], layout=layout)
            plot_div = plot(fig, output_type='div')

            return render(request, 'visualization.html', {'form': form, 'plot_div': plot_div, 'minimum': minimum, 'maximum': maximum, 'average': average, 'variance': variance, 'median': median})
    else:
        form = CSVUploadForm()

    return render(request, 'visualization.html', {'form': form})


def get_driver():
    brave_path = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"  
    chrome_options = Options()
    chrome_options.binary_location = brave_path
    chrome_options.add_argument("--headless")
    service = Service('D:\\stockbeta\\stock\\arima\\chromedriver\\chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def index(request):
    return render(request, 'index.html')

def logout_view(request):
    logout(request)
    return redirect('index')

def news(request):
    import time
    ts = time.time()
    try:
        db_exp_time = News.objects.values('expiry').latest('id')
        if ts < db_exp_time['expiry']:
            db_data = News.objects.all().order_by('id').values()
            send_news = {'news': db_data}
            return render(request, 'news.html', send_news)
        else:
            driver = get_driver()

            try:
                driver.get('https://merolagani.com/NewsList.aspx/')
                WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#ctl00_ContentPlaceHolder1_divData > .btn-block"))).click()
                time.sleep(2)
            except Exception as e:
                print(f"Error: {e}")
                data = {'news': None}
                driver.quit()
                return render(request, 'news.html', data)

            img = driver.find_elements(By.CSS_SELECTOR, '.media-wrap > a > img')
            img_data = [i.get_attribute('src') for i in img]

            hrefs = driver.find_elements(By.CSS_SELECTOR, '.media-wrap > a')
            single_news_href_data = [i.get_attribute('href') for i in hrefs]

            news_link = driver.find_elements(By.CLASS_NAME, 'media-body')
            news_titledate_data = [i.text.replace("\n", "<br>") for i in news_link]

            news_data = [{'title': news_titledate_data[i], 'link': single_news_href_data[i], 'image': img_data[i]} for i in range(len(news_titledate_data))]

            driver.quit()

            if len(news_data) == 16:
                expiry_time = ts + 9000
                News.objects.all().delete()
                for i in news_data:
                    add_news = News(title=i['title'], image=i['image'], link=i['link'], expiry=expiry_time)
                    add_news.save()

                db_data = News.objects.all().order_by('id').values()
                data = {'news': db_data}
                return render(request, 'news.html', data)
            else:
                data = {'news': None}
                return render(request, 'news.html', data)
    except Exception as e:
        print(f"Error: {e}")
        db_exp_time = {'expiry': 100}

        if ts < db_exp_time['expiry']:
            db_data = News.objects.all().order_by('id').values()
            send_news = {'news': db_data}
            return render(request, 'news.html', send_news)
        else:
            driver = get_driver()

            try:
                driver.get('https://merolagani.com/NewsList.aspx/')
                WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#ctl00_ContentPlaceHolder1_divData > .btn-block"))).click()
                time.sleep(2)
            except Exception as e:
                print(f"Error: {e}")
                data = {'news': None}
                driver.quit()
                return render(request, 'news.html', data)

            img = driver.find_elements(By.CSS_SELECTOR, '.media-wrap > a > img')
            img_data = [i.get_attribute('src') for i in img]

            hrefs = driver.find_elements(By.CSS_SELECTOR, '.media-wrap > a')
            single_news_href_data = [i.get_attribute('href') for i in hrefs]

            news_link = driver.find_elements(By.CLASS_NAME, 'media-body')
            news_titledate_data = [i.text.replace("\n", "<br>") for i in news_link]

            news_data = [{'title': news_titledate_data[i], 'link': single_news_href_data[i], 'image': img_data[i]} for i in range(len(news_titledate_data))]

            driver.quit()

            if len(news_data) == 16:
                expiry_time = ts + 9000
                News.objects.all().delete()
                for i in news_data:
                    add_news = News(title=i['title'], image=i['image'], link=i['link'], expiry=expiry_time)
                    add_news.save()

                db_data = News.objects.all().order_by('id').values()
                data = {'news': db_data}
                return render(request, 'news.html', data)
            else:
                data = {'news': None}
                return render(request, 'news.html', data)


#admin
from django.contrib.auth.views import LoginView
from django.urls import path

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'  # Path to your login template

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
]
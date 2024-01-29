from flask import Flask, jsonify, request, render_template
from flask_socketio import SocketIO, emit
import requests
from bs4 import BeautifulSoup
import re
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
socketio = SocketIO(app)

def fetch_stock_data(stock_symbol):
    try:
        # Construct the URL with the provided symbol
        url = f"https://finance.yahoo.com/quote/{stock_symbol}"

        # Send a GET request to Yahoo Finance
        headers = {'Cache-Control': 'no-cache'}
        r = requests.get(url, headers=headers)
        r.raise_for_status()  # Raise an exception for 4xx or 5xx status codes

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(r.text, 'html.parser')

        # Initialize variables to store table data
        table1_data = {}
        table2_data = {}

        # Find all tbody elements on the page
        alldata = soup.find_all("tbody")

        # Extract data from the first tbody (if available)
        if alldata:
            table1 = alldata[0].find_all("tr")
            for row in table1:
                table1_td = row.find_all("td")
                if len(table1_td) >= 2:
                    table1_data[table1_td[0].text] = table1_td[1].text

        # Extract data from the second tbody (if available)
        if len(alldata) > 1:
            table2 = alldata[1].find_all("tr")
            for row in table2:
                table2_td = row.find_all("td")
                if len(table2_td) >= 2:
                    table2_data[table2_td[0].text] = table2_td[1].text

        # Extract time from the quote-market-notice div
        time_div = soup.find('div', {'id': 'quote-market-notice'})
        time = (time_div).text if time_div else None

        # Find the <fin-streamer> tag with the data-test="qsp-price" attribute
        # Extract the price value from the tag using regex
        fin_streamer = soup.find('fin-streamer', {'data-test': 'qsp-price'})
        price_match = re.search(r'value="([\d.]+)"', str(fin_streamer)) if fin_streamer else None
        price = price_match.group(1) if price_match else None

        # Combine the extracted data
        stock_data = {
            "symbol": stock_symbol,
            "price": price,
            "time": time,
            "table1": table1_data,
            "table2": table2_data,
        }

        return stock_data

    except Exception as e:
        raise e

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('get_stock_data')
def get_stock_data(symbol):
    try:
        while True:
            # Fetch fresh stock data
            stock_data = fetch_stock_data(symbol)

            # Emit the extracted data to the client
            emit('stock_data', stock_data)

            # Sleep for a while before fetching data again
            time.sleep(5)  # Adjust the interval as needed

    except Exception as e:
        error_message = {"error": str(e)}
        emit('stock_data_error', error_message)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app, debug=True)

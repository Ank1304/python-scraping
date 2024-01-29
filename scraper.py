from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/api/stock_data')
def get_stock_data():
    try:
        # Get the stock symbol from the query parameters
        stock_symbol = request.args.get('symbol', 'AMZN')

        # Construct the URL with the provided symbol
        url = f"https://finance.yahoo.com/quote/{stock_symbol}"

        # Send a GET request to Yahoo Finance
        r = requests.get(url).text

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(r, 'html.parser')

        # Find all tbody elements on the page
        alldata = soup.find_all("tbody")

         # Find the <fin-streamer> tag with the data-test="qsp-price" attribute
        fin_streamer = soup.find('fin-streamer', {'data-test': 'qsp-price'})

        # Extract the price value from the tag
        price = fin_streamer.text if fin_streamer else None

        # Combine the extracted data from both tables
        stock_data = {
            "symbol": stock_symbol,
            "price": price
        }


        # Initialize variables to store table data
        table1_data = {}
        table2_data = {}

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

        # Combine the extracted data from both tables
        stock_data = {
            "symbol": stock_symbol,
            "table1": table1_data,
            "table2": table2_data,
            "stock_data": stock_data
        }

        # Return the extracted data in JSON format
        return jsonify(stock_data), 200

    except Exception as e:
        error_message = {"error": str(e)}
        return jsonify(error_message), 500

if __name__ == '__main__':
    app.run(debug=True)

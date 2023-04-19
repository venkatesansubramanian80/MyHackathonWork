import requests
import json
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import date
import os

def financial_strength_retreival(symbol, influx_frendly_data, api_key, function, current_date):
    url = f"{os.environ.get('Fin_Stren_Provider')}?function={function}&symbol={symbol}&apikey={api_key}"

    response = requests.get(url)
    data = json.loads(response.text)

    eps = data["EPS"]
    pe_ratio = data["PERatio"]
    roe = data["ReturnOnEquityTTM"]
    div_yield = data["DividendYield"]

    function = os.environ.get('Fin_BalSheet_Function')
    url = f"{os.environ.get('Fin_BalSheet_Provider')}?function={function}&symbol={symbol}&apikey={api_key}"

    response = requests.get(url)
    data = json.loads(response.text)

    total_liabilities = float(data["annualReports"][0]["totalLiabilities"])
    total_equity = float(data["annualReports"][0]["totalShareholderEquity"])
    debt_to_equity = total_liabilities / total_equity

    financial_strength = [
        influx_frendly_data(
            os.environ.get('Fin_Stren_Table'),
            current_date,
            {
                "EPS": eps,
                "PERatio": pe_ratio,
                "ROE": roe,
                "Divident_Yield": div_yield,
                "Dept_To_Equity": debt_to_equity
            },
            {
                "symbol": symbol
            }
        )
    ]
    return financial_strength

def fundamental_analysis(symbol, current_date, influx_frendly_data):
    url = os.environ.get('Fundamental_News_Provider')
    querystring = {"category": symbol}
    headers = {
        "X-RapidAPI-Key": os.environ.get('Fundamental_News_Key'),
        "X-RapidAPI-Host": os.environ.get('Fundamental_News_Host')
    }

    response = requests.get(url, headers=headers, params=querystring)
    data = json.loads(response.text)

    news_list = [
        influx_frendly_data(
            os.environ.get('Fundamental_News_Table'),
            current_date,
            {
                "Title": news_item['title'],
                "Source": news_item['source']
            },
            {
                "symbol": symbol,
                "guid": news_item['guid']
            }
        ) for news_item in data
    ]
    return news_list

def technical_analysis(symbol, influx_frendly_data, api_key):
    function = os.environ.get('Technical_Analysis_Function')
    url = f"{os.environ.get('Technical_Analysis_Provider')}?function={function}&symbol={symbol}&outputsize=compact&apikey={api_key}"

    response = requests.get(url)
    data = json.loads(response.text)

    technical_data = [
        influx_frendly_data(
            {os.environ.get('Technical_Analysis_Table')},
            date,
            {
                "open": data["Time Series (Daily)"][date]['1. open'],
                "high": data["Time Series (Daily)"][date]['2. high'],
                "low": data["Time Series (Daily)"][date]['3. low'],
                "close": data["Time Series (Daily)"][date]['4. close'],
                "volume": data["Time Series (Daily)"][date]['5. volume']
            },
            {
                "symbol": symbol
            }
        ) for date in data["Time Series (Daily)"]
    ]

    technical_data = technical_data[:20]
    return technical_data

def insert_into_influx(full_list):
    token_val = os.environ.get('Influx_Token_Value')
    client = influxdb_client.InfluxDBClient(url=os.environ.get('Influx_DB_URL'), token=token_val,
                                            org=os.environ.get('Influx_Org_Name'), verify_ssl=False)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    batch_size = 1000
    for i in range(0, len(full_list), batch_size):
        batch_data = full_list[i:i + batch_size]
        write_api.write(bucket=os.environ.get('Influx_Bucket_Name'), record=batch_data)
    client.close()


def execute_stock(symbol):
    influx_frendly_data = lambda measurement_name, time_value, field_values, tag_values: {
        "measurement": measurement_name,
        "time": time_value,
        "fields": field_values,
        "tags": tag_values
    }
    api_key = os.environ.get('Api_Key')
    function = os.environ.get('Fin_Stren_Function')
    current_date = date.today().isoformat()
    financial_strength = financial_strength_retreival(symbol, influx_frendly_data, api_key, function, current_date)
    news_list = fundamental_analysis(symbol, current_date, influx_frendly_data)
    technical_data = technical_analysis(symbol, influx_frendly_data, api_key)
    full_list = sum([financial_strength, news_list, technical_data[:30]], [])
    insert_into_influx(full_list)


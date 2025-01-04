import websockets
import json
import pandas as pd
import requests
from common import trunc
from binance.client import Client
from endpoints import Endpoints

class DataParser:
    def __init__(self, client: Client):
        self.token = "BTC"
        self.data_rows = 5
        self.client = client
        self.data = None
        self.tokenPrice = None
        
    def set_token(self):
        token = input("Specify token for which you would like data: ")
        print(f"You have chosen token: {token}")
        self.token = token.upper()
    
    def get_data(self):
        return self.data

    async def get_live_product_data(self, token = None, id = 1, number_of_calls=float('inf'), endpoint: Endpoints = Endpoints.OPTIONWEBSOCKET.value):
        if token is None:
            token = self.token
        our_msg = json.dumps({'method': 'SUBSCRIBE', 'params': [token], 'id': id})
        call_count = number_of_calls
        endpoint += token
        async with websockets.connect(endpoint, open_timeout=30, close_timeout=30) as ws:
            await ws.send(our_msg)

            while call_count > 0:
                try:
                    # Receive message
                    message = await ws.recv()
                    self.data = json.loads(message)
                    # print(self.data)
                except Exception as e:
                    print(f"Error receiving data: {e}") 
                    continue
                try:
                # Process the data
                    if self.data['result'] == None:
                            print("No data recieved yet")
                            continue
                    call_count -= 1
                except:
                    try:
                        call_count -= 1
                    except Exception as e:
                        print(f"Error receiving data: {e}")

    
    

    async def get_current_coin_price(self):
        try:
            if len(self.token) <= 4: #Did not just do an ends with check so other coins can be checked such as BTCETH price
                token = self.token.upper() + "USDT"
            else:
                token = self.token
            url = Endpoints.TICKERPRICE.value+token
            request = requests.get(url)
            coinPriceData = json.loads(request.text)
            self.tokenPrice = trunc(float(coinPriceData['price']), 3)
            print (f"\nBINANCE Price for {token} = ${self.tokenPrice}")
        except Exception as e:
            print(e)
            print("Could not get coin price")
    
    def get_current_holdings_options(self):
        positions = self.client.options_account_info()
        print(positions)
        return positions
        
    def get_current_holdings_spot(self):
        positions = self.client.get_asset_balance()
        portfoliio = {}
        for position in positions:
            if float(position["free"]) != 0:
                symbol = position["asset"]
                quantity = position["free"]
                print(f"{symbol}: {quantity}")
                portfoliio[symbol] = quantity
        return portfoliio
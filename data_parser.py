import websocket
import json
import pandas as pd
import requests
import re
from common import trunc
from binance.client import Client

class DataParser:
    def __init__(self, client: Client):
        self.optionSocketEndpoint = 'wss://nbstream.binance.com/eoptions/ws'
        self.token = "BTC"
        self.data_rows = 15
        self.client = client
    
    def set_token(self):
        token = input("Specify token for which you would like data: ")
        print(f"You have chosen token: {token}")
        self.token = token.upper()

    def get_live_option_data(self, id = 1):
        try:
            if self.token[-1:-10] != "@markPrice":
                token = self.token.upper() + "@markPrice"

            our_msg = json.dumps({'method': 'SUBSCRIBE',
                                'params': [token], 'id': id})

            def on_open(ws):
                ws.send(our_msg)

            def on_message(ws, message):
                out = json.loads(message)
                df = pd.DataFrame(out)
                df = df.tail(self.data_rows)
                df.drop(columns=["e"])
                df.drop(columns=["E"])
                df_puts = df[df['s'].str.endswith('P')].reset_index(drop=True)
                df_calls = df[df['s'].str.endswith('C')].reset_index(drop=True)

                # Display the results
                print("Puts:\n", df_puts)
                print("\nCalls:\n", df_calls)


            ws = websocket.WebSocketApp(self.optionSocketEndpoint, on_message=on_message, on_open=on_open)

            ws.run_forever()
        except Exception as e:
            print(e)
            print("Could not get live option data")

    def get_current_coin_price(self):
        try:
            if len(self.token) == 3:
                token = self.token.upper() + "USDT"
            else:
                token = self.token
            request = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={token}')
            coinPriceData = json.loads(request.text)
            coinPrice = trunc(float(coinPriceData['price']), 3)
            print (f"\nBINANCE Price for {token} = ${coinPrice}")
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
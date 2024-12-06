import websockets
import json
import pandas as pd
import requests
import re
from common import trunc
from binance.client import Client
import asyncio

class DataParser:
    def __init__(self, client: Client):
        self.optionSocketEndpoint = 'wss://nbstream.binance.com/eoptions/ws'
        self.token = "BTC"
        self.data_rows = 5
        self.client = client
        self.data = pd.DataFrame()
    
    def set_token(self):
        token = input("Specify token for which you would like data: ")
        print(f"You have chosen token: {token}")
        self.token = token.upper()
    
    def get_data(self):
        return self.data

    async def get_live_option_data(self, token, number_of_calls=float('inf')):
        if not token.endswith("@markPrice"):
            token += "@markPrice"

        our_msg = json.dumps({'method': 'SUBSCRIBE', 'params': [token], 'id': 1})
        call_count = number_of_calls

        async with websockets.connect(self.optionSocketEndpoint) as ws:
            await ws.send(our_msg)

            while call_count > 0:
                try:
                    # Receive message
                    message = await ws.recv()
                    out = json.loads(message)

                    # Process the data
                    self.data = pd.DataFrame(out)
                    call_count -= 1

                except Exception as e:
                    print(f"Error receiving data: {e}")
                    continue
    
    async def display_option_data(self):
        """Displays the fetched option data in real time."""
        token = self.token
        if not token.endswith("@markPrice"):
            token += "@markPrice"

        # Start fetching data in the background
        task = asyncio.create_task(self.get_live_option_data(token))
        try:
            try:
                while True:  # Keep displaying the data as it arrives
                    await asyncio.sleep(1)  # Delay for a moment before checking for updates
                    if self.data is not None:
                        df = self.data.copy()
                        try:
                            df.drop(columns=["e", "E"], inplace=True)  # Drop 'e' and 'E' columns
    
                            df_puts = df[df['s'].str.endswith('P')].reset_index(drop=True)  # Filter puts
                            df_calls = df[df['s'].str.endswith('C')].reset_index(drop=True)  # Filter calls

                            # Display the results
                            print("Puts:\n", df_puts.tail(self.data_rows))
                            print("\nCalls:\n", df_calls.tail(self.data_rows))

                        except:
                            continue


            except asyncio.CancelledError:
                print("Data display cancelled.")
        except KeyboardInterrupt:
            task.cancel()



    def get_current_coin_price(self):
        try:
            if len(self.token) <= 4:
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
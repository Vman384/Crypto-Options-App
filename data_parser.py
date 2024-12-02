import websocket
import json
import pandas as pd


class DataParser:
    def __init__(self):
        self.optionSocketEndpoint = 'wss://nbstream.binance.com/eoptions/ws'
        self.token = "BTC@markPrice"
        self.data_rows = 15
    
    def set_token(self):
        token = input("Specify token for which you would like data: ")
        self.token = token

    def get_live_option_data(self, id = 1):

        our_msg = json.dumps({'method': 'SUBSCRIBE',
                            'params': [self.token], 'id': id})

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
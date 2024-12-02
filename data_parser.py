import websocket
import json
import pandas as pd


class DataParser:
    def __init__(self):
        self.optionSocketEndpoint = 'wss://nbstream.binance.com/eoptions/ws'
        self.token = "BTC@markPrice"
    
    def set_token(self, token):
        self.token = token

    def get_live_option_data(self, id = 1):

        our_msg = json.dumps({'method': 'SUBSCRIBE',
                            'params': [self.token], 'id': id})

        def on_open(ws):
            ws.send(our_msg)

        def on_message(ws, message):
            out = json.loads(message)
            df = pd.DataFrame(out)
            print(df)

        ws = websocket.WebSocketApp(self.optionSocketEndpoint, on_message=on_message, on_open=on_open)

        ws.run_forever()
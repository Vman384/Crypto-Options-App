import websocket
import json
import pandas as pd


class DataParser:
    def __init__(self, token = "BTC@markPrice"):
        self.optionEndpoint = 'wss://nbstream.binance.com/eoptions/ws'

    def get_option_data(self, id = 1):

        our_msg = json.dumps({'method': 'SUBSCRIBE',
                            'params': [self.token], 'id': id})

        def on_open(ws):
            ws.send(our_msg)

        def on_message(ws, message):
            out = json.loads(message)
            df = pd.DataFrame(out)
            print(df)

        ws = websocket.WebSocketApp(self.endpoint, on_message=on_message, on_open=on_open)

        ws.run_forever()
import websocket
import json
import pandas as pd


endpoint = 'wss://nbstream.binance.com/eoptions/ws'

our_msg = json.dumps({'method': 'SUBSCRIBE',
                      'params': ["BTC@markPrice"], 'id': 1})

def on_open(ws):
    ws.send(our_msg)

def on_message(ws, message):
     out = json.loads(message)
     df = pd.DataFrame(out)
     print(df)

ws = websocket.WebSocketApp(endpoint, on_message=on_message, on_open=on_open)

print(ws.run_forever())
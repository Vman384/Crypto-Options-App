from enum import Enum

class Endpoints(Enum):
    OPTIONWEBSOCKET = 'wss://nbstream.binance.com/eoptions/ws/'
    TICKERPRICE = "https://api.binance.com/api/v3/ticker/price?symbol="
    TOKENWEBSOCKET = "wss://fstream.binance.com/ws/"

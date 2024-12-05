from UI import UI
from data_parser import DataParser
from order_sender import OrderSender
from binance.client import Client
from options_calculator import OptionsCalculator



print("Welcome to the all inclusive option app")
# apiKey = input("Please enter your binance api key: ")
# apiSecret = input("Please enter your binance api secret: ")
client = Client(api_key="SqbANdfqkSGM2uN7zeXMZSekaCuxRbD6KWru1q7tyibhU04lFhahcR7FUhaJY0cN",api_secret="5cXBv9T5Qpy0UgeASbRXEhO2d22GpF7WhdJpx5mwYOev3lP2gMwnk3ERVKh4eryW")
# print(client.options_account_info())
dataParser = DataParser(client)
ui = UI(dataParser) 
optionsCalculator = OptionsCalculator(dataParser)
orderSender = OrderSender(client, optionsCalculator)
ui.add_menu_option("Live Option Data", dataParser.get_live_option_data)
ui.add_menu_option("Change Token", dataParser.set_token)
ui.add_menu_option("Get Coin Price", dataParser.get_current_coin_price)
ui.add_menu_option("Get Current Spot Holdings", dataParser.get_current_holdings_spot)
ui.add_menu_option("Sell Order", orderSender.sell_order)
ui.add_menu_option("Buy Order", orderSender.buy_order)
ui.add_menu_option("Balance Deltas (Not Tested)", orderSender.balance_deltas)
ui.render_menu()
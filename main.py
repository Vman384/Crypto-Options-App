from UI import UI
from data_parser import DataParser


print("Welcome to the all inclusive option app")
dataParser = DataParser()
ui = UI(dataParser) 
ui.add_menu_option("Live Option Data", dataParser.get_live_option_data)
ui.add_menu_option("Change Token", dataParser.set_token)
ui.add_menu_option("Get Coin Price", dataParser.get_current_coin_price)
ui.render_menu()
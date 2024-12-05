from binance.client import Client
from options_calculator import OptionsCalculator

class OrderSender:
    def __init__(self, client: Client, optionsCalculator: OptionsCalculator):
        self.optionsCalculator = optionsCalculator
        self.client = client

    def sell_order(self, symbol: str = None, quantity: float = None):
        if symbol is None:
            symbol = input("Enter Symbol: ")
        
        if quantity is None:
            try:
                quantity = float(input("Enter Quantity: "))
            except ValueError:
                print("Invalid quantity. Please enter a numeric value.")
                return

        # Proceed with order logic
        print(f"Placing a sell order for {quantity} of {symbol}")
        try:
            order = self.client.order_market_sell(
                symbol=symbol,
                quantity=quantity)
        except Exception as e:
            print("Order did not execute")
            print(e)
        return order
        

    def buy_order(self, symbol: str = None, quantity: float = None):
        if symbol is None:
            symbol = input("Enter Symbol: ")
        
        if quantity is None:
            try:
                quantity = float(input("Enter Quantity: "))
            except ValueError:
                print("Invalid quantity. Please enter a numeric value.")
                return

        # Proceed with order logic
        print(f"Placing a buy order for {quantity} of {symbol}")
        try:
            order = self.client.order_market_buy(
                symbol= symbol,
                quantity=quantity)
        except Exception as e:
            print("Order did not execute")
            print(e)
        return order
    
    def balance_deltas(self):
        deltaSheet = self.optionsCalculator.account_delta_calculator()
        for coin in deltaSheet.keys():
            if deltaSheet[coin] > 0:
                print(f"Sell {coin} to cover delta of {deltaSheet[coin]}")
                self.sell_order(coin, abs(deltaSheet[coin]))
            else:
                print(f"Buy {coin} to cover delta of {deltaSheet[coin]}")
                self.buy_order(coin, abs(deltaSheet[coin]))
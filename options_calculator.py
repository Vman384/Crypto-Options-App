import asyncio
import numpy as np
from scipy.stats import norm
from data_parser import DataParser
from concurrent.futures import ThreadPoolExecutor
import asyncio

class OptionsCalculator:
    def __init__(self, dataParser: DataParser) -> None:
        self.dataParser = dataParser

    def account_delta_calculator(self) -> dict[str, int]: 
        """
            Since I am in Australia I do not have access to trade binance options therefore can not verify if the this function works
        """
        options = self.dataParser.get_current_holdings_options()
        spot = self.dataParser.get_current_holdings_spot()
        totalDelta = {}    
        # Loop through the positions
        for option in options:
            delta = float(option["delta"])
            underlying = option["underlying"]
            totalDelta[underlying[0:2]] = delta
        for coin in spot.keys():
            try:
                totalDelta[coin] += spot[coin] 
            except KeyError:
                totalDelta[coin] = spot[coin]

        return totalDelta

    
    def mispriced_options(self) -> float:
        # Step 1: Fetch the initial options data synchronously
        asyncio.run(self.dataParser.get_live_product_data(self.dataParser.token + "@markPrice", 2, 2)) #could use binance client but since I am in Australia I dont have access
        symbolsDf = self.dataParser.get_data()['s']
        # tokenPrice = asyncio.run(self.dataParser.get_live_product_data(self.dataParser.token + "@aggTrade"))
        tokenPrice = self.dataParser.get_current_coin_price() #change to use a websocket 
        print(symbolsDf)

        # Step 2: Fetch additional data for each option
        async def fetch_option_data(symbol):
            return await self.dataParser.get_live_product_data(symbol + "@ticker")

        async def fetch_all_options(symbols):
            tasks = [fetch_option_data(symbol) for symbol in symbols]
            return await asyncio.gather(*tasks)

        optionData = asyncio.run(fetch_all_options(symbolsDf))

        # Step 3: Process each option in a separate thread
        def process_option(optionData):
            try:
                print(optionData)
                symbol = optionData['s'].split("-")
                strikePrice = symbol[2]
                callOrPut = symbol[3]
                self.black_scholes(tokenPrice, strikePrice, optionData['t'], optionData['r'], optionData['v'], callOrPut)
            except Exception as e:
                print(f"Error processing option {optionData}: {e}")

        with ThreadPoolExecutor() as executor:
            executor.map(process_option, optionData.tail(10)) # have got the value set to 10 as otherwise I get too many requests and get timed out

    def black_scholes(self, S, K, T, r, vega, option_type='call') -> float:
        """
        Calculate the Black-Scholes option price.

        Parameters:
        S : float
            Current stock price
        K : float
            Strike price
        T : float
            Time to maturity (in years)
        r : float
            Risk-free interest rate (annualized)
        vega : float
            Volatility of the underlying stock (annualized)
        option_type : str
            Type of option: 'C' or 'P'

        Returns:
        float
            Option price
        """
        d1 = (np.log(S / K) + (r + 0.5 * vega()**2) * T) / (vega() * np.sqrt(T))
        d2 = d1 - vega() * np.sqrt(T)
        
        if option_type == 'C':
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        elif option_type == 'P':
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        else:
            raise ValueError("option_type must be 'C' or 'P'")
        
        return price


     
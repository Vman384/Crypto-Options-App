import numpy as np
import pandas as pd
from scipy.stats import norm
from data_parser import DataParser
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import asyncio
from threading import Thread, Semaphore
from queue import Queue
from multiprocessing import Pool, cpu_count
import time
from endpoints import Endpoints


class OptionsCalculator:
    def __init__(self, dataParser: DataParser) -> None:
        self.dataParser = dataParser
        self.tokenPrice = None

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
    
    def black_scholes(self, S: float, K: float, T: float, r: float, vega: float, option_type='call') -> float:
        """
        Calculate the Black-Scholes option price.

        Parameters:
        S : float
            Current stock price
        K : float
            Strike price
        T : float
            Time to maturity (in days)
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
        T = abs(T) / 365 #Binance gives the time in days and negative
        d1 = (np.log(S / K) + (r + 0.5 * vega**2) * T) / (vega * np.sqrt(T))
        d2 = d1 - vega * np.sqrt(T)
        
        if option_type == 'C':
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        elif option_type == 'P':
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        else:
            raise ValueError("option_type must be 'C' or 'P'")
        
        return price
    
    

    def fetch_data_background(self, symbol: str, dataParser: DataParser, endpoint: Endpoints):
        """
        Thread wrapper to continuously fetch live data
        Need this because threads and async gets funky, would need asyncio.new_event_loop otherwise 
        """
        asyncio.run(dataParser.get_live_product_data(symbol, endpoint=endpoint))

    def process_option(self, token_price, option_data):
        """
        Process option data using Black-Scholes calculation.
        """
        try:
            symbol_parts = option_data['s'].split("-")
            strike_price = symbol_parts[2]
            call_or_put = symbol_parts[3]
            predicted_price = self.black_scholes(
                float(token_price),
                float(strike_price),
                float(option_data['t']),  # Time to expiry
                float(option_data['r']),  # Risk-free rate
                float(option_data['v']),  # Volatility
                call_or_put
            )
            print(f"Processed Price: {predicted_price}")
            return predicted_price
        except Exception as e:
            print(f"Error processing option {option_data}: {e}")
            return None

    async def mispriced_options(self):
        """
        Main function to fetch live token price, fetch options data, and process it.
        """
        # Step 1: Validate token
        if len(self.dataParser.token) <= 4:
            token = self.dataParser.token.lower() + "usdt@aggTrade"
        else:
            print("Invalid token, can only price against usdt")
            return
        # Step 2: Create thread to fetch live token price
        tokenThread = Thread(target=self.fetch_data_background, args=(token, self.dataParser, Endpoints.TOKENWEBSOCKET.value,), daemon=True)
        # Step 3: Fetch initial options data and prepare symbols
        await self.dataParser.get_live_product_data(self.dataParser.token + "@markPrice", 2, 2, Endpoints.OPTIONWEBSOCKET.value)
        symbolsDf = pd.DataFrame(self.dataParser.get_data())['s']
        print("Symbols to fetch:", symbolsDf)
        tokenThread.start()
        # Step 5: Start option data fetchers
        optionTasks = []
        for symbol in symbolsDf.tail(10):  # Limit to 10 symbols
            asyncio.new_event_loop()
            dataParser = DataParser(self.dataParser.client)
            task = Thread(target=self.fetch_data_background, args=(symbol+"@ticker", dataParser, Endpoints.OPTIONWEBSOCKET.value,), daemon=True)
            optionTasks.append((task, dataParser))
            task.start()
        while True:
            try:
                tokenPrice = self.dataParser.get_data()['p']
                print(tokenPrice)
            except:
                continue
            
            if tokenPrice:
                
                
                
                    # Step 6: Process fetched data with ProcessPoolExecutor
                    with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
                        try:
                            for thread in optionTasks:
                                try:
                                    optionData = thread[1].get_data()
                                    executor.submit(self.process_option, (tokenPrice, optionData))
                                    theoreticalPrice = self.process_option(tokenPrice, optionData)
                                    time.sleep(1)
                                    print(optionData['mp'])
                                    if float(optionData['mp']) * 1.03 > theoreticalPrice:
                                        print(f"Option {optionData['s']} is overpriced")
                                    elif float(optionData['mp']) * 0.97 < theoreticalPrice:
                                        print(f"Option {optionData['s']} is underpriced")
                                    else:
                                        print(f"Option {optionData['s']} is fairly priced")
                                except Exception as e: 
                                    print(e)
                        except KeyboardInterrupt:
                            print("Stopping all tasks...")

                        finally:
                            # Step 7: Cancel all background tasks
                            for task in optionTasks:
                                task.cancel()
                            print("All tasks stopped.")    
        




        
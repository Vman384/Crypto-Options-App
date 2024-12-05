import numpy as np
from scipy.stats import norm
from data_parser import DataParser

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
        pass

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
            Type of option: 'call' or 'put'

        Returns:
        float
            Option price
        """
        d1 = (np.log(S / K) + (r + 0.5 * vega()**2) * T) / (vega() * np.sqrt(T))
        d2 = d1 - vega() * np.sqrt(T)
        
        if option_type == 'call':
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        elif option_type == 'put':
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        else:
            raise ValueError("option_type must be 'call' or 'put'")
        
        return price


     
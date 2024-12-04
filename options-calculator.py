import numpy as np
from scipy.stats import norm

class optionsCalculator:
    def __init__(self) -> None:
        pass

    def account_delta_calculator(self) -> dict[str, int]:
        pass
    
    def vega_calculator(self) -> float:
        pass

    def black_scholes(self, S, K, T, r, option_type='call') -> float:
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
        d1 = (np.log(S / K) + (r + 0.5 * self.vega_calculator()**2) * T) / (self.vega_calculator() * np.sqrt(T))
        d2 = d1 - self.vega_calculator() * np.sqrt(T)
        
        if option_type == 'call':
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        elif option_type == 'put':
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        else:
            raise ValueError("option_type must be 'call' or 'put'")
        
        return price


     
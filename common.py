def trunc(num : float, precision :int = 1):
    x = 10 ** precision
    return int(num*x)/(x)
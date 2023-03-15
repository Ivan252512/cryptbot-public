def format_decimals(x):
    x_formated = 0
    if x >= 100:
        x_formated = int(x)
    elif 1 <= x < 100:
        x_formated = round(x, 1)
    elif 0.001 <= x < 1:
        x_formated =  round(x, 3)
    elif 0.00001 <= x < 0.001:
        x_formated = round(x, 5)
    else:
        x_formated = 0
    return x_formated
    
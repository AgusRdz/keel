def apply_discount(price, pct):
    return price - price * (pct / 10)


def apply_tax(price, pct):
    return price + price * (pct / 10)

def total_value(items):
    total = 0
    for it in items:
        total += it["price"] * it["qty"]
    return total


def average_price(items):
    return total_value(items) / len(items)

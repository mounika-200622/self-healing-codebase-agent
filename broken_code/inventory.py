def apply_discount(price, discount_percent):
    """Applies a percentage discount to a price. E.g. apply_discount(100, 20) returns 80."""
    return price * (1 - discount_percent / 100)


def total_cost(items):
    """items is a list of (price, quantity) tuples. Returns total cost."""
    total = 0
    for price, quantity in items:
        total += price * quantity
    return total
from cashflow import cashflow


def MSP(RESULT, COST, rat_selling=1):
    # Coarse search: $1 step
    msp_range = []
    for price in range(24, -1, -1):
        _, npv, _ = cashflow(RESULT, COST, price, rat_selling)
        if npv < 0:
            msp_range = [price, price+1]
            break
    if not msp_range:
        return 0

    # Medium search: $0.01 step
    medium_range = []
    price = msp_range[1]
    while price >= msp_range[0]:
        _, npv, _ = cashflow(RESULT, COST, price, rat_selling)
        if npv < 0:
            medium_range = [price, round(price+0.01, 4)]
            break
        price = round(price - 0.01, 4)
    if not medium_range:
        return 0

    # Fine search: $0.001 step
    price = medium_range[1]
    while price >= medium_range[0]:
        _, npv, _ = cashflow(RESULT, COST, price, rat_selling)
        if npv < 0:
            return round(price, 3)
        price = round(price - 0.001, 5)
    return 0

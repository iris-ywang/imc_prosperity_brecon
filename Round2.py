from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order
import jsonpickle
import numpy as np


class Trader:

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        # Initialize the method output dict as an empty dict
        result = {}

        # load previous data
        data = jsonpickle.decode(state.traderData) if state.traderData else {}

        # Iterate over all the keys (the available products) contained in the order dephts
        for product in state.order_depths.keys():
            # Retrieve the Order Depth containing all the market BUY and SELL orders
            order_depth: OrderDepth = state.order_depths[product]
            # Initialize the list of Orders to be sent as an empty list
            orders: list[Order] = []

            if len(order_depth.sell_orders) > 0:
                # Sort all the available sell orders by their price,
                # and select only the sell order with the lowest price
                best_ask = min(order_depth.sell_orders.keys())
                best_ask_volume = order_depth.sell_orders[best_ask]

            if len(order_depth.buy_orders) > 0:
                # Sort all the available buy orders by their price,
                # and select only the buy order with the highest price
                best_bid = max(order_depth.buy_orders.keys())
                best_bid_volume = order_depth.buy_orders[best_bid]

            mid_price = (best_ask + best_bid) / 2
            position = state.position.get(product, 0)
            print(f"mid_price: {mid_price}, position: {position}, best_bid: {best_bid}, best_ask: {best_ask}\n")

            if product == "SQUID_INK":
                history = data.get("SQUID_INK", [])
                if len(history) > 10:
                    roll_mean = np.mean(history)
                    history.pop(0)

                    # compare rolling mean with mid price and skew??
                    # skew depends on the position
                    skew = - np.round(position / 10)
                    price = roll_mean + skew
                    # buy if target price is lower than rolling mean
                    if mid_price <= price:  # cheap, buy
                        bid_price = min(price, best_bid + 1)
                        bid_vol = max(price - bid_price, 5) * 5 - position
                        orders.append(Order(product, bid_price, bid_vol))
                        print(f"BUY {bid_vol}x {bid_price}\n")
                    # sell if target price is higher than rolling mean
                    elif mid_price >= price:  # expensive, sell
                        ask_price = max(price, best_ask - 1)
                        ask_vol = max(ask_price - price, 5) * 5 + position
                        orders.append(Order(product, ask_price, -ask_vol))
                        print(f"SELL {ask_vol}x {ask_price}\n")
                    result[product] = orders

                history.append(mid_price)
                data["SQUID_INK"] = history


            elif product == "RAINFOREST_RESIN":

                # stable price at 10000
                # buy no higher than 10000, use min(10000, best_bid+1)
                # sell no lower than 10000, use max(10000, best_ask-1)

                if mid_price < 10000 & position <= 0:  # cheap & short, buy
                    bid_price = min(10000, best_bid + 1)
                    bid_vol_1 = max(10000 - bid_price, 5) * 5 - position
                    orders.append(Order(product, bid_price, bid_vol_1))
                    print(f"BUY {bid_vol_1}x {bid_price}\n")
                    bid_vol_2 = max(10000 - bid_price, 5) * 5
                    orders.append(Order(product, bid_price, bid_vol_2))
                    print(f"BUY {bid_vol_2}x {bid_price - 1}\n")
                elif mid_price > 10000 & position >= 0:  # expensive & long, sell
                    ask_price = max(10000, best_ask - 1)
                    ask_vol_1 = max(ask_price - 10000, 5) * 5 + position
                    orders.append(Order(product, ask_price, -ask_vol_1))
                    print(f"SELL {ask_vol_1}x {ask_price}\n")
                    ask_vol_2 = max(ask_price - 10000, 5) * 5
                    orders.append(Order(product, ask_price + 1, -ask_vol_2))
                    print(f"SELL {ask_vol_2}x {ask_price + 1}\n")
                result[product] = orders


            elif product in ["DJEMBES", "JAMS", "CROISSANTS", "PICNIC_BASKET1", "PICNIC_BASKET2"]:

                mid_prices = {}
                for p in ["DJEMBES", "JAMS", "CROISSANTS", "PICNIC_BASKET1", "PICNIC_BASKET2"]:
                    od = state.order_depths.get(p)
                    if od and od.buy_orders and od.sell_orders:
                        mid_prices[p] = (min(od.sell_orders.keys()) + max(od.buy_orders.keys())) / 2

                if all(k in mid_prices for k in ["DJEMBES", "JAMS", "CROISSANTS", "PICNIC_BASKET1", "PICNIC_BASKET2"]):
                    synthetic_A = mid_prices["DJEMBES"] + 3 * mid_prices["JAMS"] + 6 * mid_prices["CROISSANTS"]
                    synthetic_B = 2 * mid_prices["JAMS"] + 4 * mid_prices["CROISSANTS"]


                    spread_A = mid_prices["PICNIC_BASKET1"] - synthetic_A
                    spread_B = mid_prices["PICNIC_BASKET2"] - synthetic_B
                    spread_djembe = mid_prices["PICNIC_BASKET1"] - 1.5 * mid_prices["PICNIC_BASKET2"] - mid_prices[
                        "DJEMBES"]
                    # spread_djembe = spread_A - 1.5 * spread_B

                    for key, spread in zip(["spread_A", "spread_B", "spread_djembe"], [spread_A, spread_B, spread_djembe]):
                        h = data.get(key, [])
                        h.append(spread)
                        if len(h) > 3000:
                            h.pop(0)
                        data[key] = h

                    def calculate_z_score(series, window=3000):
                        if len(series) < window:
                            return 0
                        return (series[-1] - np.mean(series[-window:])) / (np.std(series[-window:]) + 1e-6)

                    z_A = calculate_z_score(data.get("spread_A", []))
                    z_B = calculate_z_score(data.get("spread_B", []))
                    z_pair = calculate_z_score(data.get("spread_djembe", []))

                    A_threshold, djembe_threshold, vol = 1.2, 1.2, 5

                    price_data = {}
                    for p in ["DJEMBES", "JAMS", "CROISSANTS", "PICNIC_BASKET1"]:
                        od = state.order_depths[p]
                        if od.sell_orders:
                            price_data[f"{p}_ask"] = min(od.sell_orders.keys())
                        if od.buy_orders:
                            price_data[f"{p}_bid"] = max(od.buy_orders.keys())

                    # Trade basket A vs synthetic A
                    if z_A > A_threshold:
                        # PB1 is rich — short it, long synthetic
                        orders.append(Order("PICNIC_BASKET1", price_data["PICNIC_BASKET1_bid"], -vol))
                        orders.append(Order("DJEMBES", price_data["DJEMBES_ask"], +1 * vol))
                        orders.append(Order("JAMS", price_data["JAMS_ask"], +3 * vol))
                        orders.append(Order("CROISSANTS", price_data["CROISSANTS_ask"], +6 * vol))

                    elif z_A < - A_threshold:
                        # PB1 is cheap — long it, short synthetic
                        orders.append(Order("PICNIC_BASKET1", price_data["PICNIC_BASKET1_ask"], +vol))
                        orders.append(Order("DJEMBES", price_data["DJEMBES_bid"], -1 * vol))
                        orders.append(Order("JAMS", price_data["JAMS_bid"], -3 * vol))
                        orders.append(Order("CROISSANTS", price_data["CROISSANTS_bid"], -6 * vol))

                    # Trade Djembe
                    if z_pair > djembe_threshold:
                        # DJEMBE is rich — short it
                        orders.append(Order("DJEMBES", price_data["DJEMBES_bid"], -vol))
                    elif z_pair < -djembe_threshold:
                        # DJEMBE is cheap — long it
                        orders.append(Order("DJEMBES", price_data["DJEMBES_ask"], +vol))
                for order in orders:
                    result.setdefault(order.product, []).append(order)






        traderData = jsonpickle.encode(data)
        # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.

        conversions = 1

        # Return the dict of orders
        # These possibly contain buy or sell orders
        # Depending on the logic above

        return result, conversions, traderData


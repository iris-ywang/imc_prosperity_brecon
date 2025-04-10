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
                    if mid_price <= price: # cheap, buy
                        bid_price = min(price, best_bid + 1)
                        bid_vol = max(price-bid_price, 5)*5 - position
                        orders.append(Order(product, bid_price, bid_vol))
                        print(f"BUY {bid_vol}x {bid_price}\n")
                    # sell if target price is higher than rolling mean
                    elif mid_price >= price: # expensive, sell
                        ask_price = max(price, best_ask - 1)
                        ask_vol = max(ask_price-price, 5)*5 + position
                        orders.append(Order(product, ask_price, -ask_vol))
                        print(f"SELL {ask_vol}x {ask_price}\n")
                    result[product] = orders
                
                history.append(mid_price)
                data["SQUID_INK"] = history


            elif product == "RAINFOREST_RESIN":

                # stable price at 10000
                # buy no higher than 10000, use min(10000, best_bid+1)
                # sell no lower than 10000, use max(10000, best_ask-1)

                if mid_price < 10000 & position <= 0: # cheap & short, buy
                    bid_price = min(10000, best_bid + 1)
                    bid_vol = max(10000-bid_price, 5)*10 - position
                    orders.append(Order(product, bid_price, bid_vol))
                    print(f"BUY {bid_vol}x {bid_price}\n")
                elif mid_price > 10000 & position >= 0: # expensive & long, sell
                    ask_price = max(10000, best_ask - 1)
                    ask_vol = max(ask_price-10000, 5)*10 + position
                    orders.append(Order(product, ask_price, -ask_vol))
                    print(f"SELL {ask_vol}x {ask_price}\n")
                result[product] = orders

  
        traderData = jsonpickle.encode(data)
        # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.
        
        conversions = 1 

                # Return the dict of orders
                # These possibly contain buy or sell orders
                # Depending on the logic above
        
        return result, conversions, traderData

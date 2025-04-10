from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order


class Trader:

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        # Initialize the method output dict as an empty dict
        result = {}

        # Iterate over all the keys (the available products) contained in the order dephts
        for product in state.order_depths.keys():

            if product == "RAINFOREST_RESIN":

                # stable price at 10000
                # buy no higher than 10000, use min(10000, best_bid+1)
                # sell no lower than 10000, use max(10000, best_ask-1)

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

                # # Retrieve the Order Depth containing all the market BUY and SELL orders
                # order_depth: OrderDepth = state.order_depths[product]

                # # Initialize the list of Orders to be sent as an empty list
                # orders: list[Order] = []

                # # Note that this value of 1 is just a dummy value, you should likely change it!
                # acceptable_price = 10

                # # If statement checks if there are any SELL orders in the market
                # if len(order_depth.sell_orders) > 0:

                #     # Sort all the available sell orders by their price,
                #     # and select only the sell order with the lowest price
                #     best_ask = min(order_depth.sell_orders.keys())
                #     best_ask_volume = order_depth.sell_orders[best_ask]

                #     # Check if the lowest ask (sell order) is lower than the above defined fair value
                #     if best_ask < acceptable_price:

                #         # In case the lowest ask is lower than our fair value,
                #         # This presents an opportunity for us to buy cheaply
                #         # The code below therefore sends a BUY order at the price level of the ask,
                #         # with the same quantity
                #         # We expect this order to trade with the sell order
                #         print("BUY", str(-best_ask_volume) + "x", best_ask)
                #         orders.append(Order(product, best_ask, -best_ask_volume))

                # # The below code block is similar to the one above,
                # # the difference is that it find the highest bid (buy order)
                # # If the price of the order is higher than the fair value
                # # This is an opportunity to sell at a premium
                # if len(order_depth.buy_orders) != 0:
                #     best_bid = max(order_depth.buy_orders.keys())
                #     best_bid_volume = order_depth.buy_orders[best_bid]
                #     if best_bid > acceptable_price:
                #         print("SELL", str(best_bid_volume) + "x", best_bid)
                #         orders.append(Order(product, best_bid, -best_bid_volume))

                # # Add all the above the orders to the result dict
                # result[product] = orders
                
        traderData = "SAMPLE" # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.
        
        conversions = 1 

                # Return the dict of orders
                # These possibly contain buy or sell orders
                # Depending on the logic above
        
        return result, conversions, traderData

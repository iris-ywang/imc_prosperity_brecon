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
        data = jsonpickle.decode(state.traderData) if state.traderData and state.traderData != 'SAMPLE' else {}

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
                best_ask_volume = -order_depth.sell_orders[best_ask]

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
                    last_price = history[-1]
                    history.pop(0)
                
                history.append(mid_price)
                data["SQUID_INK"] = history

                if not last_price: continue
                # check if the price is stable
                # if abs((mid_price - last_price)/last_price) > 0.0025: continue

                # determine fair price
                beta = -0.20
                fair = mid_price + beta * (mid_price - last_price)
            
                # slew due to position
                fair -= np.round(position / 27) # hyperparam

                width = 1
                limit = 50
                order_lim = 25
                bid_vol = ask_vol = 0

                # if the price is good, always take the best order
                if best_ask <= fair - width:
                    # buy at the best ask
                    bid_price = best_ask
                    bid_vol = min(max(0, min(best_ask_volume, limit - position)), order_lim)
                    if bid_vol > 0:
                        self.execute_take_order(product, order_depth, orders, bid_price, bid_vol)
                        position += bid_vol
                elif best_bid >= fair + width:
                    # sell at the best bid
                    ask_price = best_bid
                    ask_vol = min(max(0, min(best_bid_volume, limit + position)), order_lim)
                    if ask_vol >0:
                        self.execute_take_order(product, order_depth, orders, ask_price, -ask_vol)
                        position -= ask_vol

                # if there are more orders to take that can reduce the position, take them
                if position > 0 and len(order_depth.buy_orders) > 0:
                    best_bid = max(order_depth.buy_orders.keys())
                    best_bid_volume = order_depth.buy_orders[best_bid]
                    if best_bid >= fair + width:
                        ask_price = best_bid
                        ask_vol = min(max(0, min(best_bid_volume, position)), order_lim)
                        if ask_vol >0:
                            self.execute_take_order(product, order_depth, orders, ask_price, -ask_vol)
                            position -= ask_vol
                elif position < 0 and len(order_depth.sell_orders) > 0:
                    best_ask = min(order_depth.sell_orders.keys())
                    best_ask_volume = -order_depth.sell_orders[best_ask]
                    if best_ask <= fair - width:
                        bid_price = best_ask
                        bid_vol = min(max(0, min(best_ask_volume, -position)), order_lim)
                        if bid_vol > 0:
                            self.execute_take_order(product, order_depth, orders, bid_price, bid_vol)
                            position += bid_vol
                
                # market making orders
                best_ask_above_fair = min([i for i in order_depth.sell_orders.keys() if i > fair+width], default=0)
                best_bid_below_fair = max([i for i in order_depth.buy_orders.keys() if i < fair-width], default=0)

                if best_ask_above_fair:
                    sell_mm_vol = min(max(0, limit + position), order_lim)
                    if sell_mm_vol > 0:
                        self.execute_marketmaking_order(product, orders, best_ask_above_fair-1, -sell_mm_vol)
                if best_bid_below_fair:
                    buy_mm_vol = min(max(0, limit - position), order_lim)
                    if buy_mm_vol > 0:
                        self.execute_marketmaking_order(product, orders, best_bid_below_fair+1, buy_mm_vol)

                result[product] = orders


            elif product == "RAINFOREST_RESIN":

                # stable price at 10000
                # buy no higher than 9999
                # sell no lower than 10001

                fair = 10000
                width = 1
                bid_vol = ask_vol = 0
                limit = 50
                order_lim = 50

                # if the price is good, always take the best order
                if best_ask <= fair - width:
                    # buy at the best ask
                    bid_price = best_ask
                    bid_vol = max(0, min(best_ask_volume, limit - position))
                    if bid_vol > 0:
                        self.execute_take_order(product, order_depth, orders, bid_price, bid_vol)
                        position += bid_vol
                elif best_bid >= fair + width:
                    # sell at the best bid
                    ask_price = best_bid
                    ask_vol = max(0, min(best_bid_volume, limit + position))
                    if ask_vol >0:
                        self.execute_take_order(product, order_depth, orders, ask_price, -ask_vol)
                        position -= ask_vol

                # market making orders
                best_ask_above_fair = min([i for i in order_depth.sell_orders.keys() if i > fair+width], default=0)
                best_bid_below_fair = max([i for i in order_depth.buy_orders.keys() if i < fair-width], default=0)

                if best_ask_above_fair:
                    sell_mm_vol = max(0, limit + position)
                    if sell_mm_vol > 0:
                        self.execute_marketmaking_order(product, orders, best_ask_above_fair-1, -sell_mm_vol)
                if best_bid_below_fair:
                    buy_mm_vol = max(0, limit - position)
                    if buy_mm_vol > 0:
                        self.execute_marketmaking_order(product, orders, best_bid_below_fair+1, buy_mm_vol)

                result[product] = orders

            elif product == "KELP":
                history = data.get("KELP", [])
                last_price = 0
                if len(history) > 2:
                    last_price = history[-1]
                    history.pop(0)
                
                history.append(mid_price)
                data["KELP"] = history
                if not last_price: continue
                # check if the price is stable
                # if abs((mid_price - last_price)/last_price) > 0.0012: continue

                # determine fair price
                beta = -0.49
                fair = mid_price + beta * (mid_price - last_price)
            
                # slew due to position
                # overall market trend is up, set a positive position target
                fair -= np.round((position-35) / 30)

                width = 1
                limit = 50
                bid_vol = ask_vol = 0
                order_lim = 25

                # if the price is good, always take the best order
                if best_ask <= fair - width:
                    # buy at the best ask
                    bid_price = best_ask
                    bid_vol = min(max(0, min(best_ask_volume, limit - position)), order_lim)
                    if bid_vol > 0:
                        self.execute_take_order(product, order_depth, orders, bid_price, bid_vol)
                        position += bid_vol
                elif best_bid >= fair + width:
                    # sell at the best bid
                    ask_price = best_bid
                    ask_vol = min(max(0, min(best_bid_volume, limit + position)), order_lim)
                    if ask_vol >0:
                        self.execute_take_order(product, order_depth, orders, ask_price, -ask_vol)
                        position -= ask_vol

                # market making orders
                best_ask_above_fair = min([i for i in order_depth.sell_orders.keys() if i > fair+width], default=0)
                best_bid_below_fair = max([i for i in order_depth.buy_orders.keys() if i < fair-width], default=0)

                if best_ask_above_fair:
                    sell_mm_vol = min(max(0, limit + position), order_lim)
                    if sell_mm_vol > 0:
                        self.execute_marketmaking_order(product, orders, best_ask_above_fair-1, -sell_mm_vol)
                if best_bid_below_fair:
                    buy_mm_vol = min(max(0, limit - position), order_lim)
                    if buy_mm_vol > 0:
                        self.execute_marketmaking_order(product, orders, best_bid_below_fair+1, buy_mm_vol)

                result[product] = orders

                pass

  
        traderData = jsonpickle.encode(data)
        # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.
        
        conversions = 1 

                # Return the dict of orders
                # These possibly contain buy or sell orders
                # Depending on the logic above
        
        return result, conversions, traderData

    @staticmethod
    def execute_take_order(product: str, order_depth: OrderDepth, orders: List[Order],
                           price: int, volume: int) -> None:
        """
        Execute a take order by adding it to the orders list and updating the order depth.
        """
        if volume > 0:
            orders.append(Order(product, price, volume))
            print(f"TAKE: BUY {volume}x {price}\n")
            order_depth.sell_orders[price] += volume
            if order_depth.sell_orders[price] == 0:
                del order_depth.sell_orders[price]
        elif volume < 0:
            orders.append(Order(product, price, volume))
            print(f"TAKE: SELL {abs(volume)}x {price}\n")
            order_depth.buy_orders[price] += volume
            if order_depth.buy_orders[price] == 0:
                del order_depth.buy_orders[price]

    @staticmethod
    def execute_marketmaking_order(product: str, orders: List[Order],
                                   price: int, volume: int) -> None:
        """
        Execute a market making order by adding it to the orders list.
        """
        if volume > 0:
            orders.append(Order(product, price, volume))
            print(f"MARKET MAKING: BUY {volume}x {price}\n")
        elif volume < 0:
            orders.append(Order(product, price, volume))
            print(f"MARKET MAKING: SELL {abs(volume)}x {price}\n")



# from datamodel import LoadTradingState
# import pandas as pd

# if __name__ == "__main__":
#     trader = Trader()
#     # The run method will be called by the framework
#     # The code below is just for testing purposes
#     df = pd.read_csv("./data/round-1-island-data-bottle/prices_round_1_day_0.csv", sep=";")

#     state = LoadTradingState().load_all_products_by_timestamp(df, 0)

#     trader.run(state)

"""COPIED FROM THE EXAMPLE-PROGRAM.PY"""

from typing import Dict, List

from datamodel import OrderDepth, TradingState, Order
import jsonpickle
import numpy as np
import statistics


class Trader:

    @staticmethod
    def generate_correlation(history: list, rolling_period: int = 30, eval_length: int = 15) -> float:
        if len(history) < rolling_period + eval_length:
            print("Not enough data for the rolling window.")
            return 0.0

        # Convert to numpy array for fast computation
        history_np = np.array(history, dtype=np.float64)

        # Compute rolling mean using convolution
        kernel = np.ones(rolling_period) / rolling_period
        rolling_means = np.convolve(history_np, kernel, mode='valid')

        # Take the last `rolling_period` rolling mean values
        latest_roll_means = rolling_means[-eval_length:]

        # Create a linear range to correlate with
        index_array = np.arange(eval_length)

        # Calculate rough correlation using numpy
        # corr = np.corrcoef(latest_roll_means, index_array)[0, 1]

        # Calculate gradient of latest_roll_means and index_array
        corr = np.corrcoef(latest_roll_means, index_array)[0, 1]
        print(f"Correlation: {corr}\n")

        gradient_roll_means = statistics.linear_regression(index_array, latest_roll_means, )[0]

        return gradient_roll_means

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        # Initialize the method output dict as an empty dict
        result = {}

        # load previous data
        data = jsonpickle.decode(state.traderData) if state.traderData and state.traderData != "SAMPLE" else {}

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

            if product == "SQUID_INK":
                print(f"mid_price: {mid_price}, position: {position}, best_bid: {best_bid}, best_ask: {best_ask}\n")

                history = data.get("SQUID_INK", [])
                print(f"{product} history: {history}\n")

                timestamp = state.timestamp
                period_w_allowance = 33 * 100

                # check the rolling mean for the first 50 timestamps after a defined period starts


                trend_eval_length = 8
                # if timestamp == 65 * 100:
                #     corr = self.generate_correlation(history=history, rolling_period=30, eval_length=trend_eval_length)


                if (len(history) > period_w_allowance / 100) & \
                        (timestamp % period_w_allowance == trend_eval_length * 100):
                    # calculating the 30 rolling means and correlation on the last 15 rolling means
                    gradient = self.generate_correlation(
                        history=history,
                        rolling_period=30,
                        eval_length=trend_eval_length
                    )

                    print(f"Using gradient: {gradient}\n")

                    presumed_max_gradient = 20 / (period_w_allowance / 100)    /2

                    corr = gradient / presumed_max_gradient

                    if corr >= 0.3:
                        # corr >= 0.3, price is going up. we can buy:
                        if corr >= 0.6 and position <= 25:
                            bid_price = best_ask + 1
                            bid_vol = int(16 /2)
                            orders.append(Order(product, bid_price, bid_vol))
                            print(f"BUY {bid_vol}x {bid_price}\n")
                        elif corr >= 0.3 and position <= 40:
                            bid_price = best_ask + 1
                            bid_vol = int(4 /2)
                            orders.append(Order(product, bid_price, bid_vol))
                            print(f"BUY {bid_vol}x {bid_price}\n")

                    if corr <= -0.3:
                        # corr <= -0.3, price is going down. we can sell:
                        if corr <= -0.6 and position >= -25:
                            ask_price = best_bid + 1
                            ask_vol = int(16 /2)
                            orders.append(Order(product, ask_price, -ask_vol))
                            print(f"SELL {ask_vol}x {ask_price}\n")
                        elif corr <= -0.3 and position >= -40:
                            ask_price = best_bid + 1
                            ask_vol = int(16 /2)
                            orders.append(Order(product, ask_price, -ask_vol))
                            print(f"SELL {ask_vol}x {ask_price}\n")

                    result[product] = orders

                if (len(history) > period_w_allowance / 100) & \
                        (timestamp % period_w_allowance == (trend_eval_length + 1) * 100):
                    # log the last trade in my data
                    try:
                        last_trade = state.own_trades[product][-1]
                        data["SQUID_INK_TRADE_TO_DEMOLISH"] = {
                            "trade": last_trade,
                            "remaining_quantity": last_trade.quantity
                        }
                    except KeyError:
                        data["SQUID_INK_TRADE_TO_DEMOLISH"] = {}


                if timestamp % period_w_allowance == 0:
                    # Sell whatever you bought last time and vice versa
                    last_trade_and_remains = data.get("SQUID_INK_TRADE_TO_DEMOLISH", {})

                    if last_trade_and_remains:

                        last_trade = last_trade_and_remains["trade"]
                        quantity = last_trade_and_remains["remaining_quantity"]

                        print("Trade the quantities from the beginning of this period:")
                        print(last_trade, "\n")
                        print(f"Remaining quantity to let-go: {quantity}\n")


                        # if quantity > 0: last trade was a buy
                        # if quantity < 0: last trade was a sell

                        if quantity > 0:
                            # last trade was a buy, so we want to sell the same quantity if price ok

                            last_trade_price = last_trade.price

                            if mid_price >= last_trade_price:
                                ask_vol = quantity
                            else:
                                ask_vol = int(quantity / 2)

                            ask_price = best_ask
                            orders.append(Order(product, ask_price, -ask_vol))
                            print(f"SELL {ask_vol}x {ask_price}\n")
                        if quantity < 0:
                            # last trade was a sell, so we want to buy the same quantity

                            last_trade_price = last_trade.price

                            if mid_price <= last_trade_price:
                                bid_vol = -quantity
                            else:
                                bid_vol = int(-quantity / 2)

                            bid_price = best_bid
                            orders.append(Order(product, bid_price, bid_vol))
                            print(f"BUY {bid_vol}x {bid_price}\n")



                if len(history) > 2 * (period_w_allowance / 100):
                    # if we have more than 2 periods of history, we can start to shorten the length
                    # of the history from the beginning
                    history.pop(0)

                history.append(mid_price)
                data["SQUID_INK"] = history



        traderData = jsonpickle.encode(data)
        # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.

        conversions = 1

        # Return the dict of orders
        # These possibly contain buy or sell orders
        # Depending on the logic above

        return result, conversions, traderData



# if __name__ == "__main__":
#     from datamodel import LoadTradingState
#     import pandas as pd
#     trader = Trader()
#     # The run method will be called by the framework
#     # The code below is just for testing purposes
#     df = pd.read_csv("./data/round-1-island-data-bottle/prices_round_1_day_0.csv", sep=";")
#
#     for t in range(65, 81):
#         # Load the trading state for the current timestamp
#         state = LoadTradingState().load_all_products_by_timestamp(df, int(t * 100))
#         # Run the trader with the loaded state
#         trader.run(state)


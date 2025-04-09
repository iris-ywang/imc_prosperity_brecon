"""
Copied from archipelago. 
Link:
https://imc-prosperity.notion.site/Writing-an-Algorithm-in-Python-19ee8453a0938114a15eca1124bf28a1#19ee8453a0938005b98dc82bb11b21b1
"""

import json
from typing import Dict, List
from json import JSONEncoder
import jsonpickle

import pandas as pd
Time = int
Symbol = str
Product = str
Position = int
UserId = str
ObservationValue = int


class Listing:

    def __init__(self, symbol: Symbol, product: Product, denomination: Product):
        self.symbol = symbol
        self.product = product
        self.denomination = denomination
        
                 
class ConversionObservation:

    def __init__(self, bidPrice: float, askPrice: float, transportFees: float, exportTariff: float, importTariff: float, sugarPrice: float, sunlightIndex: float):
        self.bidPrice = bidPrice
        self.askPrice = askPrice
        self.transportFees = transportFees
        self.exportTariff = exportTariff
        self.importTariff = importTariff
        self.sugarPrice = sugarPrice
        self.sunlightIndex = sunlightIndex
        

class Observation:

    def __init__(self, plainValueObservations: Dict[Product, ObservationValue], conversionObservations: Dict[Product, ConversionObservation]) -> None:
        self.plainValueObservations = plainValueObservations
        self.conversionObservations = conversionObservations
        
    def __str__(self) -> str:
        return "(plainValueObservations: " + jsonpickle.encode(self.plainValueObservations) + ", conversionObservations: " + jsonpickle.encode(self.conversionObservations) + ")"
     

class Order:

    def __init__(self, symbol: Symbol, price: int, quantity: int) -> None:
        self.symbol = symbol
        self.price = price
        self.quantity = quantity

    def __str__(self) -> str:
        return "(" + self.symbol + ", " + str(self.price) + ", " + str(self.quantity) + ")"

    def __repr__(self) -> str:
        return "(" + self.symbol + ", " + str(self.price) + ", " + str(self.quantity) + ")"
    

class OrderDepth:

    def __init__(self):
        self.buy_orders: Dict[int, int] = {}
        self.sell_orders: Dict[int, int] = {}


class Trade:

    def __init__(self, symbol: Symbol, price: int, quantity: int, buyer: UserId=None, seller: UserId=None, timestamp: int=0) -> None:
        self.symbol = symbol
        self.price: int = price
        self.quantity: int = quantity
        self.buyer = buyer
        self.seller = seller
        self.timestamp = timestamp

    def __str__(self) -> str:
        return "(" + self.symbol + ", " + self.buyer + " << " + self.seller + ", " + str(self.price) + ", " + str(self.quantity) + ", " + str(self.timestamp) + ")"

    def __repr__(self) -> str:
        return "(" + self.symbol + ", " + self.buyer + " << " + self.seller + ", " + str(self.price) + ", " + str(self.quantity) + ", " + str(self.timestamp) + ")"


class TradingState(object):

    def __init__(self,
                 traderData: str,
                 timestamp: Time,
                 listings: Dict[Symbol, Listing],
                 order_depths: Dict[Symbol, OrderDepth],
                 own_trades: Dict[Symbol, List[Trade]],
                 market_trades: Dict[Symbol, List[Trade]],
                 position: Dict[Product, Position],
                 observations: Observation):
        self.traderData = traderData
        self.timestamp = timestamp
        self.listings = listings
        self.order_depths = order_depths
        self.own_trades = own_trades
        self.market_trades = market_trades
        self.position = position
        self.observations = observations
        
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)

    
class ProsperityEncoder(JSONEncoder):

        def default(self, o):
            return o.__dict__


class LoadTradingState():
    """
    For trials & debugging by Brecon.

    Add this to trader.py (or equivalent) to load a trading state from a CSV file.
    The TradingState object is the desired input for our Trader class to run trading.

    Credit: Copilot**

    Example:

        In example-program.py, you can use the following code to load a trading state from a CSV file:

        from datamodel import LoadTradingState

        if __name__ == "__main__":
            trader = Trader()
            # The run method will be called by the framework
            # The code below is just for testing purposes
            df = pd.read_csv("./data/round-1-island-data-bottle/prices_round_1_day_0.csv", sep=";")

            state = LoadTradingState().load_all_product_by_timestamp(df, 0)

            trader.run(state)

    """

    def load_single_product(self, df: pd.DataFrame, row_id: int):

        # Select the row of the dataframe, and create a TradingState object from the row.
        # Each row, in CSV format, contains the following columns:
        # day;timestamp;product;bid_price_1;bid_volume_1;bid_price_2;bid_volume_2;bid_price_3;bid_volume_3;ask_price_1;ask_volume_1;ask_price_2;ask_volume_2;ask_price_3;ask_volume_3;mid_price;profit_and_loss
        # The row_id is the index of the row in the dataframe.
        row = df.iloc[row_id]
        self.timestamp = row["timestamp"]
        self.product = row["product"]
        self.bid_price_1 = row["bid_price_1"]
        self.bid_volume_1 = row["bid_volume_1"]
        self.bid_price_2 = row["bid_price_2"]
        self.bid_volume_2 = row["bid_volume_2"]
        self.bid_price_3 = row["bid_price_3"]
        self.bid_volume_3 = row["bid_volume_3"]
        self.ask_price_1 = row["ask_price_1"]
        self.ask_volume_1 = -row["ask_volume_1"]
        self.ask_price_2 = row["ask_price_2"]
        self.ask_volume_2 = -row["ask_volume_2"]
        self.ask_price_3 = row["ask_price_3"]
        self.ask_volume_3 = -row["ask_volume_3"]
        self.mid_price = row["mid_price"]
        self.profit_and_loss = row["profit_and_loss"]
        self.symbol = row["product"]
        self.denomination = row["product"]
        self.listing = Listing(self.symbol, self.product, self.denomination)
        self.order_depth = OrderDepth()
        self.order_depth.buy_orders[self.bid_price_1] = self.bid_volume_1

        self.order_depth.buy_orders[self.bid_price_2] = self.bid_volume_2
        self.order_depth.buy_orders[self.bid_price_3] = self.bid_volume_3
        self.order_depth.sell_orders[self.ask_price_1] = self.ask_volume_1
        self.order_depth.sell_orders[self.ask_price_2] = self.ask_volume_2
        self.order_depth.sell_orders[self.ask_price_3] = self.ask_volume_3
        self.position = {self.product: 0}
        self.own_trades = {self.product: []}
        self.market_trades = {self.product: []}
        self.observations = Observation({self.product: self.mid_price}, {self.product: ConversionObservation(0, 0, 0, 0, 0, 0, 0)})
        self.traderData = "SAMPLE"
        self.timestamp = 0
        self.listings = {self.symbol: self.listing}
        self.order_depths = {self.symbol: self.order_depth}
        self.own_trades = {self.symbol: []}

        # Enter the required data into the TradingState object
        state = TradingState(
            self.traderData,
            self.timestamp,
            self.listings,
            self.order_depths,
            self.own_trades,
            self.market_trades,
            self.position,
            self.observations)
        return state

    def load_all_products_by_timestamp(self, df, timestamp):
        """
        Given a timestamp, filter the df by the timestamp and create a single TradingState object with multiple
        products listed in the listings, order depths, market trades and own trades.
        """
        # Filter the dataframe by the timestamp
        df = df[df["timestamp"] == timestamp]

        # Create a TradingState object from the filtered dataframe
        self.timestamp = timestamp
        self.listings = {}
        self.order_depths = {}
        self.own_trades = {}
        self.market_trades = {}
        self.position = {}
        self.observations = {}

        for index, row in df.iterrows():
            product = row["product"]
            listing = Listing(row["product"], row["product"], row["product"])
            order_depth = OrderDepth()
            order_depth.buy_orders[row["bid_price_1"]] = row["bid_volume_1"]
            order_depth.buy_orders[row["bid_price_2"]] = row["bid_volume_2"]
            order_depth.buy_orders[row["bid_price_3"]] = row["bid_volume_3"]
            order_depth.sell_orders[row["ask_price_1"]] = -row["ask_volume_1"]
            order_depth.sell_orders[row["ask_price_2"]] = -row["ask_volume_2"]
            order_depth.sell_orders[row["ask_price_3"]] = -row["ask_volume_3"]

            self.listings[product] = listing
            self.order_depths[product] = order_depth
            self.own_trades[product] = []
            self.market_trades[product] = []
            self.position[product] = 0
            self.observations[product] = Observation({product: row["mid_price"]}, {product: ConversionObservation(0, 0, 0, 0, 0, 0, 0)})

        # Enter the required data into the TradingState object
        state = TradingState(
            "SAMPLE",
            timestamp,
            self.listings,
            self.order_depths,
            self.own_trades,
            self.market_trades,
            self.position,
            self.observations)

        return state

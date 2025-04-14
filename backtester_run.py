import datetime
import json
import pandas as pd
from collections import defaultdict
from typing import List, Dict, Any
import string
import jsonpickle
import numpy as np
import math
import io
from datamodel import Listing, ConversionObservation
from datamodel import TradingState, Listing, OrderDepth, Trade, Observation
from round2_justPB import Trader
from backtester import Backtester
import pandas as pd
import numpy as np
from typing import List, Dict, Any
import string
import jsonpickle
import numpy as np
import math

def _process_data_(file):
    with open(file, 'r') as file:
        log_content = file.read()
    sections = log_content.split('Sandbox logs:')[1].split('Activities log:')
    sandbox_log =  sections[0].strip()
    activities_log = sections[1].split('Trade History:')[0]
    # sandbox_log_list = [json.loads(line) for line in sandbox_log.split('\n')]
    trade_history =  json.loads(sections[1].split('Trade History:')[1])
    # sandbox_log_df = pd.DataFrame(sandbox_log_list)
    market_data_df = pd.read_csv(io.StringIO(activities_log), sep=";", header=0)
    trade_history_df = pd.json_normalize(trade_history)
    return market_data_df, trade_history_df

listings = {
    'RAINFOREST_RESIN': Listing(symbol='RAINFOREST_RESIN', product='RAINFOREST_RESIN', denomination='SEASHELLS'),
    'KELP': Listing(symbol='KELP', product='KELP', denomination='SEASHELLS'),
    'SQUID_INK': Listing(symbol='SQUID_INK', product='SQUID_INK', denomination='SEASHELLS'),
    'DJEMBES': Listing(symbol='DJEMBES', product='DJEMBES', denomination='SEASHELLS'),
    'JAMS': Listing(symbol='JAMS', product='JAMS', denomination='SEASHELLS'),
    'CROISSANTS': Listing(symbol='CROISSANTS', product='CROISSANTS', denomination='SEASHELLS'),
    'PICNIC_BASKET1': Listing(symbol='PICNIC_BASKET1', product='PICNIC_BASKET1', denomination='SEASHELLS'),
    'PICNIC_BASKET2': Listing(symbol='PICNIC_BASKET', product="PICNIC_BASKET", denomination="SEASHELLS"),
}

position_limit = {
    'RAINFOREST_RESIN': 50,
    'KELP': 50,
    'SQUID_INK': 50,
    'DJEMBES': 60,
    'JAMS': 350,
    'CROISSANTS': 250,
    'PICNIC_BASKET1': 60,
    'PICNIC_BASKET2': 100
}

fair_calculations = {
}

for i in range(1, 2):
    # with fair prediction
    day = i
    market_data = pd.read_csv(f"R2Data/prices_round_2_day_{day}.csv", sep=";", header=0)
    trade_history = pd.read_csv(f"R2Data/trades_round_2_day_{day}.csv", sep=";", header=0)

    trader = Trader()
    backtester = Backtester(trader, listings, position_limit, fair_calculations, market_data, trade_history, f"clean_data_logs/trade_history_day_{i}.log")
    backtester.run()
    print(backtester.pnl)
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Read the data
dfs = [pd.read_csv(f"prices_round_2_day_{i}.csv", sep=';') for i in range(-1, 2)]
df = pd.concat(dfs, ignore_index=True)
df['alltime'] = df['day'] * 1e6 + df['timestamp']
pivot = df.pivot(index='alltime', columns='product', values='mid_price').sort_index()

# Basket definitions
pivot['synthetic_A'] = pivot['DJEMBES'] + 3 * pivot['JAMS'] + 6 * pivot['CROISSANTS']
pivot['synthetic_B'] = 2 * pivot['JAMS'] + 4 * pivot['CROISSANTS']
pivot['basket_A'] = pivot['PICNIC_BASKET1']
pivot['basket_B'] = pivot['PICNIC_BASKET2']

# Spreads
pivot['spread_A'] = pivot['basket_A'] - pivot['synthetic_A']
pivot['spread_B'] = pivot['basket_B'] - pivot['synthetic_B']
pivot['spread_djembe'] = pivot['basket_A'] - 1.5 * pivot['basket_B'] - pivot['DJEMBES']

# Calculate z-scores
def calculate_z_score(series, window=3000):
    return (series - series.rolling(window=window).mean()) / series.rolling(window=window).std()

pivot['z_score_A'] = calculate_z_score(pivot['spread_A'])
pivot['z_score_B'] = calculate_z_score(pivot['spread_B'])
pivot['z_score_pair_spread'] = calculate_z_score(pivot['spread_djembe'])

# Normalize spreads to range [-1, 1]
def normalize(series):
    return (series - series.min()) / (series.max() - series.min()) * 4 - 2

pivot['norm_spread_A'] = normalize(pivot['spread_A'])
pivot['norm_spread_B'] = normalize(pivot['spread_B'])
pivot['norm_spread_djembe'] = normalize(pivot['spread_djembe'])

# Plots (existing ones)
plt.figure(figsize=(14, 12))

# 1. Basket A - 1.5 * Basket B vs Djembe
plt.subplot(4, 1, 1)
plt.plot(pivot.index, pivot['basket_A'] - 1.5 * pivot['basket_B'], label='Basket A - 1.5 * Basket B')
plt.plot(pivot.index, pivot['DJEMBES'], label='Djembe')
plt.legend()
plt.title("1. Basket A - 1.5 * Basket B vs Djembe")

# 2. Spread A vs Spread B
plt.subplot(4, 1, 2)
plt.plot(pivot.index, pivot['spread_A'], label='Spread A = Basket A - Synthetic A')
plt.plot(pivot.index, pivot['spread_B'], label='Spread B = Basket B - Synthetic B')
plt.axhline(0, color='gray', linestyle='--')
plt.legend()
plt.title("2. Spread A vs Spread B")

# 3. Z-scores for Spread A, Spread B, and Spread A - 1.5 * Basket B
plt.subplot(4, 1, 3)
plt.plot(pivot.index, pivot['z_score_A'], label='Z-score of Spread A')
plt.plot(pivot.index, pivot['z_score_B'], label='Z-score of Spread B')
plt.plot(pivot.index, pivot['z_score_pair_spread'], label='Z-score of Spread of Djembe')
plt.axhline(0, color='gray', linestyle='--')
plt.legend()
plt.title("3. Z-scores for Spread A, Spread B, and Spread of Djembe")

plt.tight_layout()
#plt.show()

# New plot for Spreads and Z-scores with respect to time
plt.figure(figsize=(14, 8))

# 1. Spread A vs Time (normalized)
plt.subplot(3, 1, 1)
plt.plot(pivot.index, pivot['norm_spread_A'], label='Normalized Spread A', color='blue')
plt.plot(pivot.index, pivot['z_score_A'], label='Z-score of Spread A', color='green')
plt.axhline(0, color='gray', linestyle='--')
plt.xlabel('Time')
plt.ylabel('Normalized Spread A / Z-score')
plt.title('Normalized Spread A = Basket A - Synthetic A')

# 2. Spread B vs Time (normalized)
plt.subplot(3, 1, 2)
plt.plot(pivot.index, pivot['norm_spread_B'], label='Normalized Spread B', color='blue')
plt.plot(pivot.index, pivot['z_score_B'], label='Z-score of Spread B', color='green')
plt.axhline(0, color='gray', linestyle='--')
plt.xlabel('Time')
plt.ylabel('Normalized Spread B / Z-score')
plt.title('Normalized Spread B = Basket B - Synthetic B')

# 3. Spread of Djembe vs Time (normalized)
plt.subplot(3, 1, 3)
plt.plot(pivot.index, pivot['norm_spread_djembe'], label='Normalized Spread of Djembe', color='blue')
plt.plot(pivot.index, pivot['z_score_pair_spread'], label='Z-score of Spread Djembe', color='green')
plt.axhline(0, color='gray', linestyle='--')
plt.xlabel('Time')
plt.ylabel('Normalized Spread Djembe / Z-score')
plt.title('Normalized Spread of Djembe = Basket A - 1.5 * Basket B - DJEMBES')

plt.tight_layout()
plt.show()

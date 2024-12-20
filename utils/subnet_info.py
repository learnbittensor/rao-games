import bittensor as bt
import pandas as pd
import matplotlib.pyplot as plt
import json
import numpy as np

def load_subnet_performances(filename='subnet_performances.json'):
    with open(filename, 'r') as f:
        return json.load(f)

def get_subnet_data():
    subtensor = bt.subtensor()
    subnets = subtensor.get_all_subnet_dynamic_info()

    data = []
    for subnet in subnets[1:]:
        emission_rate = float(subnet.emission)
        inflation_rate = (float(subnet.alpha_out) + 1000) / float(subnet.alpha_out) - 1 if float(subnet.alpha_out) != 0 else 0

        data.append({
            'Netuid': int(subnet.netuid),
            'TAO in pool': float(subnet.tao_in),
            'Alpha in pool': float(subnet.alpha_in),
            'Alpha outstanding': float(subnet.alpha_out),
            'Emission rate': emission_rate,
            'Inflation rate': inflation_rate,
            'Price': float(subnet.price)
        })

    return pd.DataFrame(data)

def plot_relative_difference(df):
    plt.figure(figsize=(12, 6))
    relative_diff = (df['Price'] - df['Emission rate']) / df['Emission rate']
    plt.bar(df['Netuid'], relative_diff)
    plt.title('Relative Difference between Emission and Price for Each Subnet')
    plt.xlabel('Subnet Netuid')
    plt.ylabel('Relative Difference')
    plt.savefig('relative_difference.png')
    plt.close()

def plot_price_difference_per_block(performances):
    plt.figure(figsize=(12, 6))
    price_diff = {}
    for netuid, data in performances.items():
        if len(data['prices']) > 1:
            diff = (data['prices'][-1] - data['prices'][0]) / len(data['prices'])
            price_diff[int(netuid)] = np.log(abs(diff)) if diff != 0 else 0

    plt.bar(price_diff.keys(), price_diff.values())
    plt.title('Price Difference per Block for Each Subnet')
    plt.xlabel('Subnet Netuid')
    plt.ylabel('Log of Price Difference per Block')
    plt.savefig('price_difference_per_block.png')
    plt.close()

def plot_price_drop_percentage(performances):
    plt.figure(figsize=(12, 6))
    price_drop = {}
    for netuid, data in performances.items():
        if len(data['prices']) > 1:
            drop = (data['prices'][-1] - data['prices'][0]) / data['prices'][0]
            price_drop[int(netuid)] = drop

    plt.bar(price_drop.keys(), price_drop.values())
    plt.title(f'Price Drop Percentage')
    plt.xlabel('Subnet Netuid')
    plt.ylabel('Price Drop Percentage')
    plt.savefig('price_drop_percentage.png')
    plt.close()

def plot_price_drop_and_inflation(df, performances):
    plt.figure(figsize=(12, 6))
    price_drop = {}
    for netuid, data in performances.items():
        if len(data['prices']) > 1:
            drop = (data['prices'][-1] - data['prices'][0]) / data['prices'][0]
            price_drop[int(netuid)] = drop

    x = df['Netuid']
    width = 0.35

    plt.bar(x - width/2, [price_drop.get(netuid, 0) for netuid in x], width, label='Price Drop Percentage', color='r')
    plt.bar(x + width/2, df['Inflation rate'], width, label='Inflation', color='b')

    plt.title(f'Price Drop Percentage and Inflation')
    plt.xlabel('Subnet Netuid')
    plt.ylabel('Percentage')
    plt.legend()
    plt.savefig('price_drop_and_inflation.png')
    plt.close()

def main():
    df = get_subnet_data()
    performances = load_subnet_performances()

    print(df)

    plot_relative_difference(df)
    plot_price_difference_per_block(performances)
    plot_price_drop_percentage(performances)
    plot_price_drop_and_inflation(df, performances)

if __name__ == "__main__":
    main()

import json
import bittensor as bt
from tabulate import tabulate

subtensor = None

def load_wallets(filename):
    with open(filename, 'r') as file:
        return json.load(file)

def get_wallet_info(coldkey_ss58):
    subnets = subtensor.get_all_subnet_dynamic_info()
    try:
        substakes = subtensor.get_stake_info_for_coldkeys(coldkey_ss58_list=[coldkey_ss58])[coldkey_ss58]
        free_balance = subtensor.get_balance(coldkey_ss58)
    except Exception as e:
        print(f"Error processing coldkey: {coldkey_ss58}")
        print(f"Error message: {str(e)}")
        return None

    total_tao = float(free_balance)
    subnet_stakes = {}

    for substake in substakes:
        subnet = subnets[substake.netuid]
        stake_float = float(substake.stake)
        price_float = float(subnet.price)
        stake_in_tao = stake_float * price_float
        total_tao += stake_in_tao
        subnet_stakes[substake.netuid] = stake_in_tao

    if subnet_stakes:
        most_stake_subnet = max(subnet_stakes, key=subnet_stakes.get)
        most_stake_percentage = (subnet_stakes[most_stake_subnet] / total_tao) * 100
        most_stake = f"Subnet {most_stake_subnet} ({most_stake_percentage:.2f}%)"
    else:
        most_stake = "No stakes"

    return total_tao, most_stake

def main():
    wallets = load_wallets('wallets.json')
    results = []

    for name, coldkey_ss58 in wallets.items():
        print(f"\nProcessing wallet: {name}")
        wallet_info = get_wallet_info(coldkey_ss58)
        if wallet_info is not None:
            total_tao, most_stake = wallet_info
            results.append([name, coldkey_ss58, total_tao, most_stake])

    results.sort(key=lambda x: x[2], reverse=True)

    headers = ["Name", "Coldkey Address", "Total TAO", "Most Stake"]
    table = tabulate(results, headers=headers, tablefmt="grid")

    print("\nWallet Balances (Sorted by Total TAO):")
    print(table)

if __name__ == "__main__":
    subtensor = bt.subtensor('rao')
    main()

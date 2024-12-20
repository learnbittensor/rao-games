import json
import re

def extract_wallets(data):
    pattern = r'(.*?)\s*—.*?\n(5[A-Za-z0-9]{47,48})'
    matches = re.findall(pattern, data, re.MULTILINE)
    return {name.strip(): wallet.strip() for name, wallet in matches}

with open('wallets.json', 'r') as f:
    existing_wallets = json.load(f)

with open('data.txt', 'r', encoding='utf-8') as f:
    data = f.read()

new_wallets = extract_wallets(data)

merged_wallets = {**new_wallets, **existing_wallets}

with open('wallets.json', 'w') as f:
    json.dump(merged_wallets, f, indent=4)

print(f"Updated wallets.json with {len(merged_wallets)} entries.")

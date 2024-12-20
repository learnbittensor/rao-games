import json
import os
from typing import Dict
from subnet_performance import SubnetPerformance

def save_performances(filename: str, performances: Dict[int, SubnetPerformance]):
    data = {netuid: {attr: getattr(perf, attr) for attr in ['emission_rates', 'prices']}
            for netuid, perf in performances.items()}
    with open(filename, 'w') as f:
        json.dump(data, f)

def load_performances(filename: str) -> Dict[int, SubnetPerformance]:
    performances = {}
    if not os.path.exists(filename) or os.stat(filename).st_size == 0:
        return performances
    with open(filename, 'r') as f:
        data = json.load(f)
    for netuid, perf_data in data.items():
        perf = SubnetPerformance()
        perf.emission_rates = perf_data.get('emission_rates', [])
        perf.prices = perf_data.get('prices', [])
        performances[int(netuid)] = perf
    return performances

import time
import traceback
from typing import List, Tuple, Dict
import bittensor as bt
from subnet_performance import SubnetPerformance
from swap_logic import SwapLogic
from utils import load_performances, save_performances

class ArbitrageBot:
    def __init__(self, config: bt.config):
        self.wallet = bt.wallet(config=config)
        self.subtensor = bt.subtensor(config=config)
        self.performances = load_performances('subnet_performances.json')
        self.profit_threshold = 0.001
        self.volatility_threshold = 0.05
        self.swap_logic = SwapLogic(self.subtensor, self.wallet)

    def run(self):
        while True:
            try:
                registered_subnets = self.swap_logic.check_subnet_registrations()
                current_global_tao = self.swap_logic.global_dynamic()
                bt.logging.info(f'Current Global TAO: {current_global_tao}')
                subnets = self.subtensor.get_all_subnet_dynamic_info()
                for subnet in subnets:
                    self.performances.setdefault(subnet.netuid, SubnetPerformance()).update(subnet)
                substakes = self.subtensor.get_stake_info_for_coldkeys(coldkey_ss58_list=[self.wallet.coldkeypub.ss58_address])[self.wallet.coldkeypub.ss58_address]
                staked_subnets = [substake.netuid for substake in substakes if float(substake.stake) > 0 and substake.netuid != 0]
                origin, dest, improvement, allows_negative = self.swap_logic.find_best_swap(registered_subnets, staked_subnets, self.performances)

                if improvement > self.profit_threshold or (allows_negative and improvement < 0):
                    self.swap_logic.swap(origin, dest)
                    new_global_tao = self.swap_logic.global_dynamic()
                    bt.logging.info(f'New Global TAO: {new_global_tao}, Improvement: {new_global_tao - current_global_tao}')
                else:
                    bt.logging.info(f'No profitable swap found. Best improvement: {improvement}')
                save_performances('subnet_performances.json', self.performances)
                #max_volatility = max(perf.volatility for perf in self.performances.values())
            except KeyboardInterrupt:
                break
            except Exception as e:
                bt.logging.error(f"An error occurred: {str(e)}")
                bt.logging.error(f"Full traceback: {traceback.format_exc()}")
                time.sleep(60)

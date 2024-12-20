from typing import List, Tuple, Dict
import bittensor as bt
from subnet_performance import SubnetPerformance
import numpy as np

class SwapLogic:
    def __init__(self, subtensor: bt.subtensor, wallet: bt.wallet):
        self.subtensor = subtensor
        self.wallet = wallet
        self.tolerance = 1e-6
        self.long_term_factor = 1.0
        self.emission_weight = 2.0
        self.price_emission_discrepancy_weight = 1.5
        self.inflation_weight = 1.2
        self.price_drop_weight = 1.0
        self.prediction_weight = 0.8
        self.slippage_weight = 1.5
        self.min_improvement_threshold = 0.001

    def swap(self, netuid_from: int, netuid_to: int) -> None:
        bt.logging.info(f"Swapping stake from subnet {netuid_from} to subnet {netuid_to}")
        call = self.subtensor.substrate.compose_call(
            call_module="SubtensorModule",
            call_function="move_stake",
            call_params={
                "origin_hotkey": "Enter SS58",
                "origin_netuid": netuid_from,
                "destination_hotkey": "Enter SS58",
                "destination_netuid": netuid_to,
                "amount_moved": 0,
            },
        )
        extrinsic = self.subtensor.substrate.create_signed_extrinsic(call=call, keypair=self.wallet.coldkey)
        self.subtensor.substrate.submit_extrinsic(extrinsic, wait_for_inclusion=False, wait_for_finalization=True)
        bt.logging.info("Swap completed")

    def global_dynamic(self) -> bt.Balance:
        subnets = self.subtensor.get_all_subnet_dynamic_info()
        substakes = self.subtensor.get_stake_info_for_coldkeys(coldkey_ss58_list=[self.wallet.coldkeypub.ss58_address])[self.wallet.coldkeypub.ss58_address]
        return sum(subnets[substake.netuid].tao_in * substake.stake / subnets[substake.netuid].alpha_out for substake in substakes)

    def check_subnet_registrations(self) -> List[int]:
        return [subnet.netuid for subnet in self.subtensor.get_all_subnet_dynamic_info()
                if self.subtensor.is_hotkey_registered(netuid=subnet.netuid, hotkey_ss58="Enter SS58")]

    def compute_swap_opportunity(self, subnet_a, subnet_b, stake_amount: bt.Balance, performance_a: SubnetPerformance, performance_b: SubnetPerformance) -> Tuple[float, bool, float]:
        if any(float(x) == 0 for x in [subnet_a.alpha_out, subnet_b.alpha_out, subnet_a.tao_in, subnet_b.tao_in]):
            return float('-inf'), False, 0

        is_valid, allows_negative = self.is_valid_swap(performance_a, performance_b)
        if not is_valid:
            return float('-inf'), False, 0

        global_tao_before = float(subnet_a.tao_in) * float(stake_amount) / float(subnet_a.alpha_out)
        received_amount_tao, slippage_a = subnet_a.alpha_to_tao_with_slippage(stake_amount)
        received_amount_destination, slippage_b = subnet_b.tao_to_alpha_with_slippage(received_amount_tao)
        global_tao_after = float(subnet_b.tao_in) * float(received_amount_destination) / float(subnet_b.alpha_out)
        global_tao_dif = global_tao_after - global_tao_before

        total_slippage = (float(slippage_a) + float(slippage_b)) / float(stake_amount)
        adjusted_improvement = self.calculate_adjusted_improvement(global_tao_dif, performance_a, performance_b, total_slippage)
        return adjusted_improvement, allows_negative, total_slippage

    def is_valid_swap(self, performance_a: SubnetPerformance, performance_b: SubnetPerformance) -> Tuple[bool, bool]:
        emission_a, price_a = performance_a.current_emission_rate, performance_a.current_price
        emission_b, price_b = performance_b.current_emission_rate, performance_b.current_price

        if emission_b <= price_b + self.tolerance:
            return False, False

        if price_a > emission_a + self.tolerance:
            return True, False

        if emission_a > price_a + self.tolerance and emission_b > price_b + self.tolerance:
            return True, True

        return False, False

    def calculate_adjusted_improvement(self, global_tao_dif: float, performance_a: SubnetPerformance, performance_b: SubnetPerformance, slippage: float) -> float:
        emission_diff = (performance_b.current_emission_rate - performance_a.current_emission_rate) * self.emission_weight
        price_emission_discrepancy_diff = ((performance_b.current_emission_rate - performance_b.current_price) -
                                           (performance_a.current_emission_rate - performance_a.current_price)) * self.price_emission_discrepancy_weight
        inflation_diff = (performance_b.inflation_rate - performance_a.inflation_rate) * self.inflation_weight
        price_drop_diff = (performance_a.price_drop_percentage - performance_b.price_drop_percentage) * self.price_drop_weight
        predicted_price_change_diff = (performance_b.predict_next_price() - performance_a.predict_next_price()) * self.prediction_weight

        slippage_factor = 1 - (slippage * self.slippage_weight)

        if performance_a.current_price > performance_a.current_emission_rate and performance_b.current_emission_rate > performance_b.current_price:
            return (global_tao_dif + emission_diff + price_emission_discrepancy_diff) * 2 * (1 + inflation_diff + price_drop_diff + predicted_price_change_diff) * slippage_factor

        return (global_tao_dif + emission_diff + price_emission_discrepancy_diff) * (1 + inflation_diff + price_drop_diff + predicted_price_change_diff) * slippage_factor

    def calculate_subnet_score(self, performance: SubnetPerformance) -> float:
        emission_score = performance.current_emission_rate * self.emission_weight
        price_emission_discrepancy = (performance.current_emission_rate - performance.current_price) * self.price_emission_discrepancy_weight
        inflation_score = performance.inflation_rate * self.inflation_weight
        price_drop_score = (1 - performance.price_drop_percentage) * self.price_drop_weight
        prediction_score = performance.predict_next_price() * self.prediction_weight

        return emission_score + price_emission_discrepancy + inflation_score + price_drop_score + prediction_score

    def find_best_swap(self, registered_subnets: List[int], staked_subnets: List[int], performances: Dict[int, SubnetPerformance]) -> Tuple[int, int, float, bool]:
        subnets = self.subtensor.get_all_subnet_dynamic_info()
        substakes = self.subtensor.get_stake_info_for_coldkeys(coldkey_ss58_list=[self.wallet.coldkeypub.ss58_address])[self.wallet.coldkeypub.ss58_address]
        stake_for_subnet = {substake.netuid: substake.stake for substake in substakes}
        best_swap = (0, 0, float('-inf'), False)

        subnet_scores = {netuid: self.calculate_subnet_score(performance) for netuid, performance in performances.items()}

        price_gt_emission_subnets = [a for a in staked_subnets if performances[a].current_price > performances[a].current_emission_rate]
        other_staked_subnets = [a for a in staked_subnets if a not in price_gt_emission_subnets]

        for a in price_gt_emission_subnets + other_staked_subnets:
            if a != 0:
                for b in registered_subnets:
                    if a != b:
                        performance_a, performance_b = performances[a], performances[b]
                        emission_a, price_a = performance_a.current_emission_rate, performance_a.current_price
                        emission_b, price_b = performance_b.current_emission_rate, performance_b.current_price

                        if price_b >= emission_b - self.tolerance:
                            continue

                        if emission_a > price_a + self.tolerance and emission_b > price_b + self.tolerance:
                            if (emission_b - price_b) <= (emission_a - price_a):
                                continue

                        improvement, allows_negative, slippage = self.compute_swap_opportunity(subnets[a], subnets[b], stake_for_subnet.get(a, bt.Balance(0)), performance_a, performance_b)

                        score_diff = subnet_scores[b] - subnet_scores[a]
                        adjusted_improvement = improvement + score_diff - (slippage * self.slippage_weight)

                        if price_a > emission_a and emission_b > price_b:
                            adjusted_improvement *= 2

                        if adjusted_improvement > best_swap[2] and adjusted_improvement > self.min_improvement_threshold:
                            best_swap = (a, b, adjusted_improvement, allows_negative)
                        elif allows_negative and adjusted_improvement > float('-inf') and adjusted_improvement > self.min_improvement_threshold:
                            best_swap = (a, b, adjusted_improvement, allows_negative)

        return best_swap

    def estimate_future_performance(self, performance: SubnetPerformance, blocks_ahead: int = 1000) -> float:
        future_price = performance.predict_next_price()
        future_emission = performance.current_emission_rate * (1 - performance.inflation_rate) ** (blocks_ahead / 100000)
        return (future_emission - future_price) / future_price

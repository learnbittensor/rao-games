import bittensor as bt

def confirm_action(message: str) -> bool:
    response = input(f"{message} (y/n): ").strip().lower()
    return response == 'y'

def stake_tao(wallet, subtensor, netuid, amount):
    if confirm_action(f"Do you want to stake {amount} TAO into subnet {netuid}?"):
        call = subtensor.substrate.compose_call(
            call_module="SubtensorModule",
            call_function="add_stake",
            call_params={
                "hotkey": wallet.hotkey.ss58_address,
                "netuid": netuid,
                "amount_staked": amount.rao,
            },
        )
        extrinsic = subtensor.substrate.create_signed_extrinsic(call=call, keypair=wallet.coldkey)
        subtensor.substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True, wait_for_finalization=True)
        bt.logging.info(f"Staked {amount} TAO into subnet {netuid}")

def unstake_alpha(wallet, subtensor, netuid, alpha_amount):
    if confirm_action(f"Do you want to unstake {alpha_amount} alpha from subnet {netuid}?"):
        call = subtensor.substrate.compose_call(
            call_module="SubtensorModule",
            call_function="remove_stake",
            call_params={
                "hotkey": wallet.hotkey.ss58_address,
                "netuid": netuid,
                "amount_unstaked": alpha_amount.rao,
            },
        )
        extrinsic = subtensor.substrate.create_signed_extrinsic(call=call, keypair=wallet.coldkey)
        subtensor.substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True, wait_for_finalization=True)
        bt.logging.info(f"Unstaked {alpha_amount} alpha from subnet {netuid}")

def get_stake_for_subnet(wallet, subtensor, netuid):
    stakes = subtensor.get_stake_info_for_coldkeys(coldkey_ss58_list=[wallet.coldkeypub.ss58_address])[wallet.coldkeypub.ss58_address]
    for stake in stakes:
        if stake.hotkey_ss58 == wallet.hotkey.ss58_address and stake.netuid == netuid:
            return stake.stake
    return bt.Balance(0)

def get_staked_subnets(wallet, subtensor):
    stakes = subtensor.get_stake_info_for_coldkeys(coldkey_ss58_list=[wallet.coldkeypub.ss58_address])[wallet.coldkeypub.ss58_address]
    return [stake.netuid for stake in stakes if stake.hotkey_ss58 == wallet.hotkey.ss58_address and float(stake.stake) > 0 and stake.netuid != 0]

def convert_alpha_to_tao(subtensor, netuid, alpha_amount):
    print(f"Alpha amount: {alpha_amount}")

    alpha_amount_float = float(alpha_amount) if isinstance(alpha_amount, bt.Balance) else alpha_amount

    exchange_rate = subtensor.get_subnet_dynamic_info(netuid).price
    print(f"Exchange rate: {exchange_rate}")

    tao_amount = alpha_amount_float * float(exchange_rate)
    print(f"TAO amount: {tao_amount}")

    return bt.Balance.from_tao(tao_amount)

def main():
    wallet = bt.wallet()
    subtensor = bt.subtensor()

    stake_tao(wallet, subtensor, netuid=5, amount=bt.Balance.from_tao(1))

    current_stake_alpha = get_stake_for_subnet(wallet, subtensor, netuid=5)
    bt.logging.info(f"Current stake in subnet 5: {current_stake_alpha}")

    alpha_to_unstake = current_stake_alpha / 2
    unstake_alpha(wallet, subtensor, netuid=5, alpha_amount=alpha_to_unstake)

    tao_to_stake = convert_alpha_to_tao(subtensor, netuid=5, alpha_amount=alpha_to_unstake)

    stake_tao(wallet, subtensor, netuid=18, amount=tao_to_stake)

if __name__ == "__main__":
    main()

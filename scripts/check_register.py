import bittensor as bt

def check_subnet_registrations(wallet):
    subtensor = bt.subtensor()

    subnets = subtensor.get_all_subnet_dynamic_info()

    print(f"Checking registrations for hotkey: {wallet.hotkey.ss58_address}")
    print("---------------------------------------------------")

    for subnet in subnets:
        netuid = subnet.netuid

        is_registered = subtensor.is_hotkey_registered(netuid=netuid, hotkey_ss58=wallet.hotkey.ss58_address)

        status = "Registered" if is_registered else "Not registered"
        print(f"Subnet {netuid}: {status}")

def main():
    wallet = bt.wallet(name="default")

    wallet.hotkey

    check_subnet_registrations(wallet)

if __name__ == "__main__":
    main()

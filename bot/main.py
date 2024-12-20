import argparse
import bittensor as bt
from arbitrage_bot import ArbitrageBot

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAO Bot")
    bt.wallet.add_args(parser)
    bt.subtensor.add_args(parser)
    bt.logging.add_args(parser)
    config = bt.config(parser)
    bot = ArbitrageBot(config)
    bot.run()

import pandas as pd
import numpy as np


import sys
from tokenize import tabsize
import driftpy
import pandas as pd 
import numpy as np 
pd.options.plotting.backend = "plotly"

# from driftpy.constants.config import configs
from anchorpy import Provider, Wallet
from solana.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from driftpy.clearing_house import ClearingHouse
from driftpy.accounts import get_perp_market_account, get_spot_market_account, get_user_account, get_state_account
from driftpy.constants.numeric_constants import * 
import os
import json
from driftpy.constants.banks import devnet_banks, Bank
from driftpy.constants.markets import devnet_markets, Market
from dataclasses import dataclass
from solana.publickey import PublicKey
from helpers import serialize_perp_market_2, serialize_spot_market
import asyncio

@dataclass
class Config:
    env: str
    pyth_oracle_mapping_address: PublicKey
    clearing_house_program_id: PublicKey
    usdc_mint_address: PublicKey
    markets: list[Market]
    banks: list[Bank]


configs = {
    "devnet": Config(
        env='devnet',
        pyth_oracle_mapping_address=PublicKey('BmA9Z6FjioHJPpjT39QazZyhDRUdZy2ezwx4GiDdE2u2'),
		clearing_house_program_id=PublicKey('dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH'),
		usdc_mint_address=PublicKey('8zGuJQqwhZafTah7Uc7Z4tXRnguqkn5KLFAP8oV6PHe2'),
		markets=devnet_markets,
		banks=devnet_banks,
    ),
    "mainnet-beta": Config(
        env='mainnet-beta',
        pyth_oracle_mapping_address=PublicKey('BmA9Z6FjioHJPpjT39QazZyhDRUdZy2ezwx4GiDdE2u2'),
		clearing_house_program_id=PublicKey('dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH'),
		usdc_mint_address=PublicKey('8zGuJQqwhZafTah7Uc7Z4tXRnguqkn5KLFAP8oV6PHe2'),
		markets=devnet_markets,
		banks=devnet_banks,
    )
}


async def load_and_save_data(pid='', url='https://api.mainnet-beta.solana.com'):
    config = configs['mainnet-beta']
    # print(config)
    # random key 
    with open("DRFTL7fm2cA13zHTSHnTKpt58uq5E49yr2vUxuonEtYd.json", 'r') as f: secret = json.load(f) 
    kp = Keypair.from_secret_key(bytes(secret))

    wallet = Wallet(kp)
    connection = AsyncClient(url)
    provider = Provider(connection, wallet)
    ch = ClearingHouse.from_config(config, provider)

    state = await get_state_account(ch.program)
    pd.Series(state.__dict__).to_csv("data/state.csv")

    mdfs = {}
    for i in range(state.number_of_markets):
        market = await get_perp_market_account(ch.program, i)
        market_name = ''.join(map(chr, market.name))
        print(market_name)
        mdfs[i] = serialize_perp_market_2(market).T

    pd.concat(mdfs, axis=1).to_csv("data/perp_markets.csv")


    smdfs = {}
    for i in range(state.number_of_spot_markets):
        market = await get_spot_market_account(ch.program, i)
        market_name = ''.join(map(chr, market.name))
        print(market_name)
        smdfs[i] = serialize_spot_market(market).T

    pd.concat(smdfs, axis=1).to_csv("data/spot_markets.csv")


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    url = os.environ['ANCHOR_PROVIDER_URL']
    loop.run_until_complete(load_and_save_data('', url))
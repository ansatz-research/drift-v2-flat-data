import pandas as pd
import numpy as np


import sys
from tokenize import tabsize
import driftpy
import pandas as pd 
import numpy as np 

pd.options.plotting.backend = "plotly"

print(driftpy.__dir__())
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

    all_users = await ch.program.account['User'].all()

    for user_account in all_users:
        uu = user_account.account.__dict__
        print(uu.keys())
        perps = pd.json_normalize([x.__dict__ for x in uu['perp_positions']])
        spots = pd.json_normalize([x.__dict__ for x in uu['spot_positions']])
        orders = pd.json_normalize([x.__dict__ for x in uu['orders']])
        ddf1 = pd.concat({'perp': perps, 'spot': spots, 'order': orders},axis=1).unstack().swaplevel(i=0,j=2).swaplevel(i=1,j=2)
        ddf1.index = [".".join([str(x) for x in col]).strip() for col in ddf1.index.values]
        ddf1 = ddf1.loc[[x for x in ddf1.index if '.padding' not in x]]
        # import pdb; pdb.set_trace()

        pd.json_normalize(uu)
        uu.pop('spot_positions')
        uu.pop('perp_positions')
        uu.pop('orders')
        uu.pop('name')
        uu.pop('padding')
        df_1 = pd.DataFrame(uu, index=list(range(8))).head(1) #todo show all positions
        df = pd.concat([df_1, pd.DataFrame(ddf1).sort_index().dropna().T],axis=1)
        df.T.to_csv("data/users/%s.csv" % str(user_account.public_key))




if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(load_and_save_data())
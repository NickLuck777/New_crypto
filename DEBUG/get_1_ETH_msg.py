from web3 import Web3, HTTPProvider
from web3.types import AccessList
import json
from hexbytes import HexBytes
from transform_md import transform_eth_trx
import pandas as pd

def hex_encode_binary_keys(d):
    for key, value in d.items():
        if value is None:
            if key in ["blockNumber", "gas", "nonce", "chainId", "maxFeePerGas", "maxPriorityFeePerGas", "value", "transactionIndex", "type", "v", "yParity"]:
                d[key] = 0  # Explicitly set 0 for INT64/INT32 fields
            else:
                d[key] = ""  # For string fields, if needed
        elif isinstance(value, HexBytes):  # Handle HexBytes
            d[key] = value.hex()
        elif isinstance(value, bytes):
            d[key] = value.hex()
        elif isinstance(value, dict):
            hex_encode_binary_keys(value)
        elif isinstance(value, list):  # Add list processing
            for entry in value:
                if isinstance(entry, HexBytes):
                    d[key].append(entry.hex())
                elif isinstance(entry, type(AccessList)):
                    hex_encode_binary_keys(entry)  #entry
                else:
                    d[key].append(entry)

    return d

x = 0

while x <= 10:
    w3 = Web3(HTTPProvider("https://eth-mainnet.g.alchemy.com/v2/2wrUporcMxcIMvRrpuVaBYWFmeh_Mo7y"))
    last_block_number = w3.eth.get_block_number()

    trx = w3.eth.get_transaction_by_block(last_block_number, 0)
    trx = dict(trx)
    trx['accessList'] = None
    # print(trx)
    hex_encode_binary_keys(trx)
    print(json.dumps(transform_eth_trx([trx]), indent=4))
    x += 1
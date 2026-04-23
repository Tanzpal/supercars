"""
deploy_contract.py
------------------
Compiles and deploys FractionalOwnership.sol to a running Ganache instance.
Run this ONCE to get the contract address, which is saved to contract_address.txt.

Usage:
    cd d:\antigravity project\supercars
    python blockchain/deploy_contract.py
"""

import json
import os
import sys

# Install py-solc-x if not already installed
try:
    from solcx import compile_standard, install_solc
except ImportError:
    print("Installing py-solc-x...")
    os.system("pip install py-solc-x")
    from solcx import compile_standard, install_solc

from web3 import Web3

# -----------------------------------------------
# 1. Connect to Ganache
# -----------------------------------------------
GANACHE_URL = "http://127.0.0.1:8545"
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))

if not w3.is_connected():
    print("ERROR: Cannot connect to Ganache. Make sure ganache is running at 127.0.0.1:8545")
    sys.exit(1)

print(f"Connected to Ganache. Accounts available: {len(w3.eth.accounts)}")
deployer = w3.eth.accounts[0]
print(f"Deploying from account: {deployer}")

# -----------------------------------------------
# 2. Install Solidity Compiler
# -----------------------------------------------
SOLC_VERSION = "0.8.0"
print(f"Installing solc v{SOLC_VERSION}...")
install_solc(SOLC_VERSION)
print("Solc installed.")

# -----------------------------------------------
# 3. Read the Solidity source
# -----------------------------------------------
base_dir = os.path.dirname(os.path.abspath(__file__))
sol_path = os.path.join(base_dir, "contracts", "FractionalOwnership.sol")

with open(sol_path, "r") as f:
    contract_source = f.read()

# -----------------------------------------------
# 4. Compile the contract
# -----------------------------------------------
print("Compiling FractionalOwnership.sol...")
compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {
            "FractionalOwnership.sol": {
                "content": contract_source
            }
        },
        "settings": {
            "outputSelection": {
                "*": {
                    "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
                }
            }
        },
    },
    solc_version=SOLC_VERSION,
)
print("Compilation successful.")

# -----------------------------------------------
# 5. Extract ABI and Bytecode
# -----------------------------------------------
contract_interface = compiled_sol["contracts"]["FractionalOwnership.sol"]["FractionalOwnership"]
abi = contract_interface["abi"]
bytecode = contract_interface["evm"]["bytecode"]["object"]

# Overwrite the ABI file with the freshly compiled version
abi_path = os.path.join(base_dir, "contract_abi.json")
with open(abi_path, "w") as f:
    json.dump(abi, f, indent=4)
print(f"ABI saved to: {abi_path}")

# -----------------------------------------------
# 6. Deploy the contract
# -----------------------------------------------
print("Deploying contract to Ganache...")
Contract = w3.eth.contract(abi=abi, bytecode=bytecode)

tx_hash = Contract.constructor().transact({"from": deployer, "gas": 3000000})
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

contract_address = tx_receipt.contractAddress
print(f"\nContract deployed successfully!")
print(f"Contract Address: {contract_address}")
print(f"Gas Used:         {tx_receipt.gasUsed}")

# -----------------------------------------------
# 7. Save the contract address for use in the app
# -----------------------------------------------
address_file = os.path.join(base_dir, "contract_address.txt")
with open(address_file, "w") as f:
    f.write(contract_address)

print(f"\nContract address saved to: {address_file}")
print("\nNext step: Run `python test_smart_contract.py` to verify on-chain transactions.")

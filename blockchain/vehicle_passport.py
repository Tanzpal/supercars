"""
Registers a newly verified car onto the blockchain.
Called by Flask when admin clicks 'Verify Car'.
"""

import time
from .web3_client import get_web3, get_contract, get_deployed_contract_address


def register_car_on_blockchain(car_id: int) -> dict:
    """
    Registers a car on the blockchain by recording an initial ownership event.
    Returns a dict with status and the blockchain_id (tx_hash used as the ID).
    """
    web3_instance = get_web3()
    contract_address = get_deployed_contract_address()

    if web3_instance and web3_instance.is_connected() and contract_address:
        try:
            contract = get_contract(contract_address)
            deployer = web3_instance.eth.accounts[0]

            # We record 0 shares for the car as a registration event.
            # This sets up the car's mapping in the contract.
            # A 'registration' is simply a buyShares call with 0 shares by the platform.
            # Instead we emit a dedicated registration by buying 1 share for the platform account
            # (platform holds 1 token representing the car itself).
            tx_hash = contract.functions.buyShares(car_id, 1).transact({
                'from': deployer,
                'gas': 200000
            })
            receipt = web3_instance.eth.wait_for_transaction_receipt(tx_hash)

            blockchain_id = receipt.transactionHash.hex()

            return {
                "status": "success",
                "blockchain_id": blockchain_id,
                "message": f"Car ID {car_id} registered on blockchain."
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Blockchain registration failed: {str(e)}"
            }
    else:
        # Mock fallback for development without Ganache
        mock_id = f"mock_register_{car_id}_{int(time.time())}"
        return {
            "status": "success",
            "blockchain_id": mock_id,
            "message": f"Car ID {car_id} registered (mocked)."
        }

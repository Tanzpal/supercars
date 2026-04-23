import time
from .web3_client import get_web3, get_contract, get_deployed_contract_address

def buy_shares(car_id: int, user_address: str, amount: int, contract_address: str = None) -> dict:
    """
    Buys shares on the blockchain if Web3 is available. 
    If not, it simulates the transaction for functional testing.
    """
    web3_instance = get_web3()
    
    # Auto-load contract address if not provided
    if not contract_address:
        contract_address = get_deployed_contract_address()
    
    if web3_instance and web3_instance.is_connected() and contract_address:
        try:
            contract = get_contract(contract_address)
            
            # Using the first account from Ganache as the default sender for demo purposes,
            # or require the user's private key to sign transactions. 
            # In a real app, you'd use raw transactions signed by the user's wallet.
            default_account = web3_instance.eth.accounts[0]
            
            # Estimate Gas
            tx_hash = contract.functions.buyShares(car_id, amount).transact({
                'from': default_account,
                'gas': 2000000
            })
            
            # Wait for receipt
            receipt = web3_instance.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                "status": "success",
                "tx_hash": receipt.transactionHash.hex(),
                "message": "Shares purchased successfully on blockchain."
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Blockchain transaction failed: {str(e)}"
            }
    else:
        # Mocking for local development without Ganache
        return {
            "status": "success",
            "tx_hash": f"mock_tx_{int(time.time())}",
            "message": "Shares purchased successfully (Mocked)."
        }

def get_ownership_status(car_id: int, contract_address: str = None) -> dict:
    """
    Retrieves total shares distributed for a car.
    """
    web3_instance = get_web3()
    
    # Auto-load contract address if not provided
    if not contract_address:
        contract_address = get_deployed_contract_address()
    
    if web3_instance and web3_instance.is_connected() and contract_address:
        try:
            contract = get_contract(contract_address)
            total = contract.functions.totalShares(car_id).call()
            return {
                "status": "success",
                "total_shares": total
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to fetch data from blockchain: {str(e)}"
            }
    else:
        # Mocking for local development
        return {
            "status": "success",
            "total_shares": 0, # Should be fetched from DB
            "message": "Using mock data."
        }

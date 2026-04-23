import os
import sys

# Ensure imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from blockchain.ownership_contract import buy_shares, get_ownership_status
from blockchain.web3_client import get_web3

def test_smart_contract_logic():
    print("=== Testing Smart Contract Logic ===")
    
    web3_instance = get_web3()
    if web3_instance and web3_instance.is_connected():
        print(f"Connected to Web3 provider at {web3_instance.provider.endpoint_uri}")
    else:
        print("No Web3 provider found. Using mock/fallback logic.")
        print("To test actual Web3, start Ganache (e.g., ganache-cli) at 127.0.0.1:8545.")

    car_id = 1
    user_address = "user@example.com" # Just a dummy identifier for logging
    shares_to_buy = 15
    
    print(f"\n1. Fetching initial ownership status for Car ID: {car_id}...")
    initial_status = get_ownership_status(car_id)
    print("Initial Status:", initial_status)

    print(f"\n2. Buying {shares_to_buy} shares for {user_address}...")
    buy_result = buy_shares(car_id, user_address, shares_to_buy)
    print("Buy Result:", buy_result)

    print(f"\n3. Fetching updated ownership status for Car ID: {car_id}...")
    updated_status = get_ownership_status(car_id)
    print("Updated Status:", updated_status)

if __name__ == "__main__":
    test_smart_contract_logic()

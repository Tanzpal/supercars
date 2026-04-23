// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract FractionalOwnership {
    // carId => (ownerAddress => shares)
    mapping(uint256 => mapping(address => uint256)) public ownershipShares;
    // carId => totalShares
    mapping(uint256 => uint256) public totalShares;

    event SharesPurchased(uint256 indexed carId, address indexed buyer, uint256 amount);

    // Buy shares for a specific car
    function buyShares(uint256 carId, uint256 amount) public payable {
        require(amount > 0, "Amount must be greater than 0");
        
        // In a real scenario, we would check msg.value against a share price.
        // For simplicity, we are just minting the shares for the user.

        ownershipShares[carId][msg.sender] += amount;
        totalShares[carId] += amount;

        emit SharesPurchased(carId, msg.sender, amount);
    }

    // Get shares owned by a specific address for a car
    function getShares(uint256 carId, address owner) public view returns (uint256) {
        return ownershipShares[carId][owner];
    }
}

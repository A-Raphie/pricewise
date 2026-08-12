// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/// @title InvoiceToken
/// @notice Minimal ERC-20 stand-in for a tokenized invoice, so Pricewise's
///         "act" step has a real token to quote/swap on the OKX DEX. 6 decimals.
contract InvoiceToken is ERC20, Ownable {
    uint8 private constant DECIMALS = 6;

    constructor(string memory name, string memory symbol) ERC20(name, symbol) Ownable(msg.sender) {}

    function decimals() public pure override returns (uint8) {
        return DECIMALS;
    }

    /// @notice Mint invoice tokens (demo liquidity). Owner only.
    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }
}

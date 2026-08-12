// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {Script, console2} from "forge-std/Script.sol";
import {ValuationRegistry} from "../src/ValuationRegistry.sol";

/// @notice Deploys ValuationRegistry to X Layer (testnet chain 195 / mainnet 196).
/// @dev Requires env: DEPLOYER_PRIVATE_KEY (funded), APPRAISER_ADDRESS (the agent wallet).
contract DeployValuationRegistry is Script {
    function run() external returns (ValuationRegistry registry) {
        address appraiser = vm.envAddress("APPRAISER_ADDRESS");
        uint256 pk = vm.envUint("DEPLOYER_PRIVATE_KEY");

        vm.startBroadcast(pk);
        registry = new ValuationRegistry(appraiser);
        vm.stopBroadcast();

        console2.log("ValuationRegistry deployed at:", address(registry));
        console2.log("Appraiser:", appraiser);
    }
}

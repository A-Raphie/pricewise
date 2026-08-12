// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {Test, console2} from "forge-std/Test.sol";
import {ValuationRegistry} from "../src/ValuationRegistry.sol";

contract ValuationRegistryTest is Test {
    ValuationRegistry internal reg;

    address internal deployer = address(this);
    address internal appraiser = address(0xA77);
    address internal other = address(0xBAD);

    bytes32 internal constant ASSET = keccak256("invoice-001");
    bytes32 internal constant REASON = keccak256("debtor-tier-A, term-30d, comps-3");

    function setUp() public {
        reg = new ValuationRegistry(appraiser);
    }

    // --- helpers ---
    function _attestAs(address who, bytes32 id, uint96 fv, uint16 conf) internal {
        vm.prank(who);
        reg.attest(id, fv, conf, REASON);
    }

    // 1. Happy path: appraiser attests, fields are stored.
    function test_AttestStoresFields() public {
        vm.prank(appraiser);
        reg.attest(ASSET, 95_000e6, 8200, REASON);

        ValuationRegistry.Attestation memory a = reg.getLatest(ASSET);
        assertEq(uint256(a.fairValue), 95_000e6);
        assertEq(uint256(a.confidenceBps), 8200);
        assertEq(a.appraiser, appraiser);
        assertEq(a.reasoningHash, REASON);
        assertGt(a.timestamp, 0);
    }

    // 2. Never-set asset returns a zeroed struct (timestamp == 0 sentinel).
    function test_NeverAttestedIsZeroed() public {
        ValuationRegistry.Attestation memory a = reg.getLatest(keccak256("nope"));
        assertEq(uint256(a.fairValue), 0);
        assertEq(a.confidenceBps, 0);
        assertEq(a.appraiser, address(0));
        assertEq(a.timestamp, 0);
    }

    // 3. Non-appraiser cannot attest.
    function test_RevertIfNotAppraiser() public {
        vm.expectRevert();
        vm.prank(other);
        reg.attest(ASSET, 1e6, 5000, REASON);
    }

    // 4. Zero assetId rejected.
    function test_RevertIfZeroAssetId() public {
        vm.prank(appraiser);
        vm.expectRevert(ValuationRegistry.ZeroAssetId.selector);
        reg.attest(bytes32(0), 1e6, 5000, REASON);
    }

    // 5. Zero fairValue rejected.
    function test_RevertIfZeroFairValue() public {
        vm.prank(appraiser);
        vm.expectRevert(ValuationRegistry.ZeroFairValue.selector);
        reg.attest(ASSET, 0, 5000, REASON);
    }

    // 6. confidenceBps above 10000 rejected.
    function test_RevertIfConfidenceTooHigh() public {
        vm.prank(appraiser);
        vm.expectRevert(ValuationRegistry.ConfidenceOutOfRange.selector);
        reg.attest(ASSET, 1e6, 10001, REASON);
    }

    // 7. Boundary: confidenceBps == 10000 accepted.
    function test_AcceptConfidence10000() public {
        _attestAs(appraiser, ASSET, 1e6, 10000);
        assertEq(reg.getLatest(ASSET).confidenceBps, 10000);
    }

    // 8. Boundary: confidenceBps == 0 accepted (floor enforced offchain).
    function test_AcceptConfidenceZero() public {
        _attestAs(appraiser, ASSET, 1e6, 0);
        assertEq(reg.getLatest(ASSET).confidenceBps, 0);
    }

    // 9. Overwrite updates fields, appraiser, and timestamp.
    function test_OverwriteUpdatesAll() public {
        _attestAs(appraiser, ASSET, 90_000e6, 6000);
        uint40 ts0 = reg.getLatest(ASSET).timestamp;

        vm.warp(block.timestamp + 100);
        address appraiser2 = address(0xA78);
        reg.grantRole(reg.APPRAISER_ROLE(), appraiser2); // test contract is DEFAULT_ADMIN

        vm.prank(appraiser2);
        reg.attest(ASSET, 95_000e6, 9000, keccak256("v2"));

        ValuationRegistry.Attestation memory a = reg.getLatest(ASSET);
        assertEq(uint256(a.fairValue), 95_000e6);
        assertEq(a.confidenceBps, 9000);
        assertEq(a.appraiser, appraiser2);
        assertGt(a.timestamp, ts0);
    }

    // 10. Attested event is emitted with the right args.
    function test_EmitsAttested() public {
        vm.expectEmit(true, true, false, true);
        emit ValuationRegistry.Attested(ASSET, 95_000e6, 8200, appraiser, uint40(block.timestamp), REASON);
        vm.prank(appraiser);
        reg.attest(ASSET, 95_000e6, 8200, REASON);
    }

    // 11. Admin can grant APPRAISER_ROLE; the new appraiser can attest.
    function test_AdminGrantsRole() public {
        address newbie = address(0xCE1);
        reg.grantRole(reg.APPRAISER_ROLE(), newbie); // test contract is DEFAULT_ADMIN

        vm.prank(newbie);
        reg.attest(ASSET, 1e6, 5000, REASON);
        assertEq(reg.getLatest(ASSET).appraiser, newbie);
    }

    // 12. The public mapping getter equals getLatest().
    function test_PublicGetterMatchesGetLatest() public {
        _attestAs(appraiser, ASSET, 12_345e6, 7000);
        (uint96 fv,, address ap, uint40 ts,) = reg.attestations(ASSET);
        ValuationRegistry.Attestation memory b = reg.getLatest(ASSET);
        assertEq(uint256(fv), uint256(b.fairValue));
        assertEq(ap, b.appraiser);
        assertEq(ts, b.timestamp);
    }
}

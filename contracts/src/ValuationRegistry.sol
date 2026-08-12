// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";

/// @title ValuationRegistry
/// @notice Pricewise — stores AI-derived fair-value attestations for illiquid/private RWA.
/// @dev No funds are held. Only APPRAISER_ROLE wallets may write. Reads are open.
///
/// Storage invariant:
///   attestations[id].timestamp == 0  <=> never attested (fairValue 0, appraiser address(0)).
///   attestations[id].timestamp  > 0  => fairValue > 0, confidenceBps <= 10000, appraiser != address(0).
contract ValuationRegistry is AccessControl {
    /// @dev Holder may call attest().
    bytes32 public constant APPRAISER_ROLE = keccak256("APPRAISER_ROLE");

    struct Attestation {
        uint96 fairValue; // asset units (e.g. 6-dec, USDC-pegged). > 0 when set.
        uint16 confidenceBps; // 0..10000 (basis points).
        address appraiser; // msg.sender of the latest attest().
        uint40 timestamp; // block.timestamp of latest attest(); 0 == never set.
        bytes32 reasoningHash; // keccak256(reasoning) for integrity/display.
    }

    event Attested(
        bytes32 indexed assetId,
        uint96 fairValue,
        uint16 confidenceBps,
        address indexed appraiser,
        uint40 timestamp,
        bytes32 reasoningHash
    );

    error ZeroAssetId();
    error ZeroFairValue();
    error ConfidenceOutOfRange();

    mapping(bytes32 => Attestation) public attestations;

    /// @param initialAppraiser The agent wallet allowed to call attest().
    constructor(address initialAppraiser) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(APPRAISER_ROLE, initialAppraiser);
    }

    /// @notice Write (or overwrite) the attestation for `assetId`.
    /// @dev pre: caller has APPRAISER_ROLE; assetId != 0; fairValue > 0; confidenceBps <= 10000.
    ///      post: attestations[assetId] updated; Attested emitted. Preserves the storage invariant.
    function attest(bytes32 assetId, uint96 fairValue, uint16 confidenceBps, bytes32 reasoningHash)
        external
        onlyRole(APPRAISER_ROLE)
    {
        if (assetId == bytes32(0)) revert ZeroAssetId();
        if (fairValue == 0) revert ZeroFairValue();
        if (confidenceBps > 10000) revert ConfidenceOutOfRange();

        uint40 ts = uint40(block.timestamp);
        attestations[assetId] = Attestation({
            fairValue: fairValue,
            confidenceBps: confidenceBps,
            appraiser: msg.sender,
            timestamp: ts,
            reasoningHash: reasoningHash
        });

        emit Attested(assetId, fairValue, confidenceBps, msg.sender, ts, reasoningHash);
    }

    /// @notice Read the current attestation for `assetId`.
    /// @dev Returns a zeroed struct (timestamp == 0) if never attested.
    function getLatest(bytes32 assetId) external view returns (Attestation memory) {
        return attestations[assetId];
    }
}

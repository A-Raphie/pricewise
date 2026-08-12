import type { Abi } from 'viem'

/**
 * Subset of the ValuationRegistry ABI used by the SDK.
 * (attest, getLatest, APPRAISER_ROLE, Attested event.)
 */
export const VALUATION_REGISTRY_ABI = [
  {
    inputs: [
      { name: 'assetId', type: 'bytes32' },
      { name: 'fairValue', type: 'uint96' },
      { name: 'confidenceBps', type: 'uint16' },
      { name: 'reasoningHash', type: 'bytes32' },
    ],
    name: 'attest',
    outputs: [],
    stateMutability: 'nonpayable',
    type: 'function',
  },
  {
    inputs: [{ name: 'assetId', type: 'bytes32' }],
    name: 'getLatest',
    outputs: [
      {
        components: [
          { name: 'fairValue', type: 'uint96' },
          { name: 'confidenceBps', type: 'uint16' },
          { name: 'appraiser', type: 'address' },
          { name: 'timestamp', type: 'uint40' },
          { name: 'reasoningHash', type: 'bytes32' },
        ],
        name: '',
        type: 'tuple',
      },
    ],
    stateMutability: 'view',
    type: 'function',
  },
  {
    inputs: [],
    name: 'APPRAISER_ROLE',
    outputs: [{ name: '', type: 'bytes32' }],
    stateMutability: 'view',
    type: 'function',
  },
  {
    anonymous: false,
    inputs: [
      { indexed: true, name: 'assetId', type: 'bytes32' },
      { name: 'fairValue', type: 'uint96' },
      { name: 'confidenceBps', type: 'uint16' },
      { indexed: true, name: 'appraiser', type: 'address' },
      { name: 'timestamp', type: 'uint40' },
      { name: 'reasoningHash', type: 'bytes32' },
    ],
    name: 'Attested',
    type: 'event',
  },
] as const satisfies Abi

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { PublicClient, WalletClient } from 'viem'
import { assetId, detectMisprice, PricewiseClient } from '../src'

const TOKEN = '0x0000000000000000000000000000000000000001'
const fakePublic = { getChainId: async () => 195 } as unknown as PublicClient
const fakeWallet = {} as WalletClient

describe('assetId', () => {
  it('is deterministic for the same inputs', () => {
    expect(assetId(195, TOKEN, 'INV-1')).toBe(assetId(195, TOKEN, 'INV-1'))
  })
  it('differs when the invoice ref differs', () => {
    expect(assetId(195, TOKEN, 'INV-1')).not.toBe(assetId(195, TOKEN, 'INV-2'))
  })
})

describe('detectMisprice', () => {
  it('flags an underpriced ask with the right gap', () => {
    expect(detectMisprice(1_000_000n, 900_000n)).toEqual({ mispriced: true, gapBps: 1000n })
  })
  it('ignores an overpriced ask', () => {
    expect(detectMisprice(1_000_000n, 1_050_000n).mispriced).toBe(false)
  })
  it('is safe on zero inputs', () => {
    expect(detectMisprice(0n, 1n).mispriced).toBe(false)
  })
})

describe('PricewiseClient.appraise', () => {
  beforeEach(() => vi.unstubAllGlobals())

  it('parses the engine response and attaches the onchain assetId', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({
        ok: true,
        status: 200,
        json: async () => ({
          invoice_id: 'INV-1',
          fair_value: 24814.21,
          fair_value_asset_units: '24814212213',
          confidence_bps: 8000,
          annual_rate: 0.095,
          days_to_maturity: 30,
          reasoning: 'deterministic core',
          comps: [{ token: 't', price_usd: 0.985 }],
        }),
      })) as unknown as typeof fetch,
    )

    const c = new PricewiseClient({
      engineUrl: 'http://localhost:8000',
      registryAddress: '0x0000000000000000000000000000000000000002',
      invoiceTokenAddress: TOKEN,
      publicClient: fakePublic,
      walletClient: fakeWallet,
    })
    const v = await c.appraise({
      invoiceId: 'INV-1',
      faceValue: 25000,
      debtorTier: 'B',
      issueDate: '2026-08-12',
      dueDate: '2026-09-11',
    })
    expect(v.fairValueAssetUnits).toBe(24814212213n)
    expect(v.confidenceBps).toBe(8000)
    expect(v.assetId).toMatch(/^0x[0-9a-f]{64}$/)
  })
})

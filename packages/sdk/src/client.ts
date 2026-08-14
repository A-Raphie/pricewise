import { type Address, type Hash, type Hex, type PublicClient, type WalletClient, encodePacked, keccak256, stringToBytes } from 'viem'
import { VALUATION_REGISTRY_ABI } from './abi'

export interface InvoiceInput {
  invoiceId: string
  faceValue: number
  currency?: string
  debtorTier: string
  debtorSector?: string
  issueDate?: string // ISO date yyyy-mm-dd
  dueDate?: string
}

export interface ValuationResult {
  invoiceId: string
  fairValue: number
  fairValueAssetUnits: bigint
  confidenceBps: number
  annualRate: number
  daysToMaturity: number
  reasoning: string
  comps: Array<{ token: string; priceUsd: number; volume24h: number; liquidityUsd: number }>
  compsSource: 'live' | 'seeded'
  assetId: Hex
}

export interface PricewiseClientOptions {
  engineUrl: string
  registryAddress: Address
  invoiceTokenAddress: Address
  /** Required for getValue; for appraise if chainId is not set. */
  publicClient?: PublicClient
  /** Required for attest. */
  walletClient?: WalletClient
  /** Overrides publicClient.getChainId() for assetId derivation. */
  chainId?: number
}

/** Deterministic assetId = keccak256(encodePacked(chainId, tokenContract, invoiceRef)). */
export function assetId(chainId: number, token: Address, invoiceRef: string): Hex {
  return keccak256(encodePacked(['uint256', 'address', 'string'], [BigInt(chainId), token, invoiceRef]))
}

/** Is the invoice token underpriced on the DEX relative to attested fair value? */
export function detectMisprice(fairValue: bigint, dexAsk: bigint, thresholdBps = 500n) {
  if (fairValue <= 0n || dexAsk <= 0n) return { mispriced: false, gapBps: 0n }
  const gapBps = ((fairValue - dexAsk) * 10000n) / fairValue
  return { mispriced: gapBps >= thresholdBps, gapBps }
}

/** The Pricewise one-call client: appraise (engine) -> attest (X Layer) -> read. */
export class PricewiseClient {
  constructor(private readonly opts: PricewiseClientOptions) {}

  /** Call the valuation engine and attach the onchain assetId. */
  async appraise(invoice: InvoiceInput): Promise<ValuationResult> {
    const res = await fetch(`${this.opts.engineUrl}/appraise`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        invoice_id: invoice.invoiceId,
        face_value: invoice.faceValue,
        currency: invoice.currency ?? 'USD',
        debtor_tier: invoice.debtorTier,
        debtor_sector: invoice.debtorSector ?? 'stable',
        issue_date: invoice.issueDate,
        due_date: invoice.dueDate,
      }),
    })
    if (!res.ok) throw new Error(`engine responded ${res.status}`)
    const j: any = await res.json()
    const chainId = this.opts.chainId ?? (await this.opts.publicClient?.getChainId())
    if (chainId === undefined) throw new Error('chainId or publicClient is required to appraise')
    return {
      invoiceId: j.invoice_id,
      fairValue: j.fair_value,
      fairValueAssetUnits: BigInt(j.fair_value_asset_units),
      confidenceBps: j.confidence_bps,
      annualRate: j.annual_rate,
      daysToMaturity: j.days_to_maturity,
      reasoning: j.reasoning as string,
      comps: (j.comps ?? []).map((c: any) => ({
        token: c.token,
        priceUsd: c.price_usd,
        volume24h: c.volume_24h ?? 0,
        liquidityUsd: c.liquidity_usd ?? 0,
      })),
      compsSource: j.comps_source === 'live' ? 'live' : 'seeded',
      assetId: assetId(chainId, this.opts.invoiceTokenAddress, invoice.invoiceId),
    }
  }

  /** Write the attestation onchain (appraiser wallet must hold APPRAISER_ROLE). */
  async attest(v: ValuationResult): Promise<Hash> {
    const wc = this.opts.walletClient
    if (!wc) throw new Error('walletClient is required to attest')
    const reasoningHash = keccak256(stringToBytes(v.reasoning))
    return wc.writeContract({
      account: wc.account ?? null,
      chain: wc.chain ?? undefined,
      address: this.opts.registryAddress,
      abi: VALUATION_REGISTRY_ABI,
      functionName: 'attest',
      args: [v.assetId, v.fairValueAssetUnits, v.confidenceBps, reasoningHash],
    } as const)
  }

  /** Read the current attestation for an assetId (timestamp 0 == never attested). */
  async getValue(id: Hex) {
    const pc = this.opts.publicClient
    if (!pc) throw new Error('publicClient is required to read')
    return pc.readContract({
      address: this.opts.registryAddress,
      abi: VALUATION_REGISTRY_ABI,
      functionName: 'getLatest',
      args: [id],
    } as const)
  }
}

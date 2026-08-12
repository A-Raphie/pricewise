// End-to-end demo: appraise (engine) -> attest (anvil) -> read back -> detect misprice.
// Env: RPC_URL, CHAIN_ID, ENGINE_URL, REGISTRY_ADDRESS, INVOICE_TOKEN_ADDRESS, APPRAISER_PRIVATE_KEY
import { createPublicClient, createWalletClient, http } from 'viem'
import { privateKeyToAccount } from 'viem/accounts'
import { PricewiseClient, detectMisprice } from '../dist/index.js'

const RPC = process.env.RPC_URL || 'http://127.0.0.1:8545'
const CHAIN_ID = Number(process.env.CHAIN_ID || 31337)
const ENGINE = process.env.ENGINE_URL || 'http://localhost:8000'
const { REGISTRY_ADDRESS: REGISTRY, INVOICE_TOKEN_ADDRESS: TOKEN, APPRAISER_PRIVATE_KEY: APPRAISER_PK } = process.env

if (!REGISTRY || !TOKEN || !APPRAISER_PK) {
  console.error('set REGISTRY_ADDRESS, INVOICE_TOKEN_ADDRESS, APPRAISER_PRIVATE_KEY')
  process.exit(1)
}

const account = privateKeyToAccount(APPRAISER_PK)
const publicClient = createPublicClient({ transport: http(RPC) })
const walletClient = createWalletClient({ account, transport: http(RPC) })
const pc = new PricewiseClient({
  engineUrl: ENGINE,
  registryAddress: REGISTRY,
  invoiceTokenAddress: TOKEN,
  publicClient,
  walletClient,
  chainId: CHAIN_ID,
})

const invoice = {
  invoiceId: 'INV-DEMO-001',
  faceValue: 25000,
  debtorTier: 'B',
  debtorSector: 'stable',
  issueDate: '2026-08-12',
  dueDate: '2026-09-11',
}

console.log('1) appraise (engine) ->')
const v = await pc.appraise(invoice)
console.log(
  `   fairValue=${v.fairValue.toFixed(2)} (${v.fairValueAssetUnits} units @6dp)  conf=${v.confidenceBps}bps  assetId=${v.assetId}`,
)

console.log('2) attest onchain (anvil) ->')
const tx = await pc.attest(v)
console.log(`   tx=${tx}`)

const a = await pc.getValue(v.assetId)
const att = Array.isArray(a)
  ? { fairValue: a[0], confidenceBps: a[1], appraiser: a[2], timestamp: a[3] }
  : a
console.log('3) read back from registry ->')
console.log(
  `   fairValue=${att.fairValue} conf=${att.confidenceBps} appraiser=${att.appraiser} timestamp=${att.timestamp}`,
)

const ask = v.fairValueAssetUnits - (v.fairValueAssetUnits * 12n) / 100n // 12% below fair value
const m = detectMisprice(v.fairValueAssetUnits, ask)
console.log(`4) detect misprice: dexAsk=${ask} (12% below) -> mispriced=${m.mispriced} gap=${m.gapBps}bps`)
console.log('DONE')

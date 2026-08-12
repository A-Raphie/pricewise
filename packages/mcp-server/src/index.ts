#!/usr/bin/env node
/**
 * @pricewise/mcp-server — exposes Pricewise as agent tools over MCP (stdio).
 *
 * Tools: appraise_asset, get_valuation, list_recent_attestations,
 *         explain_valuation, attest_asset.
 *
 * Env: ENGINE_URL, REGISTRY_ADDRESS, INVOICE_TOKEN_ADDRESS, XLAYER_RPC,
 *      XLAYER_CHAIN_ID (default 195), APPRAISER_PRIVATE_KEY (for attest_asset).
 * Tools degrade gracefully and report what's unconfigured.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js'
import { createPublicClient, createWalletClient, http, parseAbiItem } from 'viem'
import { privateKeyToAccount } from 'viem/accounts'
import {
  PricewiseClient,
  assetId,
  detectMisprice,
  VALUATION_REGISTRY_ABI,
  type InvoiceInput,
} from '@pricewise/sdk'

const ENV = {
  engineUrl: process.env.ENGINE_URL || 'http://localhost:8000',
  registryAddress: process.env.REGISTRY_ADDRESS,
  invoiceTokenAddress: process.env.INVOICE_TOKEN_ADDRESS || '0x0000000000000000000000000000000000000000',
  rpc: process.env.XLAYER_RPC,
  chainId: Number(process.env.XLAYER_CHAIN_ID || 195),
  appraiserKey: process.env.APPRAISER_PRIVATE_KEY,
}

const ATTESTED_EVENT = parseAbiItem(
  'event Attested(bytes32 indexed assetId, uint96 fairValue, uint16 confidenceBps, address indexed appraiser, uint40 timestamp, bytes32 reasoningHash)',
)

function publicClient() {
  if (!ENV.rpc) return undefined
  return createPublicClient({ transport: http(ENV.rpc) })
}
function walletClient() {
  if (!ENV.appraiserKey || !ENV.rpc) return undefined
  return createWalletClient({ account: privateKeyToAccount(ENV.appraiserKey as `0x${string}`), transport: http(ENV.rpc) })
}
function sdk() {
  if (!ENV.registryAddress) throw new Error('REGISTRY_ADDRESS is not set')
  return new PricewiseClient({
    engineUrl: ENV.engineUrl,
    registryAddress: ENV.registryAddress as `0x${string}`,
    invoiceTokenAddress: ENV.invoiceTokenAddress as `0x${string}`,
    publicClient: publicClient(),
    walletClient: walletClient(),
    chainId: ENV.chainId,
  })
}

function invoiceFromArgs(a: any): InvoiceInput {
  return {
    invoiceId: String(a.invoice_id),
    faceValue: Number(a.face_value),
    debtorTier: String(a.debtor_tier ?? 'B'),
    debtorSector: a.debtor_sector,
    issueDate: a.issue_date,
    dueDate: a.due_date,
  }
}

function fmtAttestation(a: any): string {
  const fairValue = a[0]
  const confidenceBps = a[1]
  const appraiser = a[2]
  const timestamp = a[3]
  const reasoningHash = a[4]
  if (timestamp === 0) return 'no attestation (never set)'
  return JSON.stringify(
    { fairValue: String(fairValue), confidenceBps, appraiser, timestamp, reasoningHash },
    null,
    2,
  )
}

type ToolResult = { content: Array<{ type: 'text'; text: string }>; isError?: boolean }
function ok(text: string): ToolResult {
  return { content: [{ type: 'text', text }] }
}
function err(text: string): ToolResult {
  return { content: [{ type: 'text', text }], isError: true }
}

export async function handleCall(name: string, args: any): Promise<ToolResult> {
  try {
    switch (name) {
      case 'appraise_asset': {
        const v = await sdk().appraise(invoiceFromArgs(args))
        return ok(
          `Fair value: ${v.fairValue.toFixed(2)} (${v.fairValueAssetUnits} units @6dp)\n` +
            `Confidence: ${v.confidenceBps} bps\nAnnual rate: ${(v.annualRate * 100).toFixed(2)}%\n` +
            `Days to maturity: ${v.daysToMaturity}\nassetId: ${v.assetId}\nReasoning: ${v.reasoning}`,
        )
      }
      case 'get_valuation': {
        const id =
          (args.asset_id as `0x${string}`) ||
          assetId(ENV.chainId, ENV.invoiceTokenAddress as `0x${string}`, String(args.invoice_ref))
        const a = await sdk().getValue(id)
        return ok(`assetId ${id}\n${fmtAttestation(a)}`)
      }
      case 'list_recent_attestations': {
        const pc = publicClient()
        if (!pc || !ENV.registryAddress) return err('XLAYER_RPC and REGISTRY_ADDRESS required')
        const logs = await pc.getLogs({
          address: ENV.registryAddress as `0x${string}`,
          event: ATTESTED_EVENT,
          fromBlock: 0n,
          toBlock: 'latest',
        })
        const recent = logs.slice(-10).reverse()
        return ok(
          recent.length
            ? recent
                .map((l) => `${l.blockNumber}: asset ${l.args.assetId} fv=${l.args.fairValue} conf=${l.args.confidenceBps} by=${l.args.appraiser}`)
                .join('\n')
            : 'no attestations yet',
        )
      }
      case 'explain_valuation': {
        const a = await sdk().getValue(args.asset_id)
        const conf = (a as any)[1] as number
        const band = conf >= 7500 ? 'high' : conf >= 5000 ? 'medium' : 'low'
        return ok(`Attestation:\n${fmtAttestation(a)}\nConfidence band: ${band}.`)
      }
      case 'attest_asset': {
        const v = await sdk().appraise(invoiceFromArgs(args))
        if (v.confidenceBps < 2500) return err(`confidence ${v.confidenceBps} bps below 2500 floor; refusing to attest`)
        const tx = await sdk().attest(v)
        return ok(`Attested onchain. tx: ${tx}\nassetId: ${v.assetId}\nfairValue: ${v.fairValueAssetUnits} units`)
      }
      case 'detect_misprice': {
        const r = detectMisprice(BigInt(args.fair_value), BigInt(args.dex_ask))
        return ok(`mispriced=${r.mispriced} gapBps=${r.gapBps}`)
      }
      default:
        return err(`unknown tool: ${name}`)
    }
  } catch (e: any) {
    return err(String(e?.message ?? e))
  }
}

export const TOOLS = [
  {
    name: 'appraise_asset',
    description: 'Appraise an invoice/receivable via the Pricewise engine. Returns fair value, confidence, reasoning, assetId.',
    inputSchema: {
      type: 'object',
      properties: {
        invoice_id: { type: 'string' },
        face_value: { type: 'number' },
        debtor_tier: { type: 'string', enum: ['A', 'B', 'C', 'D'] },
        debtor_sector: { type: 'string' },
        issue_date: { type: 'string' },
        due_date: { type: 'string' },
      },
      required: ['invoice_id', 'face_value', 'debtor_tier'],
    },
  },
  {
    name: 'get_valuation',
    description: 'Read the latest onchain attestation by asset_id or invoice_ref.',
    inputSchema: {
      type: 'object',
      properties: { asset_id: { type: 'string' }, invoice_ref: { type: 'string' } },
    },
  },
  {
    name: 'list_recent_attestations',
    description: 'List the most recent onchain Attested events (up to 10).',
    inputSchema: { type: 'object', properties: {} },
  },
  {
    name: 'explain_valuation',
    description: 'Read an attestation and interpret its confidence band.',
    inputSchema: { type: 'object', properties: { asset_id: { type: 'string' } }, required: ['asset_id'] },
  },
  {
    name: 'attest_asset',
    description: 'Appraise then write the attestation onchain (needs APPRAISER_PRIVATE_KEY; respects the 2500 bps floor).',
    inputSchema: {
      type: 'object',
      properties: {
        invoice_id: { type: 'string' },
        face_value: { type: 'number' },
        debtor_tier: { type: 'string' },
        debtor_sector: { type: 'string' },
        issue_date: { type: 'string' },
        due_date: { type: 'string' },
      },
      required: ['invoice_id', 'face_value', 'debtor_tier'],
    },
  },
  {
    name: 'detect_misprice',
    description: 'Given attested fair_value and a DEX ask (asset units), report mispricing + gap in bps.',
    inputSchema: {
      type: 'object',
      properties: { fair_value: { type: 'string' }, dex_ask: { type: 'string' } },
      required: ['fair_value', 'dex_ask'],
    },
  },
] as const

const server = new Server({ name: 'pricewise-mcp', version: '0.1.0' }, { capabilities: { tools: {} } })

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS as any }))
server.setRequestHandler(CallToolRequestSchema, async (req) => handleCall(req.params.name, req.params.arguments ?? {}))

async function main() {
  const transport = new StdioServerTransport()
  await server.connect(transport)
}

// Run only when executed directly (not when imported by tests).
const invokedDirectly = (() => {
  try {
    return process.argv[1]?.endsWith('index.js') || process.argv[1]?.endsWith('mcp-server/dist/index.js')
  } catch {
    return false
  }
})()
if (invokedDirectly) main().catch((e) => {
  console.error('[pricewise-mcp]', e)
  process.exit(1)
})

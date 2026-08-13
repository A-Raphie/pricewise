import { useState } from 'react'
import { createPublicClient, createWalletClient, http } from 'viem'
import { privateKeyToAccount } from 'viem/accounts'
import { PricewiseClient, detectMisprice, type ValuationResult } from '@pricewise/sdk'

const LS = 'pricewise.config'
const loadConfig = () => {
  try {
    return JSON.parse(localStorage.getItem(LS) || '{}')
  } catch {
    return {}
  }
}

export default function App() {
  const initial = {
    engineUrl: import.meta.env.DEV ? 'http://localhost:8000' : '',
    rpc: 'https://testrpc.xlayer.tech',
    chainId: '1952',
    registry: '0xB50eCDE9c94AaFBAF8aaC1e337B2c694223e4E79',
    token: '0x0000000000000000000000000000000000000000',
    appraiserKey: '',
    ...loadConfig(),
  }
  const [cfg, setCfg] = useState(initial)
  const saveCfg = (c: typeof cfg) => {
    setCfg(c)
    localStorage.setItem(LS, JSON.stringify(c))
  }

  const [inv, setInv] = useState({
    invoiceId: 'INV-DEMO-001',
    faceValue: '25000',
    debtorTier: 'B',
    debtorSector: 'stable',
    issueDate: '2026-08-12',
    dueDate: '2026-09-11',
  })
  const [val, setVal] = useState<ValuationResult | null>(null)
  const [tx, setTx] = useState<string | null>(null)
  const [ask, setAsk] = useState('')
  const [busy, setBusy] = useState('')
  const [err, setErr] = useState('')

  const client = () => {
    if (!cfg.registry || !cfg.token) throw new Error('Set registry + invoice token addresses in Config.')
    const account = cfg.appraiserKey ? privateKeyToAccount(cfg.appraiserKey as `0x${string}`) : undefined
    return new PricewiseClient({
      engineUrl: cfg.engineUrl,
      registryAddress: cfg.registry as `0x${string}`,
      invoiceTokenAddress: cfg.token as `0x${string}`,
      chainId: Number(cfg.chainId),
      publicClient: createPublicClient({ transport: http(cfg.rpc) }),
      walletClient: account
        ? createWalletClient({ account, transport: http(cfg.rpc) })
        : undefined,
    })
  }

  const appraise = async () => {
    setErr(''); setTx(null); setBusy('appraise')
    try {
      const v = await client().appraise({
        invoiceId: inv.invoiceId,
        faceValue: Number(inv.faceValue),
        debtorTier: inv.debtorTier,
        debtorSector: inv.debtorSector,
        issueDate: inv.issueDate,
        dueDate: inv.dueDate,
      })
      setVal(v)
    } catch (e: any) {
      setErr(e?.message ?? String(e))
    } finally {
      setBusy('')
    }
  }

  const attest = async () => {
    if (!val) return
    setErr(''); setBusy('attest')
    try {
      const hash = await client().attest(val)
      setTx(hash)
    } catch (e: any) {
      setErr(e?.message ?? String(e))
    } finally {
      setBusy('')
    }
  }

  const misprice =
    val && ask
      ? detectMisprice(val.fairValueAssetUnits, BigInt(Math.round(Number(ask) * 1_000_000)))
      : null

  const confBand = (b: number): [string, string] =>
    b >= 7500 ? ['high', 'good'] : b >= 5000 ? ['medium', ''] : ['low', 'bad']

  return (
    <div className="wrap">
      <h1>
        Pricewise <span className="tag">— AI RWA appraisal agent</span>
      </h1>
      <p className="sub">
        Appraise an invoice → attest fair value onchain → detect mispricing. The appraise→attest→act loop is the hero, not the LLM number.
      </p>

      <div className="grid">
        <div className="panel">
          <h2>Invoice</h2>
          <label>Invoice ID</label>
          <input value={inv.invoiceId} onChange={(e) => setInv({ ...inv, invoiceId: e.target.value })} />
          <div className="row">
            <div>
              <label>Face value (USD)</label>
              <input value={inv.faceValue} onChange={(e) => setInv({ ...inv, faceValue: e.target.value })} />
            </div>
            <div>
              <label>Debtor tier</label>
              <select value={inv.debtorTier} onChange={(e) => setInv({ ...inv, debtorTier: e.target.value })}>
                {['A', 'B', 'C', 'D'].map((t) => (
                  <option key={t}>{t}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="row">
            <div>
              <label>Issue date</label>
              <input value={inv.issueDate} onChange={(e) => setInv({ ...inv, issueDate: e.target.value })} />
            </div>
            <div>
              <label>Due date</label>
              <input value={inv.dueDate} onChange={(e) => setInv({ ...inv, dueDate: e.target.value })} />
            </div>
          </div>
          <button onClick={appraise} disabled={!!busy}>
            {busy === 'appraise' ? 'Appraising…' : '1) Appraise (engine)'}
          </button>

          <h2 style={{ marginTop: 20 }}>Config</h2>
          <label>Engine URL</label>
          <input value={cfg.engineUrl} onChange={(e) => saveCfg({ ...cfg, engineUrl: e.target.value })} />
          <label>RPC URL</label>
          <input value={cfg.rpc} onChange={(e) => saveCfg({ ...cfg, rpc: e.target.value })} />
          <div className="row">
            <div>
              <label>Chain ID</label>
              <input value={cfg.chainId} onChange={(e) => saveCfg({ ...cfg, chainId: e.target.value })} />
            </div>
          </div>
          <label>ValuationRegistry address</label>
          <input value={cfg.registry} onChange={(e) => saveCfg({ ...cfg, registry: e.target.value })} />
          <label>InvoiceToken address</label>
          <input value={cfg.token} onChange={(e) => saveCfg({ ...cfg, token: e.target.value })} />
          <label>Appraiser private key (anvil/testnet only)</label>
          <input value={cfg.appraiserKey} onChange={(e) => saveCfg({ ...cfg, appraiserKey: e.target.value })} />
        </div>

        <div className="panel">
          <h2>Valuation</h2>
          {!val ? (
            <p className="mut">Run an appraisal to see the AI-derived fair value, confidence, and reasoning.</p>
          ) : (
            <>
              <div className="big">${val.fairValue.toFixed(2)}</div>
              <div className="mut">fair value · {val.fairValueAssetUnits.toString()} units @6dp</div>
              <div className="kv">
                <span className="mut">Confidence</span>
                <span className={`pill ${confBand(val.confidenceBps)[1]}`}>
                  {val.confidenceBps} bps · {confBand(val.confidenceBps)[0]}
                </span>
              </div>
              <div className="kv">
                <span className="mut">Annual rate</span>
                <span>{(val.annualRate * 100).toFixed(2)}%</span>
              </div>
              <div className="kv">
                <span className="mut">Days to maturity</span>
                <span>{val.daysToMaturity}</span>
              </div>
              <div className="kv">
                <span className="mut">Comps</span>
                <span>{val.comps.length} on-chain</span>
              </div>
              <div className="reasoning">{val.reasoning}</div>

              <button onClick={attest} disabled={!!busy || !cfg.appraiserKey}>
                {busy === 'attest' ? 'Attesting…' : '2) Attest onchain'}
              </button>
              {tx && (
                <div className="kv" style={{ marginTop: 10 }}>
                  <span className="mut">attested</span>
                  <span className="pill good">tx {tx.slice(0, 10)}…</span>
                </div>
              )}

              <h2 style={{ marginTop: 20 }}>Detect misprice</h2>
              <label>DEX ask for this invoice (USD)</label>
              <input value={ask} onChange={(e) => setAsk(e.target.value)} placeholder="e.g. 22000" />
              {misprice && (
                <div className="kv">
                  <span className="mut">verdict</span>
                  <span className={`pill ${misprice.mispriced ? 'good' : 'bad'}`}>
                    {misprice.mispriced ? `MISPRICED · buy (gap ${misprice.gapBps} bps)` : 'fairly priced'}
                  </span>
                </div>
              )}
              <div className="mut" style={{ marginTop: 8, fontSize: 12 }}>
                assetId: {val.assetId}
              </div>
            </>
          )}
          {err && <div className="err">{err}</div>}
        </div>
      </div>
      <p className="mut" style={{ marginTop: 24, fontSize: 12 }}>
        Informational estimate only — not financial advice. Deterministic core; LLM explains. © Pricewise
      </p>
    </div>
  )
}

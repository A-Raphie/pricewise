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
      walletClient: account ? createWalletClient({ account, transport: http(cfg.rpc) }) : undefined,
    })
  }

  const appraise = async () => {
    setErr('')
    setTx(null)
    setBusy('appraise')
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
    setErr('')
    setBusy('attest')
    try {
      const hash = await client().attest(val)
      setTx(hash)
    } catch (e: any) {
      setErr(e?.message ?? String(e))
    } finally {
      setBusy('')
    }
  }

  const misprice = val && ask ? detectMisprice(val.fairValueAssetUnits, BigInt(Math.round(Number(ask) * 1_000_000))) : null
  const confBand = (b: number): [string, string] =>
    b >= 7500 ? ['high', 'good'] : b >= 5000 ? ['medium', ''] : ['low', 'bad']
  const activeStep = !val ? 1 : !tx ? 2 : 3

  return (
    <div className="wrap">
      <header className="mast">
        <div className="word">
          Price<b>wise</b>
        </div>
        <div className="meta">
          AI appraisal · illiquid/private RWA
          <br />
          X Layer · <span className="live">live</span>
        </div>
      </header>

      <div className="kicker">
        <span className="lead">An active AI appraisal agent.</span> Oracles price liquid RWA — invoices have no
        price and no oracle. Appraise → attest onchain → act on mispricing.
      </div>

      <div className="steps" aria-label="appraise attest act loop">
        <div className={`step ${val ? 'done' : ''} ${activeStep === 1 ? 'active' : ''}`}>
          <span className="n">01</span> appraise
        </div>
        <div className={`step ${tx ? 'done' : ''} ${activeStep === 2 ? 'active' : ''}`}>
          <span className="n">02</span> attest
        </div>
        <div className={`step ${misprice ? 'done' : ''} ${activeStep === 3 ? 'active' : ''}`}>
          <span className="n">03</span> act
        </div>
      </div>

      <div className="grid">
        {/* LEFT: input + config */}
        <div className="col">
          <section className="card">
            <h2>Invoice — input</h2>
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
              {busy === 'appraise' ? 'Appraising…' : '01 — Appraise'}
            </button>
          </section>

          <section className="card">
            <h2>Config</h2>
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
          </section>
        </div>

        {/* RIGHT: proof cards */}
        <div className="col">
          <section className="card">
            <h2>Valuation — proof</h2>
            {!val ? (
              <p className="empty">Run an appraisal to mint a fair-value proof.</p>
            ) : (
              <>
                <div className="value">
                  <span className="cur">$</span>
                  {val.fairValue.toFixed(2)}
                </div>
                <div className="subline">
                  fair value · {val.fairValueAssetUnits.toString()} units @6dp · asset {val.assetId.slice(0, 10)}…
                </div>
                <div className="kv">
                  <span className="k">Confidence</span>
                  <span className={`pill ${confBand(val.confidenceBps)[1]}`}>
                    {val.confidenceBps} bps · {confBand(val.confidenceBps)[0]}
                  </span>
                </div>
                <div className="kv">
                  <span className="k">Annual rate</span>
                  <span className="v">{(val.annualRate * 100).toFixed(2)}%</span>
                </div>
                <div className="kv">
                  <span className="k">Days to maturity</span>
                  <span className="v">{val.daysToMaturity}</span>
                </div>
                <div className="kv">
                  <span className="k">Comps</span>
                  <span className="v">{val.comps.length} on-chain</span>
                </div>
                <div className="reasoning">{val.reasoning}</div>
              </>
            )}
          </section>

          <section className="card">
            <h2>Attestation — onchain</h2>
            {!val ? (
              <p className="empty">Valuation required first.</p>
            ) : (
              <>
                <button onClick={attest} disabled={!!busy || !cfg.appraiserKey}>
                  {busy === 'attest' ? 'Attesting…' : '02 — Attest onchain'}
                </button>
                {tx && (
                  <div className="kv" style={{ marginTop: 14 }}>
                    <span className="k">attested</span>
                    <span className="pill good">tx {tx.slice(0, 10)}…</span>
                  </div>
                )}
                {!cfg.appraiserKey && (
                  <div className="subline">Add an appraiser key in Config to write the attestation.</div>
                )}
              </>
            )}
          </section>

          <section className="card">
            <h2>Act — detect misprice</h2>
            {!val ? (
              <p className="empty">Appraise first.</p>
            ) : (
              <>
                <label>DEX ask for this invoice (USD)</label>
                <input value={ask} onChange={(e) => setAsk(e.target.value)} placeholder="e.g. 22000" />
                {misprice && (
                  <div style={{ marginTop: 14 }}>
                    <div className={`verdict ${misprice.mispriced ? 'buy' : 'fair'}`}>
                      {misprice.mispriced ? `MISPRICED — buy (gap ${misprice.gapBps} bps)` : 'fairly priced'}
                    </div>
                    <div className="monoaddr">fair {val.fairValueAssetUnits.toString()} · ask {(Number(ask) * 1_000_000) | 0}</div>
                  </div>
                )}
              </>
            )}
            {err && <div className="err">{err}</div>}
          </section>
        </div>
      </div>

      <div className="foot">
        <span>Pricewise · informational estimate, not financial advice</span>
        <span>deterministic core · LLM explains</span>
      </div>
    </div>
  )
}

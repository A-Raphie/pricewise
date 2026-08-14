import { useState } from 'react'
import { createPublicClient, createWalletClient, http, custom, type Chain } from 'viem'
import { PricewiseClient, detectMisprice, type ValuationResult } from '@pricewise/sdk'

const LS = 'pricewise.config'
const loadConfig = () => {
  try {
    return JSON.parse(localStorage.getItem(LS) || '{}')
  } catch {
    return {}
  }
}

// viem has no built-in X Layer testnet chain · define it.
const xlayerTestnet: Chain = {
  id: 1952,
  name: 'X Layer Testnet',
  nativeCurrency: { name: 'OKB', symbol: 'OKB', decimals: 18 },
  rpcUrls: { default: { http: ['https://testrpc.xlayer.tech'] } },
  blockExplorers: { default: { name: 'OKLink', url: 'https://www.okx.com/explorer/xlayer-test' } },
  testnet: true,
}

const getProvider = (): any => (window as any).okxwallet ?? (window as any).ethereum

export default function App() {
  const initial = {
    engineUrl: import.meta.env.DEV ? 'http://localhost:8000' : '',
    rpc: 'https://testrpc.xlayer.tech',
    chainId: '1952',
    registry: '0xB50eCDE9c94AaFBAF8aaC1e337B2c694223e4E79',
    token: '0x0000000000000000000000000000000000000000',
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

  // wallet state
  const [walletAddr, setWalletAddr] = useState('')
  const [roleStatus, setRoleStatus] = useState<'' | 'requesting' | 'granted'>('')

  const engineOrigin = () => cfg.engineUrl || ''

  const client = () => {
    if (!cfg.registry || !cfg.token) throw new Error('Set registry + invoice token addresses in Config.')
    const provider = getProvider()
    const publicClient = createPublicClient({ transport: http(cfg.rpc) })
    const walletClient =
      walletAddr && provider
        ? createWalletClient({ account: walletAddr as `0x${string}`, chain: xlayerTestnet, transport: custom(provider) })
        : undefined
    return new PricewiseClient({
      engineUrl: cfg.engineUrl,
      registryAddress: cfg.registry as `0x${string}`,
      invoiceTokenAddress: cfg.token as `0x${string}`,
      chainId: Number(cfg.chainId),
      publicClient,
      walletClient,
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

  const ensureChain = async (provider: any) => {
    try {
      await provider.request({ method: 'wallet_switchEthereumChain', params: [{ chainId: '0x7A0' }] }) // 1952
    } catch (e: any) {
      if (e?.code === 4902) {
        await provider.request({
          method: 'wallet_addEthereumChain',
          params: [
            {
              chainId: '0x7A0',
              chainName: 'X Layer Testnet',
              nativeCurrency: { name: 'OKB', symbol: 'OKB', decimals: 18 },
              rpcUrls: ['https://testrpc.xlayer.tech'],
              blockExplorerUrls: ['https://www.okx.com/explorer/xlayer-test'],
            },
          ],
        })
      } else {
        throw e
      }
    }
  }

  const grantRole = async (addr: string) => {
    setRoleStatus('requesting')
    try {
      const r = await fetch(`${engineOrigin()}/grant-appraiser-role`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address: addr }),
      })
      const j = await r.json()
      if (!j.ok) {
        setErr('Role grant failed: ' + (j.error || 'unknown'))
        setRoleStatus('')
        return
      }
      // poll until the role read confirms (tx mined)
      for (let i = 0; i < 12; i++) {
        await new Promise((res) => setTimeout(res, 1500))
        const h = await fetch(`${engineOrigin()}/has-appraiser-role?address=${addr}`).then((x) => x.json())
        if (h.ok && h.hasRole) {
          setRoleStatus('granted')
          return
        }
      }
      setRoleStatus('granted') // tx mined; assume granted even if read lags
    } catch (e: any) {
      setErr('Role grant failed: ' + (e?.message || e))
      setRoleStatus('')
    }
  }

  const connect = async () => {
    setErr('')
    const provider = getProvider()
    if (!provider) {
      setErr('No wallet found. Install OKX Wallet or MetaMask.')
      return
    }
    try {
      const [addr] = await provider.request({ method: 'eth_requestAccounts' })
      await ensureChain(provider)
      setWalletAddr(addr)
      await grantRole(addr)
    } catch (e: any) {
      setErr('Connect failed: ' + (e?.message || e))
    }
  }

  const disconnect = () => {
    setWalletAddr('')
    setRoleStatus('')
  }

  const misprice = val && ask ? detectMisprice(val.fairValueAssetUnits, BigInt(Math.round(Number(ask) * 1_000_000))) : null
  const confBand = (b: number): [string, string] =>
    b >= 7500 ? ['high', 'good'] : b >= 5000 ? ['medium', ''] : ['low', 'bad']
  const pctPar = (n: number) => (n * 100).toFixed(2) + '%'
  const fmtVol = (n: number) => (n >= 1e6 ? (n / 1e6).toFixed(2) + 'M' : n >= 1e3 ? (n / 1e3).toFixed(1) + 'K' : n.toFixed(0))
  const confCells = Math.round((val?.confidenceBps ?? 0) / 1000)
  const activeStep = !val ? 1 : !tx ? 2 : 3

  return (
    <div className="wrap">
      <header className="mast">
        <div className="word">
          Price<b>wise</b>
        </div>
        <div className="wallet">
          {walletAddr ? (
            <>
              <span className="addr">
                {walletAddr.slice(0, 6)}…{walletAddr.slice(-4)}
              </span>
              {roleStatus === 'granted' && <span className="pill good">appraiser ✓</span>}
              {roleStatus === 'requesting' && <span className="pill">granting role…</span>}
              <button className="ghost sm" onClick={disconnect}>
                disconnect
              </button>
            </>
          ) : (
            <button className="walletbtn" onClick={connect}>
              Connect Wallet
            </button>
          )}
        </div>
      </header>

      <div className="kicker">
        <span className="lead">An active AI appraisal agent.</span> Oracles price liquid RWA · invoices have no
        price and no oracle. Appraise → attest onchain → act on mispricing.
      </div>

      <div className="strip">
        <span className="seg"><span className="live">live</span></span>
        <span className="seg">X Layer <b>{cfg.chainId}</b></span>
        <span className="seg">comps via <b>OKX DEX</b></span>
        <span className="seg">registry <b>{cfg.registry ? `${cfg.registry.slice(0, 6)}…${cfg.registry.slice(-4)}` : '·'}</b></span>
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
            <h2>Invoice · input</h2>
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
              {busy === 'appraise' ? 'Appraising…' : '01 · Appraise'}
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
          </section>
        </div>

        {/* RIGHT: proof cards */}
        <div className="col">
          <section className="card">
            <h2>Valuation · proof</h2>
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
                <div className="bar" aria-label={`confidence ${val.confidenceBps} basis points`}>
                  {Array.from({ length: 10 }).map((_, i) => (
                    <i key={i} className={i < confCells ? 'on' : ''} />
                  ))}
                </div>
                <div className="barlabel">
                  <span>confidence · {confBand(val.confidenceBps)[0]}</span>
                  <span className={`pill ${confBand(val.confidenceBps)[1]}`}>{val.confidenceBps} bps</span>
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
                  <span className="v">{val.comps.length} on-chain peers</span>
                </div>
                {val.comps.length > 0 && (
                  <table className="comps">
                    <caption>OKX DEX · comparable market data</caption>
                    <thead>
                      <tr>
                        <th>token</th>
                        <th className="num">px / par</th>
                        <th className="num">24h vol</th>
                        <th className="num">liquidity</th>
                      </tr>
                    </thead>
                    <tbody>
                      {val.comps.map((c) => (
                        <tr key={c.token}>
                          <td className="sym">{c.token}</td>
                          <td className="num">{pctPar(c.priceUsd)}</td>
                          <td className="num">${fmtVol(c.volume24h)}</td>
                          <td className="num">${fmtVol(c.liquidityUsd)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
                <div className="reasoning">{val.reasoning}</div>
              </>
            )}
          </section>

          <section className="card">
            <h2>Attestation · onchain</h2>
            {!val ? (
              <p className="empty">Valuation required first.</p>
            ) : (
              <>
                <button onClick={attest} disabled={!!busy || !walletAddr || roleStatus !== 'granted'}>
                  {busy === 'attest' ? 'Attesting…' : '02 · Attest onchain'}
                </button>
                {tx && (
                  <div className="kv" style={{ marginTop: 14 }}>
                    <span className="k">attested</span>
                    <a className="pill good" href={`https://www.okx.com/explorer/xlayer-test/tx/${tx}`} target="_blank" rel="noreferrer">
                      tx {tx.slice(0, 10)}…
                    </a>
                  </div>
                )}
                {!walletAddr && <div className="subline">Connect wallet to attest onchain.</div>}
                {walletAddr && roleStatus !== 'granted' && <div className="subline">Granting appraiser role…</div>}
                <a className="faucet" href="https://www.okx.com/xlayer/faucet" target="_blank" rel="noreferrer">
                  get testnet OKB for gas →
                </a>
              </>
            )}
          </section>

          <section className="card">
            <h2>Act · detect misprice</h2>
            {!val ? (
              <p className="empty">Appraise first.</p>
            ) : (
              <>
                <label>DEX ask for this invoice (USD)</label>
                <input value={ask} onChange={(e) => setAsk(e.target.value)} placeholder="e.g. 22000" />
                {misprice && (
                  <div style={{ marginTop: 14 }}>
                    <div className={`verdict ${misprice.mispriced ? 'buy' : 'fair'}`}>
                      {misprice.mispriced ? `MISPRICED · buy (gap ${misprice.gapBps} bps)` : 'fairly priced'}
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

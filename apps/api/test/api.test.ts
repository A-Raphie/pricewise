import { describe, it, expect } from 'vitest'
import app from '../src'

describe('pricewise-api', () => {
  it('GET /health -> 200', async () => {
    const r = await app.request('/health')
    expect(r.status).toBe(200)
    const j = await r.json()
    expect(j.ok).toBe(true)
  })

  it('POST /appraise without X-PAYMENT -> 402 (x402 gate)', async () => {
    const r = await app.request('/appraise', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ invoice_id: 'X', face_value: 1, debtor_tier: 'B' }),
    })
    expect(r.status).toBe(402)
    const j = await r.json()
    expect(j.scheme).toBe('x402')
    expect(j.error).toBe('payment_required')
  })
})

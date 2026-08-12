import { describe, it, expect } from 'vitest'
import { TOOLS, handleCall } from '../src'

describe('TOOLS', () => {
  it('exposes the expected agent tool set', () => {
    const names = TOOLS.map((t) => t.name)
    for (const n of ['appraise_asset', 'get_valuation', 'list_recent_attestations', 'explain_valuation', 'attest_asset', 'detect_misprice']) {
      expect(names).toContain(n)
    }
  })
})

describe('handleCall', () => {
  it('rejects an unknown tool', async () => {
    const r = await handleCall('nope', {})
    expect(r.isError).toBe(true)
  })

  it('detect_misprice is pure (works with no chain config)', async () => {
    const r = await handleCall('detect_misprice', { fair_value: '1000000', dex_ask: '900000' })
    expect(r.isError).toBeFalsy()
    expect(r.content[0].text).toContain('mispriced=true')
  })
})

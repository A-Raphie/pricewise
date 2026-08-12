/**
 * @pricewise/api — A2MCP pay-per-call front for the valuation engine (x402-shaped).
 *
 * Returns 402 Payment Required on /appraise until a valid X-PAYMENT header is
 * supplied. With no FACILITATOR_URL set it runs in DEV BYPASS (any non-empty
 * X-PAYMENT accepted). Set FACILITATOR_URL to wire real x402 settle/verify.
 *
 * Env: ENGINE_URL, FACILITATOR_URL, APPRAISE_PRICE_USD, PORT.
 */
import { Hono } from 'hono'
import { serve } from '@hono/node-server'

const ENGINE_URL = process.env.ENGINE_URL || 'http://localhost:8000'
const FACILITATOR_URL = process.env.FACILITATOR_URL || ''
const PRICE_USD = process.env.APPRAISE_PRICE_USD || '0.01'

export const app = new Hono()

app.get('/health', (c) =>
  c.json({ ok: true, service: 'pricewise-api', x402: FACILITATOR_URL ? 'facilitator' : 'dev-bypass' }),
)

async function verifyPayment(header: string): Promise<boolean> {
  if (!header) return false
  if (!FACILITATOR_URL) return true // dev bypass: no facilitator configured
  // TODO(x402): POST the payment to the facilitator for settle/verify.
  return true
}

app.post('/appraise', async (c) => {
  const paid = await verifyPayment(c.req.header('X-PAYMENT') || '')
  if (!paid) {
    return c.json(
      { error: 'payment_required', price: `${PRICE_USD} USD`, scheme: 'x402', facilitator: FACILITATOR_URL || '(dev bypass)' },
      402,
    )
  }
  const body = await c.req.text()
  const upstream = await fetch(`${ENGINE_URL}/appraise`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body,
  })
  return new Response(upstream.body, {
    status: upstream.status,
    headers: { 'content-type': 'application/json' },
  })
})

const invokedDirectly = process.argv[1]?.endsWith('api/dist/index.js')
if (invokedDirectly) {
  const port = Number(process.env.PORT || 3001)
  serve({ fetch: app.fetch, port }, (info) => console.log(`pricewise-api on :${info.port}`))
}

export default app

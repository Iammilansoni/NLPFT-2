// Records the product demo used in the README (docs/demo.gif).
//
// Drives the real app with Playwright and records a video. Captions and a
// visible cursor are drawn into the page so the GIF explains itself.
//
//   cd Frontend && node ../scripts/record_demo.mjs <out-dir>
//   python ../scripts/video_to_gif.py <out-dir>/<video>.webm ../docs/demo.gif
//
// Needs the stack running (docker compose up) with the demo tenant seeded.
// CHROME_EXE may point at a Chromium binary if Playwright's own isn't installed.

import { chromium } from 'playwright'

const BASE = process.env.DEMO_BASE_URL || 'http://localhost:3000'
const OUT = process.argv[2] || '.'
const SIZE = { width: 1280, height: 800 }

const overlay = () => {
  const install = () => {
    if (document.getElementById('__demo_cursor')) return
    const cursor = document.createElement('div')
    cursor.id = '__demo_cursor'
    Object.assign(cursor.style, {
      position: 'fixed', left: '-40px', top: '-40px', width: '18px', height: '18px', borderRadius: '50%',
      background: 'rgba(99,102,241,.35)', border: '2px solid rgba(79,70,229,.95)', zIndex: 2147483647,
      pointerEvents: 'none', transform: 'translate(-50%,-50%)', transition: 'width .12s, height .12s',
    })
    const caption = document.createElement('div')
    caption.id = '__demo_caption'
    Object.assign(caption.style, {
      position: 'fixed', left: '50%', top: '14px', transform: 'translateX(-50%)', maxWidth: '86%',
      padding: '10px 18px', borderRadius: '12px', background: 'rgba(15,23,42,.92)', color: '#fff',
      font: '600 17px/1.35 ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif',
      boxShadow: '0 8px 30px rgba(0,0,0,.35)', zIndex: 2147483646, pointerEvents: 'none',
      opacity: '0', transition: 'opacity .25s', textAlign: 'center',
    })
    document.documentElement.append(cursor, caption)
    document.addEventListener('mousemove', (e) => {
      cursor.style.left = `${e.clientX}px`
      cursor.style.top = `${e.clientY}px`
    }, true)
    document.addEventListener('mousedown', () => { cursor.style.width = cursor.style.height = '26px' }, true)
    document.addEventListener('mouseup', () => { cursor.style.width = cursor.style.height = '18px' }, true)
    // Keep the caption across client-side navigations.
    const saved = sessionStorage.getItem('__demo_caption')
    if (saved) { caption.textContent = saved; caption.style.opacity = '1' }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install)
  else install()
  // The first-visit guided tours would cover the product in a recording.
  try {
    const done = Object.fromEntries(['dashboard', 'templates', 'datasets', 'settings', 'query', 'audit'].map(t => [t, true]))
    localStorage.setItem('nlpforge_tour_completed', JSON.stringify(done))
  } catch {}
}

const browser = await chromium.launch({ executablePath: process.env.CHROME_EXE || undefined })
const context = await browser.newContext({ viewport: SIZE, recordVideo: { dir: OUT, size: SIZE } })
await context.addInitScript(overlay)
const page = await context.newPage()
const pause = (ms) => page.waitForTimeout(ms)

async function caption(text) {
  await page.evaluate((t) => {
    sessionStorage.setItem('__demo_caption', t)
    const el = document.getElementById('__demo_caption')
    if (el) { el.textContent = t; el.style.opacity = '1' }
  }, text)
}

async function moveTo(locator) {
  await locator.scrollIntoViewIfNeeded()
  const box = await locator.boundingBox()
  const x = box.x + box.width / 2
  const y = box.y + box.height / 2
  await page.mouse.move(x, y, { steps: 18 })
  return { x, y }
}

// Bring a part of the page into view the way a person scrolls: smoothly.
async function reveal(locator, block = 'center') {
  await locator.first().evaluate((el, b) => el.scrollIntoView({ behavior: 'smooth', block: b }), block)
  await pause(700)
}

async function click(locator) {
  const { x, y } = await moveTo(locator)
  await pause(150)
  await page.mouse.click(x, y)
}

async function skipTour() {
  const skip = page.getByRole('button', { name: /skip tour/i })
  if (await skip.isVisible().catch(() => false)) await skip.click()
}

async function ask(query) {
  const box = page.getByRole('textbox').first()
  await click(box)
  await box.fill('')
  await box.pressSequentially(query, { delay: 18 })
  await pause(250)
  await page.keyboard.press('Enter')
  await page.getByText('Extracted request body').waitFor({ timeout: 90000 })
  await pause(400)
}

// 1. Landing
await page.goto(BASE)
await caption('NLPForge: turn a plain-English request into a validated API call')
await page.mouse.move(640, 300)
await pause(1800)

// 2. One-click demo login
await click(page.getByRole('link', { name: /try the live demo/i }).first())
await caption('One click into the demo: 20 real API templates already indexed')
await page.getByRole('button', { name: /explore the live demo/i }).waitFor()
await pause(700)
await click(page.getByRole('button', { name: /explore the live demo/i }))
await page.waitForURL(/dashboard/, { timeout: 30000 })
await pause(1200)
await skipTour()

// 3. Routing + rule extraction
await caption('1. Routing: vector search picks the endpoint in about 100 ms')
await ask('Refund 25 dollars on order 8820 because it arrived broken')
await pause(1500)
await caption('2. Extraction: rules read the values straight from your text. No model call.')
await reveal(page.getByLabel('Where each value came from'))
await moveTo(page.getByLabel('Where each value came from'))
await pause(3000)

// 4. LLM only for the hard part, grounded
await reveal(page.getByRole('textbox'), 'start')
await caption('Harder phrasing: the local LLM fills the rest, and every value is checked against your text')
await ask('change my password from oldpass1 to NewPass#9')
await reveal(page.getByLabel('Where each value came from'))
await moveTo(page.getByLabel('Where each value came from'))
await pause(3000)

// 5. Missing values are reported, never invented
await reveal(page.getByRole('textbox'), 'start')
await caption('3. Never invents values: a missing email and password are reported, not made up')
await ask('log me in please')
await reveal(page.getByText(/Not used: the model suggested/))
await moveTo(page.getByText(/Not used: the model suggested/))
await pause(3400)

// 6. Any provider, models listed live
await caption('4. Any LLM from 20+ providers, local or cloud. Model lists come live from each provider.')
await page.goto(`${BASE}/settings?tab=llm-providers`)
await pause(900)
await skipTour()
await click(page.getByRole('button', { name: /add (provider|your first provider)/i }).first())
await page.getByRole('dialog').waitFor()
await pause(600)
await click(page.getByRole('dialog').getByRole('combobox').first())
await pause(900)
await click(page.getByRole('option', { name: /openrouter/i }))
await page.getByRole('listbox', { name: 'Models' }).waitFor({ timeout: 30000 })
await pause(900)
const freeOnly = page.getByRole('button', { name: 'Free only' })
if (await freeOnly.isVisible().catch(() => false)) await click(freeOnly)
await pause(2000)
await page.keyboard.press('Escape')
await pause(500)

// 7. Model catalogue
await caption('5. Model catalogue: new models appear on their own; ones a provider retires are phased out')
await click(page.getByText('Model catalogue', { exact: true }).first())
await page.getByText('Providers', { exact: true }).waitFor({ timeout: 30000 })
await pause(2800)

// 8. Per-user embedding model
await caption('6. Pick any embedding model. Each dimension is kept separate.')
await click(page.getByText('Embedding model', { exact: true }).first())
await page.getByText('Your datasets by embedding model').waitFor({ timeout: 30000 })
await pause(1200)
await click(page.getByRole('radio', { name: /built-in \(onnx\)/i }))
await page.getByRole('option', { name: /bge-small-en-v1\.5/ }).first().waitFor({ timeout: 30000 })
await pause(700)
await click(page.getByRole('option', { name: /bge-small-en-v1\.5/ }).first())
await pause(500)
await click(page.getByRole('button', { name: /^Use BAAI\/bge-small-en-v1\.5/ }))
await click(page.getByRole('button', { name: 'Switch only' }))
await page.getByText('Not searched with your current model').waitFor({ timeout: 60000 })
await reveal(page.getByText('Your datasets by embedding model'))
await pause(2400)

// 9. Mismatch is explained, with both fixes
await caption('7. Different embedding models are never mixed: switch back or re-embed, in one click')
await page.goto(`${BASE}/dashboard`)
await pause(800)
await skipTour()
const box = page.getByRole('textbox').first()
await click(box)
await box.pressSequentially('I forgot my password, send me a reset link', { delay: 18 })
await page.keyboard.press('Enter')
const switchBack = page.getByRole('button', { name: /search with nomic-embed-text/i })
await switchBack.waitFor({ timeout: 60000 })
await pause(2200)
await click(switchBack)
await page.getByText('Password_Reset_Request').first().waitFor({ timeout: 60000 })
await pause(2000)

// 10. Datasets tagged with their model
await caption('Every dataset shows the model that embedded it')
await page.goto(`${BASE}/datasets`)
await page.getByText('Demo catalogue utterances').first().waitFor({ timeout: 30000 })
await pause(900)
await skipTour()
await moveTo(page.getByText(/Ollama · nomic-embed-text · 768-dim/).first())
await pause(2400)

await caption('NLPForge · FastAPI · pgvector · Ollama · Next.js · github.com/Iammilansoni/NLPFT-2')
await pause(2600)

const video = page.video()
await context.close()
await browser.close()
console.log(await video.path())

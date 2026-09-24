/**
 * Auth layout: brand panel (left) + form (right).
 * The panel shows what the product actually does: one real request and the
 * validated API call it resolves to.
 */

import React from 'react';
import Link from 'next/link';
import { CheckCircle2, Network } from 'lucide-react';

const POINTS = [
  'Routes plain-English requests to the right endpoint in your API catalogue',
  'Extracts request bodies that validate against each endpoint’s JSON Schema',
  'Routing accuracy measured on a 180-query held-out benchmark',
];

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex bg-background">
      <aside className="hidden lg:flex lg:w-[46%] relative overflow-hidden bg-[hsl(240_32%_9%)] text-white">
        {/* Ambient brand light */}
        <div className="absolute -top-40 -left-40 h-[520px] w-[520px] rounded-full bg-primary/40 blur-[120px]" />
        <div className="absolute bottom-[-200px] right-[-120px] h-[460px] w-[460px] rounded-full bg-brand-2/30 blur-[120px]" />
        <div
          className="absolute inset-0 opacity-[0.07]"
          style={{
            backgroundImage:
              'linear-gradient(rgba(255,255,255,.6) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.6) 1px, transparent 1px)',
            backgroundSize: '44px 44px',
            maskImage: 'radial-gradient(ellipse at 30% 40%, black 30%, transparent 75%)',
          }}
        />

        <div className="relative z-10 flex flex-col justify-between w-full p-12 xl:p-14">
          <Link href="/" className="flex items-center gap-2.5 w-fit">
            <span className="grid h-9 w-9 place-items-center rounded-lg bg-brand-gradient shadow-glow">
              <Network className="h-5 w-5 text-white" />
            </span>
            <span className="font-display text-lg font-bold tracking-tight">NLPForge</span>
          </Link>

          <div className="space-y-8 max-w-lg">
            <h2 className="font-display text-4xl font-bold leading-[1.1] tracking-tight">
              From a sentence to a <span className="bg-gradient-to-r from-[hsl(245_90%_78%)] to-[hsl(265_90%_80%)] bg-clip-text text-transparent">validated API call</span>.
            </h2>

            <div className="rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-sm shadow-2xl overflow-hidden">
              <div className="flex items-center gap-1.5 border-b border-white/10 px-4 py-3">
                <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
                <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
                <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
                <span className="ml-3 font-mono text-[11px] text-white/45">semantic-search</span>
              </div>
              <div className="p-5 space-y-4 text-sm">
                <p className="text-white/75">“Refund 25 dollars on order 8820, it arrived broken”</p>
                <pre className="font-mono text-[12.5px] leading-relaxed text-white/85">{`POST /orders/{order_id}/refund
{
  "order_id": "8820",
  "amount": 25.0
}`}</pre>
              </div>
            </div>

            <ul className="space-y-3">
              {POINTS.map((p) => (
                <li key={p} className="flex items-start gap-3 text-white/70">
                  <CheckCircle2 className="h-5 w-5 mt-0.5 shrink-0 text-[hsl(156_60%_55%)]" />
                  <span>{p}</span>
                </li>
              ))}
            </ul>
          </div>

          <p className="text-xs text-white/35">FastAPI · PostgreSQL + pgvector · Ollama · Next.js</p>
        </div>
      </aside>

      <main id="main-content" className="flex w-full lg:w-[54%] items-center justify-center">
        <div className="w-full max-w-md px-6 py-10 lg:px-10">{children}</div>
      </main>
    </div>
  );
}

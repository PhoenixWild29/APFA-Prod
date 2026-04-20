import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import {
  MessageSquare,
  Upload,
  Shield,
  TrendingUp,
  Zap,
  Lock,
  ArrowRight,
  CheckCircle,
} from 'lucide-react';

const FEATURES = [
  { icon: MessageSquare, title: 'Conversational Research', desc: 'Ask about investments, market trends, economic indicators, or portfolio strategy. Get sourced, cited answers \u2014 not opinions.' },
  { icon: TrendingUp, title: 'Market Intelligence', desc: 'Track equity markets, interest rates, and economic indicators. Understand what\u2019s moving and why \u2014 with data, not speculation.' },
  { icon: Upload, title: 'Document Analysis', desc: 'Upload brokerage statements, research reports, or financial documents. APFA reads and explains them so you understand every detail.' },
  { icon: Shield, title: 'Source Transparency', desc: 'Every answer shows where it came from \u2014 investment research, SEC filings, market data, or your own documents. You verify the work.' },
  { icon: Zap, title: 'Portfolio & Scenario Analysis', desc: 'Analyze asset allocations, compare investment options, and model scenarios. Explore trade-offs with real data behind every number.' },
  { icon: Lock, title: 'Security First', desc: 'In-memory tokens, encrypted at rest, read-only data access. Your financial data stays yours.' },
];

const STATS = [
  { value: '100%', label: 'Answers cite sources' },
  { value: '<3s', label: 'Response time' },
  { value: '99.9%', label: 'Uptime' },
  { value: 'SOC 2', label: 'Compliance target' },
];

export default function Landing() {
  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden px-4 py-20 lg:py-28">
        <div className="container mx-auto max-w-6xl">
          <div className="grid items-center gap-12 lg:grid-cols-2">
            {/* Copy */}
            <div>
              {/* Trust chip */}
              <div className="mb-6 inline-flex items-center gap-2 rounded-full border bg-card px-3 py-1 text-xs">
                <span className="h-1.5 w-1.5 rounded-full bg-pos" />
                Every answer cites its sources &middot; Investment research &middot; Market data &middot; SEC filings
              </div>

              <h1 className="font-serif text-4xl font-semibold leading-tight tracking-tight sm:text-5xl lg:text-display">
                A financial advisor that{' '}
                <em className="font-serif italic text-teal-700 dark:text-teal-300">
                  shows its work
                </em>
                .
              </h1>

              <p className="mt-5 max-w-lg text-lg leading-relaxed text-muted-foreground">
                Investments, market strategy, portfolio analysis, economic
                trends — ask about your money and get answers grounded in
                research, data, and your own documents. Every answer cites its
                sources.
              </p>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Link to="/auth">
                  <Button size="lg" className="w-full bg-ink-900 text-ink-50 hover:bg-ink-700 dark:bg-ink-50 dark:text-ink-900 dark:hover:bg-ink-200 sm:w-auto">
                    Start free
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </Link>
                <a href="#how-it-works">
                  <Button size="lg" variant="outline" className="w-full sm:w-auto">
                    See how it works
                  </Button>
                </a>
              </div>
            </div>

            {/* Live demo placeholder */}
            <div className="rounded-2xl border bg-card p-6 shadow-card">
              <div className="mb-4 flex items-center gap-2 text-xs text-muted-foreground">
                <span className="h-1.5 w-1.5 rounded-full bg-pos" />
                Live preview
              </div>
              <div className="space-y-4">
                {/* Demo messages */}
                <div className="flex justify-end">
                  <div className="rounded-2xl rounded-br-md bg-teal-700 px-4 py-2.5 text-sm text-white">
                    Explain the rising-rate environment. My 401(k) is 70% equities.
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-teal-700/10 text-xs font-semibold text-teal-700 dark:bg-teal-300/10 dark:text-teal-300">
                    A
                  </div>
                  <div className="text-sm leading-relaxed text-muted-foreground">
                    The Federal Reserve has maintained rates at 5.25–5.50% since
                    July 2023, the highest level in 22 years. In a sustained
                    high-rate environment, fixed-income instruments typically
                    become more attractive on a yield basis, while equity
                    valuations face pressure from higher discount rates —
                    particularly in growth-heavy sectors.
                    <br /><br />
                    For a 70/30 equity allocation, the key considerations are
                    duration exposure and sector concentration. Understanding
                    your specific holdings would help clarify the trade-offs.
                    <span className="mt-1 block text-xs text-muted-foreground">
                      Sources: Federal Reserve FOMC Statement 03/26, Vanguard Capital Markets Model 2026
                    </span>
                  </div>
                </div>
                {/* Suggestion chips */}
                <div className="flex flex-wrap gap-2">
                  {['What drives interest rate changes?', 'Explain my brokerage statement', 'Compare index fund strategies'].map((q) => (
                    <Link
                      key={q}
                      to="/auth"
                      className="rounded-lg border border-dashed px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-teal-500 hover:text-foreground"
                    >
                      {q}
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Social proof strip */}
      <section className="border-y bg-muted/30 px-4 py-6">
        <div className="container mx-auto flex flex-wrap items-center justify-center gap-8 lg:gap-16">
          {STATS.map((stat) => (
            <div key={stat.label} className="text-center">
              <p className="tabular-nums text-2xl font-semibold text-teal-700 dark:text-teal-300">
                {stat.value}
              </p>
              <p className="text-xs text-muted-foreground">{stat.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="px-4 py-20">
        <div className="container mx-auto max-w-6xl">
          <h2 className="text-center font-serif text-3xl font-semibold">
            Built for serious financial research
          </h2>
          <p className="mx-auto mt-3 max-w-2xl text-center text-muted-foreground">
            APFA combines conversational AI with curated investment research and
            market intelligence — so every answer is transparent, sourced, and
            yours to verify.
          </p>
          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map(({ icon: Icon, title, desc }) => (
              <div key={title} className="rounded-xl border bg-card p-5">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-700/10 dark:bg-teal-300/10">
                  <Icon className="h-5 w-5 text-teal-700 dark:text-teal-300" />
                </div>
                <h3 className="mt-4 font-semibold">{title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
                  {desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="bg-muted/30 px-4 py-20">
        <div className="container mx-auto max-w-4xl">
          <h2 className="text-center font-serif text-3xl font-semibold">
            Three steps to clarity
          </h2>
          <div className="mt-12 grid gap-8 sm:grid-cols-3">
            {[
              { step: '1', title: 'Ask about your money', desc: 'Type a question about investments, markets, or your portfolio \u2014 or upload a document for analysis.' },
              { step: '2', title: 'Get sourced answers', desc: 'Every response cites investment research, market data, and relevant filings. Tap any source to inspect it.' },
              { step: '3', title: 'Make informed decisions', desc: 'Save analyses, set market alerts, and share insights with your financial professional.' },
            ].map(({ step, title, desc }) => (
              <div key={step} className="text-center">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-teal-700 font-serif text-xl font-semibold text-white dark:bg-teal-500">
                  {step}
                </div>
                <h3 className="mt-4 text-lg font-semibold">{title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA banner */}
      <section className="bg-ink-900 px-4 py-16 text-ink-50 dark:bg-ink-800">
        <div className="container mx-auto max-w-2xl text-center">
          <h2 className="font-serif text-3xl font-semibold">
            Ready to understand your finances?
          </h2>
          <p className="mt-3 text-ink-300">
            Free to start. No credit card. Your research, your terms.
          </p>
          <Link to="/auth">
            <Button
              size="lg"
              className="mt-6 bg-gold-500 text-ink-900 hover:bg-gold-300"
            >
              Start free
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </div>
      </section>
    </div>
  );
}

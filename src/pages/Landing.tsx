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
  { icon: MessageSquare, title: 'Conversational Advisor', desc: 'Ask anything about mortgages, rates, DTI, and affordability. Get sourced, regulation-backed answers.' },
  { icon: TrendingUp, title: 'Rate Tracking', desc: 'Monitor 30yr and 15yr rates with alerts. Know when to lock — before the window closes.' },
  { icon: Upload, title: 'Document Intelligence', desc: 'Upload statements and tax docs. APFA reads them so you don\'t have to summarize.' },
  { icon: Shield, title: 'Source Transparency', desc: 'Every answer cites its sources — TILA, RESPA, ECOA, and your own data. No black-box advice.' },
  { icon: Zap, title: 'Instant Calculations', desc: 'DTI, loan comparisons, affordability — compute live, save scenarios, share with your lender.' },
  { icon: Lock, title: 'Security First', desc: 'In-memory tokens, encrypted at rest, read-only data access. Your finances stay yours.' },
];

const STATS = [
  { value: '20+', label: 'Regulatory sources' },
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
                Grounded in 20 regulatory sources &middot; TILA &middot; RESPA &middot; ECOA
              </div>

              <h1 className="font-serif text-4xl font-semibold leading-tight tracking-tight sm:text-5xl lg:text-display">
                The financial advisor you{' '}
                <em className="font-serif italic text-teal-700 dark:text-teal-300">
                  deserve
                </em>
                .
              </h1>

              <p className="mt-5 max-w-lg text-lg leading-relaxed text-muted-foreground">
                Ask about mortgages, compare rates, check affordability — and get
                answers backed by real regulations and your own documents. No
                jargon, no sales pitch.
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
                    Can I afford a $400K house on $85K income?
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-teal-700/10 text-xs font-semibold text-teal-700 dark:bg-teal-300/10 dark:text-teal-300">
                    A
                  </div>
                  <div className="text-sm leading-relaxed text-muted-foreground">
                    Based on your income of $85K/yr (~$7,083/mo), a $400K home
                    with 10% down at current rates (6.62%) would cost about
                    <span className="font-medium text-foreground"> $2,308/mo</span>.
                    That puts your housing DTI at
                    <span className="font-medium text-foreground"> 32.6%</span> —
                    within the
                    <span className="text-pos font-medium"> safe zone (≤36%)</span>.
                    <span className="mt-1 block text-xs text-muted-foreground">
                      Sources: TILA §226.18, Freddie Mac PMMS 04/17
                    </span>
                  </div>
                </div>
                {/* Suggestion chips */}
                <div className="flex flex-wrap gap-2">
                  {['What about FHA?', 'Show me 15yr rates', 'Compare scenarios'].map((q) => (
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
            Built for serious financial decisions
          </h2>
          <p className="mx-auto mt-3 max-w-2xl text-center text-muted-foreground">
            APFA combines conversational AI with regulatory grounding — so every
            answer is transparent, sourced, and yours to verify.
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
              { step: '1', title: 'Ask', desc: 'Type a question — "Can I afford this house?" — or upload a document for APFA to read.' },
              { step: '2', title: 'Receive sourced answers', desc: 'Every response cites regulations, rate data, and your own documents. Tap a source to inspect.' },
              { step: '3', title: 'Act with confidence', desc: 'Save scenarios, compare loans, set rate alerts, and share results with your lender or advisor.' },
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
            Ready to take control?
          </h2>
          <p className="mt-3 text-ink-300">
            Free to start. No credit card. Upgrade when you're ready.
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

import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { CheckCircle, Upload, Brain, Shield, TrendingUp, ArrowRight } from 'lucide-react';

export default function Landing() {
  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <section className="py-20 px-4 text-center bg-gradient-to-b from-primary/10 to-background">
        <div className="container mx-auto max-w-4xl">
          <h1 className="mb-6 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
            AI-Powered Financial Advisor
          </h1>
          <p className="mx-auto mb-8 max-w-2xl text-lg text-muted-foreground sm:text-xl">
            Get personalized financial advice powered by advanced AI. Upload your documents,
            analyze your finances, and receive tailored recommendations for loans, investments, and planning.
          </p>
          <div className="flex flex-col gap-4 sm:flex-row sm:justify-center">
            <Link to="/register">
              <Button size="lg" className="w-full sm:w-auto">
                Get Started Free
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Button size="lg" variant="outline" className="w-full sm:w-auto">
              Learn More
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto max-w-6xl">
          <h2 className="mb-12 text-center text-3xl font-bold">Why Choose APFA?</h2>
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-lg border bg-card p-6 text-center">
              <Brain className="mx-auto h-12 w-12 text-primary mb-4" />
              <h3 className="mb-2 text-lg font-semibold">AI-Powered Analysis</h3>
              <p className="text-sm text-muted-foreground">
                Advanced multi-agent AI systems analyze your financial documents and provide accurate, personalized recommendations.
              </p>
            </div>
            <div className="rounded-lg border bg-card p-6 text-center">
              <Upload className="mx-auto h-12 w-12 text-primary mb-4" />
              <h3 className="mb-2 text-lg font-semibold">Document Upload</h3>
              <p className="text-sm text-muted-foreground">
                Securely upload bank statements, tax documents, and financial records for comprehensive analysis.
              </p>
            </div>
            <div className="rounded-lg border bg-card p-6 text-center">
              <Shield className="mx-auto h-12 w-12 text-primary mb-4" />
              <h3 className="mb-2 text-lg font-semibold">Secure & Private</h3>
              <p className="text-sm text-muted-foreground">
                Your financial data is protected with enterprise-grade security and privacy controls.
              </p>
            </div>
            <div className="rounded-lg border bg-card p-6 text-center">
              <TrendingUp className="mx-auto h-12 w-12 text-primary mb-4" />
              <h3 className="mb-2 text-lg font-semibold">Personalized Planning</h3>
              <p className="text-sm text-muted-foreground">
                Receive tailored financial plans and recommendations based on your unique situation.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-4 bg-muted/50">
        <div className="container mx-auto max-w-4xl">
          <h2 className="mb-12 text-center text-3xl font-bold">How It Works</h2>
          <div className="grid gap-8 sm:grid-cols-3">
            <div className="text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary text-primary-foreground text-2xl font-bold">
                1
              </div>
              <h3 className="mb-2 text-xl font-semibold">Upload Documents</h3>
              <p className="text-muted-foreground">
                Securely upload your financial documents and statements.
              </p>
            </div>
            <div className="text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary text-primary-foreground text-2xl font-bold">
                2
              </div>
              <h3 className="mb-2 text-xl font-semibold">AI Analysis</h3>
              <p className="text-muted-foreground">
                Our AI analyzes your documents and financial situation.
              </p>
            </div>
            <div className="text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary text-primary-foreground text-2xl font-bold">
                3
              </div>
              <h3 className="mb-2 text-xl font-semibold">Get Recommendations</h3>
              <p className="text-muted-foreground">
                Receive personalized financial advice and planning recommendations.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Teaser */}
      <section className="py-20 px-4">
        <div className="container mx-auto max-w-4xl text-center">
          <h2 className="mb-8 text-3xl font-bold">Pricing</h2>
          <p className="mb-8 text-lg text-muted-foreground">
            Start with our free tier and upgrade as your needs grow.
          </p>
          <div className="grid gap-8 sm:grid-cols-3">
            <div className="rounded-lg border bg-card p-6">
              <div className="mb-4">
                <h3 className="text-xl font-semibold">Free</h3>
                <p className="text-muted-foreground">$0/month</p>
              </div>
              <ul className="space-y-2 text-sm">
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  Basic document analysis
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  5 documents per month
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  Email support
                </li>
              </ul>
            </div>
            <div className="rounded-lg border border-primary bg-card p-6">
              <div className="mb-4">
                <h3 className="text-xl font-semibold">Pro</h3>
                <p className="text-muted-foreground">$19/month</p>
              </div>
              <ul className="space-y-2 text-sm">
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  Advanced AI analysis
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  Unlimited documents
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  Priority support
                </li>
              </ul>
            </div>
            <div className="rounded-lg border bg-card p-6">
              <div className="mb-4">
                <h3 className="text-xl font-semibold">Enterprise</h3>
                <p className="text-muted-foreground">Contact Us</p>
              </div>
              <ul className="space-y-2 text-sm">
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  Custom integrations
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  Dedicated support
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  SLA guarantees
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 bg-primary text-primary-foreground">
        <div className="container mx-auto max-w-2xl text-center">
          <h2 className="mb-4 text-3xl font-bold">Ready to Take Control of Your Finances?</h2>
          <p className="mb-8 text-lg opacity-90">
            Join thousands of users who trust APFA for their financial planning needs.
          </p>
          <Link to="/register">
            <Button size="lg" variant="secondary" className="w-full sm:w-auto">
              Start Your Free Trial
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t bg-background px-4 py-8">
        <div className="container mx-auto max-w-6xl">
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <h3 className="mb-4 text-lg font-semibold">APFA</h3>
              <p className="text-sm text-muted-foreground">
                AI-Powered Agentic Personalized Financial Advisor
              </p>
            </div>
            <div>
              <h4 className="mb-4 font-medium">Product</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link to="/about" className="hover:text-foreground">About</Link></li>
                <li><Link to="/contact" className="hover:text-foreground">Contact</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="mb-4 font-medium">Account</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link to="/auth" className="hover:text-foreground">Login</Link></li>
                <li><Link to="/register" className="hover:text-foreground">Register</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="mb-4 font-medium">Legal</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><a href="#" className="hover:text-foreground">Privacy Policy</a></li>
                <li><a href="#" className="hover:text-foreground">Terms of Service</a></li>
              </ul>
            </div>
          </div>
          <div className="mt-8 border-t pt-8 text-center text-sm text-muted-foreground">
            © 2025 APFA. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
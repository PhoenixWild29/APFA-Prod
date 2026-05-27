import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { User, Shield, CreditCard, Key, Loader2, ExternalLink, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useAuthStore } from '@/store/authStore';
import { useBillingStatus } from '@/hooks/useBilling';
import { createCheckoutSession, createPortalSession } from '@/api/billingApi';

function ProfileTab() {
  const user = useAuthStore((s) => s.user);

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold">Profile Information</h3>
        <p className="text-xs text-muted-foreground">
          Update your account details.
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <Label htmlFor="username" className="text-xs">Username</Label>
          <Input
            id="username"
            defaultValue={user?.username ?? ''}
            className="mt-1.5"
          />
        </div>
        <div>
          <Label htmlFor="email" className="text-xs">Email</Label>
          <Input
            id="email"
            type="email"
            defaultValue={user?.email ?? ''}
            className="mt-1.5"
          />
        </div>
      </div>
      <Button size="sm">Save changes</Button>
    </div>
  );
}

function SecurityTab() {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold">Password</h3>
        <p className="text-xs text-muted-foreground">
          Change your password. You'll be logged out of other sessions.
        </p>
      </div>
      <div className="max-w-sm space-y-3">
        <div>
          <Label htmlFor="current-pw" className="text-xs">Current password</Label>
          <Input id="current-pw" type="password" className="mt-1.5" />
        </div>
        <div>
          <Label htmlFor="new-pw" className="text-xs">New password</Label>
          <Input id="new-pw" type="password" className="mt-1.5" />
        </div>
        <div>
          <Label htmlFor="confirm-pw" className="text-xs">Confirm password</Label>
          <Input id="confirm-pw" type="password" className="mt-1.5" />
        </div>
        <Button size="sm">Update password</Button>
      </div>

      <Separator />

      <div>
        <h3 className="text-sm font-semibold">Two-Factor Authentication</h3>
        <p className="text-xs text-muted-foreground">
          Add an extra layer of security to your account.
        </p>
        <div className="mt-3 flex items-center justify-between rounded-lg border p-3">
          <div className="flex items-center gap-3">
            <Shield className="h-5 w-5 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium">Authenticator app</p>
              <p className="text-xs text-muted-foreground">Not configured</p>
            </div>
          </div>
          <Button size="sm" variant="outline">
            Set up
          </Button>
        </div>
      </div>

      <Separator />

      <div>
        <h3 className="text-sm font-semibold">Active Sessions</h3>
        <div className="mt-3 rounded-lg border p-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Current session</p>
              <p className="text-xs text-muted-foreground">
                This device &middot; Started {new Date().toLocaleDateString()}
              </p>
            </div>
            <Badge variant="secondary" className="text-xs">Current</Badge>
          </div>
        </div>
      </div>
    </div>
  );
}

const TIER_CONFIG = {
  free: { label: 'Free Plan', color: 'bg-gray-600', description: '5 queries per month' },
  pro: { label: 'Pro Plan', color: 'bg-teal-700', description: '100 queries per month' },
  enterprise: { label: 'Enterprise', color: 'bg-purple-700', description: 'Unlimited queries' },
} as const;

function BillingTab() {
  const { data: billing, isLoading, error } = useBillingStatus();
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);
  const [portalLoading, setPortalLoading] = useState(false);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-20 w-full" />
      </div>
    );
  }

  if (error || !billing) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
        Failed to load billing information. Please try again.
      </div>
    );
  }

  const tierConfig = TIER_CONFIG[billing.tier] ?? TIER_CONFIG.free;
  const isFreeTier = billing.tier === 'free';
  const isEnterprise = billing.tier === 'enterprise';

  const handleUpgrade = async (tier: 'pro' | 'enterprise') => {
    setCheckoutLoading(tier);
    try {
      const url = await createCheckoutSession(tier);
      window.location.href = url;
    } catch {
      toast.error('Failed to start checkout. Please try again.');
      setCheckoutLoading(null);
    }
  };

  const handleManageSubscription = async () => {
    setPortalLoading(true);
    try {
      const url = await createPortalSession();
      window.location.href = url;
    } catch {
      toast.error('Failed to open subscription management.');
      setPortalLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold">Current Plan</h3>
        <p className="text-xs text-muted-foreground">
          Manage your subscription and billing.
        </p>
      </div>

      {/* Current plan card */}
      <div className="rounded-xl border bg-card p-5">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-lg font-semibold">{tierConfig.label}</p>
            <p className="mt-0.5 text-sm text-muted-foreground">
              {tierConfig.description}
            </p>
          </div>
          <Badge className={`${tierConfig.color} text-white`}>Active</Badge>
        </div>

        {/* Usage bar */}
        {!isEnterprise && (
          <div className="mt-4">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>
                {billing.query_count_this_period} / {billing.limit} queries used
              </span>
              <span>{billing.usage_percentage}%</span>
            </div>
            <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-muted">
              <div
                className={`h-full rounded-full transition-all ${
                  billing.usage_percentage >= 90
                    ? 'bg-red-500'
                    : billing.usage_percentage >= 70
                      ? 'bg-amber-500'
                      : 'bg-teal-600'
                }`}
                style={{ width: `${Math.min(billing.usage_percentage, 100)}%` }}
              />
            </div>
          </div>
        )}

        {isEnterprise && (
          <div className="mt-4 text-xs text-muted-foreground">
            <CheckCircle2 className="mr-1 inline h-3.5 w-3.5 text-green-600" />
            Unlimited queries &middot; {billing.query_count_this_period} used this period
          </div>
        )}

        <Separator className="my-4" />

        {/* Action buttons */}
        <div className="flex flex-wrap gap-3">
          {isFreeTier && (
            <>
              <Button
                onClick={() => handleUpgrade('pro')}
                disabled={!!checkoutLoading}
              >
                {checkoutLoading === 'pro' && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Upgrade to Pro — $29/mo
              </Button>
              <Button
                variant="outline"
                onClick={() => handleUpgrade('enterprise')}
                disabled={!!checkoutLoading}
              >
                {checkoutLoading === 'enterprise' && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Enterprise — $99/mo
              </Button>
            </>
          )}
          {billing.tier === 'pro' && (
            <>
              <Button
                variant="outline"
                onClick={() => handleUpgrade('enterprise')}
                disabled={!!checkoutLoading}
              >
                {checkoutLoading === 'enterprise' && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Upgrade to Enterprise
              </Button>
            </>
          )}
          {billing.has_subscription && (
            <Button
              variant="outline"
              onClick={handleManageSubscription}
              disabled={portalLoading}
            >
              {portalLoading ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <ExternalLink className="mr-2 h-4 w-4" />
              )}
              Manage Subscription
            </Button>
          )}
        </div>
      </div>

      {/* Payment method info */}
      {!billing.has_subscription && (
        <div className="rounded-lg border p-4 text-center text-sm text-muted-foreground">
          <CreditCard className="mx-auto mb-2 h-8 w-8 text-muted-foreground/40" />
          <p>No payment method on file.</p>
          <p className="mt-1 text-xs">Add a card when you're ready to upgrade.</p>
        </div>
      )}
    </div>
  );
}

function APIKeysTab() {
  const user = useAuthStore((s) => s.user);
  const isFreeTier = !user?.subscription_tier || user.subscription_tier === 'free';

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold">API Keys</h3>
        <p className="text-xs text-muted-foreground">
          Manage keys for programmatic access to APFA.
        </p>
      </div>

      <div className="rounded-lg border p-4 text-center text-sm text-muted-foreground">
        <Key className="mx-auto mb-2 h-8 w-8 text-muted-foreground/40" />
        <p>No API keys yet.</p>
        <p className="mt-1 text-xs">
          API access is available on Pro and Enterprise plans.
        </p>
        <Button size="sm" variant="outline" className="mt-3" disabled={isFreeTier}>
          Generate key
        </Button>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const defaultTab = searchParams.get('tab') ?? 'profile';
  const checkoutResult = searchParams.get('checkout');

  useEffect(() => {
    if (checkoutResult === 'success') {
      toast.success('Subscription activated! Your plan has been upgraded.');
      setSearchParams((prev) => {
        prev.delete('checkout');
        return prev;
      });
    } else if (checkoutResult === 'cancel') {
      toast.info('Checkout cancelled. No changes were made.');
      setSearchParams((prev) => {
        prev.delete('checkout');
        return prev;
      });
    }
  }, [checkoutResult, setSearchParams]);

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      <div>
        <h1 className="font-serif text-2xl font-semibold">Settings</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Manage your account, security, and preferences.
        </p>
      </div>

      <Tabs defaultValue={defaultTab}>
        <TabsList>
          <TabsTrigger value="profile" className="gap-1.5 text-xs">
            <User className="h-3.5 w-3.5" />
            Profile
          </TabsTrigger>
          <TabsTrigger value="security" className="gap-1.5 text-xs">
            <Shield className="h-3.5 w-3.5" />
            Security
          </TabsTrigger>
          <TabsTrigger value="billing" className="gap-1.5 text-xs">
            <CreditCard className="h-3.5 w-3.5" />
            Billing
          </TabsTrigger>
          <TabsTrigger value="api" className="gap-1.5 text-xs">
            <Key className="h-3.5 w-3.5" />
            API Keys
          </TabsTrigger>
        </TabsList>

        <div className="mt-6">
          <TabsContent value="profile"><ProfileTab /></TabsContent>
          <TabsContent value="security"><SecurityTab /></TabsContent>
          <TabsContent value="billing"><BillingTab /></TabsContent>
          <TabsContent value="api"><APIKeysTab /></TabsContent>
        </div>
      </Tabs>
    </div>
  );
}

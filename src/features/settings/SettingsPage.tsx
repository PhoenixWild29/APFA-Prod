import { useState } from 'react';
import { User, Shield, CreditCard, Key } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { useAuthStore } from '@/store/authStore';

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

function BillingTab() {
  const user = useAuthStore((s) => s.user);

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold">Current Plan</h3>
        <p className="text-xs text-muted-foreground">
          Manage your subscription and billing.
        </p>
      </div>

      <div className="rounded-xl border bg-card p-5">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-lg font-semibold">Free Plan</p>
            <p className="mt-0.5 text-sm text-muted-foreground">
              5 queries per month &middot; Basic documents &middot; Community support
            </p>
          </div>
          <Badge className="bg-teal-700 text-white">Active</Badge>
        </div>
        <Separator className="my-4" />
        <div className="flex gap-3">
          <Button>Upgrade to Pro</Button>
          <Button variant="outline">View plans</Button>
        </div>
      </div>

      <div className="rounded-lg border p-4 text-center text-sm text-muted-foreground">
        <CreditCard className="mx-auto mb-2 h-8 w-8 text-muted-foreground/40" />
        <p>No payment method on file.</p>
        <p className="mt-1 text-xs">Add a card when you're ready to upgrade.</p>
      </div>
    </div>
  );
}

function APIKeysTab() {
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
        <Button size="sm" variant="outline" className="mt-3" disabled>
          Generate key
        </Button>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      <div>
        <h1 className="font-serif text-2xl font-semibold">Settings</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Manage your account, security, and preferences.
        </p>
      </div>

      <Tabs defaultValue="profile">
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

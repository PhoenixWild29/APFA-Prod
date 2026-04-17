import { Users, Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';

// Placeholder — will be wired to GET /admin/users once backend ships
const DEMO_USERS = [
  { id: '1', username: 'admin', email: 'admin@apfa.dev', role: 'admin', last_login: '2026-04-17', status: 'active' },
  { id: '2', username: 'demo_user', email: 'demo@example.com', role: 'standard', last_login: '2026-04-16', status: 'active' },
];

export default function AdminUsersPage() {
  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="font-serif text-2xl font-semibold">User Management</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          {DEMO_USERS.length} registered users.
        </p>
      </div>

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input placeholder="Search users..." className="pl-9" />
      </div>

      <div className="rounded-xl border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">User</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Role</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Last login</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Status</th>
            </tr>
          </thead>
          <tbody>
            {DEMO_USERS.map((u) => (
              <tr key={u.id} className="border-b last:border-0">
                <td className="px-4 py-3">
                  <p className="font-medium">{u.username}</p>
                  <p className="text-xs text-muted-foreground">{u.email}</p>
                </td>
                <td className="px-4 py-3">
                  <Badge variant={u.role === 'admin' ? 'default' : 'secondary'} className="text-xs">
                    {u.role}
                  </Badge>
                </td>
                <td className="px-4 py-3 tabular-nums text-muted-foreground">{u.last_login}</td>
                <td className="px-4 py-3">
                  <Badge className="bg-pos/10 text-pos text-xs">{u.status}</Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

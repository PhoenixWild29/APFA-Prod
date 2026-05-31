import { useEffect, useState } from 'react';
import { Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import apiClient from '@/api/apiClient';

interface AdminUser {
  id: string;
  username: string;
  email: string;
  role: string;
  disabled: boolean;
  verified: boolean;
  subscription_tier: string;
  created_at: string | null;
}

interface UsersResponse {
  users: AdminUser[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export default function AdminUsersPage() {
  const [data, setData] = useState<UsersResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');

  useEffect(() => {
    setLoading(true);
    setError(null);
    const params: Record<string, string | number> = { page, page_size: 25 };
    if (search) params.search = search;

    apiClient
      .get<UsersResponse>('/admin/users', { params })
      .then((res) => setData(res.data))
      .catch((err) => setError(err.response?.data?.detail || 'Failed to load users'))
      .finally(() => setLoading(false));
  }, [page, search]);

  const handleSearch = () => {
    setPage(1);
    setSearch(searchInput);
  };

  const users = data?.users ?? [];

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="font-serif text-2xl font-semibold">User Management</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          {data ? `${data.total_count} registered user${data.total_count !== 1 ? 's' : ''}` : 'Loading...'}
        </p>
      </div>

      <form
        className="relative max-w-sm"
        onSubmit={(e) => {
          e.preventDefault();
          handleSearch();
        }}
      >
        <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search users..."
          className="pl-9"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
        />
      </form>

      {error && (
        <div className="rounded-lg border border-neg/20 bg-neg/5 p-4 text-sm text-neg">
          {error}
        </div>
      )}

      <div className="rounded-xl border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">User</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Role</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Tier</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Joined</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                  Loading...
                </td>
              </tr>
            ) : users.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                  {search ? 'No users match your search.' : 'No users found.'}
                </td>
              </tr>
            ) : (
              users.map((u) => (
                <tr key={u.id} className="border-b last:border-0 hover:bg-muted/50">
                  <td className="px-4 py-3">
                    <p className="font-medium">{u.username}</p>
                    <p className="text-xs text-muted-foreground">{u.email}</p>
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={u.role === 'admin' ? 'default' : 'secondary'} className="text-xs">
                      {u.role}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">{u.subscription_tier}</td>
                  <td className="px-4 py-3 tabular-nums text-muted-foreground">
                    {u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}
                  </td>
                  <td className="px-4 py-3">
                    {u.disabled ? (
                      <Badge variant="destructive" className="text-xs">disabled</Badge>
                    ) : u.verified ? (
                      <Badge className="bg-pos/10 text-pos text-xs">active</Badge>
                    ) : (
                      <Badge variant="secondary" className="text-xs">unverified</Badge>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            Page {data.page} of {data.total_pages}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              <ChevronLeft className="mr-1 h-3.5 w-3.5" />
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= data.total_pages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
              <ChevronRight className="ml-1 h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

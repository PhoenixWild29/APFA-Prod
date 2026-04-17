import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Search,
  Upload,
  Filter,
  FileText,
  SlidersHorizontal,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import apiClient from '@/api/apiClient';
import DocumentCard, { type DocumentItem } from './components/DocumentCard';

type SortOption = 'newest' | 'oldest' | 'name' | 'size';
type StatusFilter = 'all' | 'completed' | 'processing' | 'failed';

export default function DocumentsPage() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('newest');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [searchMode, setSearchMode] = useState<'list' | 'semantic'>('list');

  // Fetch all documents
  const { data: documents = [], isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: async () => {
      try {
        const res = await apiClient.get<DocumentItem[]>('/admin/knowledge-base/documents');
        return Array.isArray(res.data) ? res.data : [];
      } catch {
        return [];
      }
    },
    staleTime: 60_000,
  });

  // Semantic search
  const {
    data: semanticResults,
    isLoading: isSearching,
    refetch: doSemanticSearch,
  } = useQuery({
    queryKey: ['semantic-search', searchQuery],
    queryFn: async () => {
      if (!searchQuery.trim() || searchQuery.length < 3) return null;
      try {
        const res = await apiClient.post('/documents/semantic-search', {
          query: searchQuery,
          top_k: 20,
        });
        return res.data;
      } catch {
        return null;
      }
    },
    enabled: false,
  });

  // Filter + sort
  const filtered = useMemo(() => {
    let result = [...documents];

    // Status filter
    if (statusFilter !== 'all') {
      result = result.filter((d) => d.processing_status === statusFilter);
    }

    // Text filter (local)
    if (searchQuery.trim() && searchMode === 'list') {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (d) =>
          d.filename.toLowerCase().includes(q) ||
          d.tags?.some((t) => t.toLowerCase().includes(q))
      );
    }

    // Sort
    result.sort((a, b) => {
      switch (sortBy) {
        case 'newest':
          return new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime();
        case 'oldest':
          return new Date(a.uploaded_at).getTime() - new Date(b.uploaded_at).getTime();
        case 'name':
          return a.filename.localeCompare(b.filename);
        case 'size':
          return b.file_size - a.file_size;
        default:
          return 0;
      }
    });

    return result;
  }, [documents, searchQuery, sortBy, statusFilter, searchMode]);

  const statusCounts = useMemo(() => {
    const counts = { all: documents.length, completed: 0, processing: 0, failed: 0 };
    for (const d of documents) {
      if (d.processing_status in counts) {
        counts[d.processing_status as keyof typeof counts]++;
      }
    }
    return counts;
  }, [documents]);

  const handleSemanticSearch = () => {
    if (searchQuery.trim().length >= 3) {
      doSemanticSearch();
    }
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-serif text-2xl font-semibold">Documents</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {documents.length} document{documents.length !== 1 ? 's' : ''} in your knowledge base
          </p>
        </div>
        <Button onClick={() => navigate('/app/documents/upload')}>
          <Upload className="mr-2 h-4 w-4" />
          Upload
        </Button>
      </div>

      {/* Search + filters */}
      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && searchMode === 'semantic') {
                handleSemanticSearch();
              }
            }}
            placeholder={
              searchMode === 'semantic'
                ? 'Semantic search (e.g., "FHA loan requirements")...'
                : 'Filter by name or tag...'
            }
            className="pl-9"
          />
        </div>

        <div className="flex gap-2">
          <Tabs
            value={searchMode}
            onValueChange={(v) => setSearchMode(v as 'list' | 'semantic')}
          >
            <TabsList className="h-9">
              <TabsTrigger value="list" className="text-xs">
                <Filter className="mr-1.5 h-3 w-3" />
                Filter
              </TabsTrigger>
              <TabsTrigger value="semantic" className="text-xs">
                <Search className="mr-1.5 h-3 w-3" />
                Semantic
              </TabsTrigger>
            </TabsList>
          </Tabs>

          <Select value={sortBy} onValueChange={(v) => setSortBy(v as SortOption)}>
            <SelectTrigger className="w-32 h-9 text-xs">
              <SlidersHorizontal className="mr-1.5 h-3 w-3" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="newest">Newest</SelectItem>
              <SelectItem value="oldest">Oldest</SelectItem>
              <SelectItem value="name">Name</SelectItem>
              <SelectItem value="size">Size</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Status filter chips */}
      <div className="flex flex-wrap gap-2">
        {(
          ['all', 'completed', 'processing', 'failed'] as const
        ).map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
              statusFilter === status
                ? 'border-teal-500 bg-teal-500/10 text-teal-700 dark:text-teal-300'
                : 'border-border text-muted-foreground hover:text-foreground'
            }`}
          >
            {status === 'all' ? 'All' : status.charAt(0).toUpperCase() + status.slice(1)}
            <Badge variant="secondary" className="ml-1 text-[10px] px-1 py-0">
              {statusCounts[status]}
            </Badge>
          </button>
        ))}
      </div>

      {/* Document list */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-4 rounded-lg border p-4">
              <Skeleton className="h-10 w-10 rounded-lg" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-3 w-32" />
              </div>
            </div>
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center gap-4 py-16 text-center">
          <FileText className="h-12 w-12 text-muted-foreground/30" />
          <div>
            <p className="font-medium">No documents found</p>
            <p className="mt-1 text-sm text-muted-foreground">
              {searchQuery
                ? 'Try a different search term.'
                : 'Upload your first document to get started.'}
            </p>
          </div>
          {!searchQuery && (
            <Button onClick={() => navigate('/app/documents/upload')}>
              <Upload className="mr-2 h-4 w-4" />
              Upload document
            </Button>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((doc) => (
            <DocumentCard key={doc.id} document={doc} />
          ))}
        </div>
      )}
    </div>
  );
}

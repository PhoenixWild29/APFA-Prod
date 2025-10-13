/**
 * Search Results Table Component
 * 
 * Sortable, paginated results with lazy loading
 */
import React, { useState, useEffect } from 'react';
import { ChevronUp, ChevronDown, Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface SearchResultsTableProps {
  query: string;
  filters: any;
  sortBy: string;
  onSortChange: (field: string) => void;
  onDocumentClick: (document: any) => void;
}

export default function SearchResultsTable({
  query,
  filters,
  sortBy,
  onSortChange,
  onDocumentClick
}: SearchResultsTableProps) {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [totalResults, setTotalResults] = useState(0);

  useEffect(() => {
    if (query.length >= 3) {
      searchDocuments();
    }
  }, [query, filters, sortBy, page]);

  const searchDocuments = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/documents/search?query=${encodeURIComponent(query)}&` +
        `limit=25&offset=${(page - 1) * 25}&` +
        `similarity_threshold=0.5`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );
      const data = await response.json();
      setResults(data.results || []);
      setTotalResults(data.total_results || 0);
    } catch (error) {
      console.error('Error searching documents:', error);
    } finally {
      setLoading(false);
    }
  };

  if (query.length < 3) {
    return (
      <div className="rounded-lg border bg-card p-12 text-center">
        <p className="text-muted-foreground">
          Enter at least 3 characters to search
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-card">
      <div className="border-b p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">
            Search Results ({totalResults.toLocaleString()})
          </h2>
          
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Sort by:</span>
            <select
              className="rounded-md border bg-background px-3 py-2 text-sm"
              value={sortBy}
              onChange={(e) => onSortChange(e.target.value)}
            >
              <option value="relevance">Relevance</option>
              <option value="date">Upload Date</option>
              <option value="size">File Size</option>
              <option value="title">Title</option>
            </select>
          </div>
        </div>
      </div>

      <div className="divide-y">
        {loading ? (
          <div className="p-12 text-center text-muted-foreground">
            Loading results...
          </div>
        ) : results.length === 0 ? (
          <div className="p-12 text-center">
            <p className="text-muted-foreground">No documents found</p>
            <p className="mt-2 text-sm text-muted-foreground">
              Try adjusting your search query or filters
            </p>
          </div>
        ) : (
          results.map((result: any) => (
            <div
              key={result.document_id}
              className="flex items-start gap-4 p-4 hover:bg-muted/50"
            >
              <div className="flex-1">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold">{result.document_metadata.filename}</h3>
                    <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
                      {result.snippet}
                    </p>
                    <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
                      <span>{result.document_metadata.document_type}</span>
                      <span>•</span>
                      <span>{new Date(result.document_metadata.creation_date).toLocaleDateString()}</span>
                      <span>•</span>
                      <span className="font-semibold text-primary">
                        {(result.relevance_score * 100).toFixed(0)}% match
                      </span>
                    </div>
                  </div>
                  
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onDocumentClick(result)}
                  >
                    <Eye className="mr-2 h-4 w-4" />
                    Preview
                  </Button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      {totalResults > 25 && (
        <div className="border-t p-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Page {page} of {Math.ceil(totalResults / 25)}
            </p>
            <div className="flex gap-2">
              <Button
                onClick={() => setPage(page - 1)}
                disabled={page === 1}
                variant="outline"
                size="sm"
              >
                Previous
              </Button>
              <Button
                onClick={() => setPage(page + 1)}
                disabled={page >= Math.ceil(totalResults / 25)}
                variant="outline"
                size="sm"
              >
                Next
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


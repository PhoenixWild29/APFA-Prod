/**
 * Document Table Component
 * 
 * Searchable, sortable, paginated table for document metadata
 */
import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { ChevronUp, ChevronDown, Search } from 'lucide-react';

interface Document {
  document_id: string;
  filename: string;
  file_size_bytes: number;
  upload_timestamp: string;
  processing_status: string;
  uploaded_by: string;
  content_type: string;
}

interface DocumentTableProps {
  filters: any;
}

export default function DocumentTable({ filters }: DocumentTableProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);
  const [sortField, setSortField] = useState('upload_timestamp');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchDocuments();
  }, [page, sortField, sortOrder, filters, searchQuery]);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/admin/dashboard/documents?` +
        `page=${page}&page_size=${pageSize}&` +
        `sort_field=${sortField}&sort_order=${sortOrder}&` +
        `search=${searchQuery}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );
      const data = await response.json();
      setDocuments(data.documents || []);
    } catch (error) {
      console.error('Error fetching documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="rounded-lg border bg-card">
      <div className="border-b p-4">
        <h2 className="text-lg font-semibold">Document Library</h2>
        
        {/* Search */}
        <div className="mt-4 flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search documents..."
              className="w-full rounded-md border bg-background pl-10 pr-4 py-2"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="border-b bg-muted/50">
            <tr>
              <th className="p-3 text-left">
                <button
                  onClick={() => handleSort('filename')}
                  className="flex items-center gap-1 font-medium hover:text-primary"
                >
                  Filename
                  {sortField === 'filename' && (
                    sortOrder === 'asc' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />
                  )}
                </button>
              </th>
              <th className="p-3 text-left">Type</th>
              <th className="p-3 text-left">
                <button
                  onClick={() => handleSort('file_size_bytes')}
                  className="flex items-center gap-1 font-medium hover:text-primary"
                >
                  Size
                  {sortField === 'file_size_bytes' && (
                    sortOrder === 'asc' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />
                  )}
                </button>
              </th>
              <th className="p-3 text-left">Status</th>
              <th className="p-3 text-left">Uploaded By</th>
              <th className="p-3 text-left">
                <button
                  onClick={() => handleSort('upload_timestamp')}
                  className="flex items-center gap-1 font-medium hover:text-primary"
                >
                  Upload Date
                  {sortField === 'upload_timestamp' && (
                    sortOrder === 'asc' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />
                  )}
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className="p-8 text-center text-muted-foreground">
                  Loading documents...
                </td>
              </tr>
            ) : documents.length === 0 ? (
              <tr>
                <td colSpan={6} className="p-8 text-center text-muted-foreground">
                  No documents found
                </td>
              </tr>
            ) : (
              documents.map((doc) => (
                <tr key={doc.document_id} className="border-b hover:bg-muted/50">
                  <td className="p-3 font-medium">{doc.filename}</td>
                  <td className="p-3 text-sm text-muted-foreground">{doc.content_type}</td>
                  <td className="p-3 text-sm">{formatFileSize(doc.file_size_bytes)}</td>
                  <td className="p-3">
                    <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                      doc.processing_status === 'completed' ? 'bg-green-100 text-green-800' :
                      doc.processing_status === 'processing' ? 'bg-blue-100 text-blue-800' :
                      doc.processing_status === 'failed' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {doc.processing_status}
                    </span>
                  </td>
                  <td className="p-3 text-sm">{doc.uploaded_by}</td>
                  <td className="p-3 text-sm text-muted-foreground">
                    {new Date(doc.upload_timestamp).toLocaleString()}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between border-t p-4">
        <p className="text-sm text-muted-foreground">
          Page {page} of {Math.ceil(documents.length / pageSize)}
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
            disabled={documents.length < pageSize}
            variant="outline"
            size="sm"
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}


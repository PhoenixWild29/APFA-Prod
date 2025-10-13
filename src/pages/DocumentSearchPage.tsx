/**
 * Document Search Page
 * 
 * Comprehensive document retrieval interface with:
 * - Full-text semantic search
 * - Advanced filtering
 * - Document preview
 * - Version history
 * - Audit trails
 * - Export capabilities
 */
import React, { useState } from 'react';
import SearchBar from '@/components/search/SearchBar';
import AdvancedFilters from '@/components/search/AdvancedFilters';
import SearchResultsTable from '@/components/search/SearchResultsTable';
import DocumentPreviewModal from '@/components/search/DocumentPreviewModal';
import ExportOptions from '@/components/search/ExportOptions';

export default function DocumentSearchPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    documentType: [],
    uploadDateRange: { start: null, end: null },
    processingStatus: [],
    customTags: []
  });
  const [sortBy, setSortBy] = useState('relevance');
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [showPreview, setShowPreview] = useState(false);

  const handleSearch = (query: string) => {
    setSearchQuery(query);
  };

  const handleDocumentClick = (document: any) => {
    setSelectedDocument(document);
    setShowPreview(true);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Document Search</h1>
          <p className="text-muted-foreground">
            Search and explore the knowledge base
          </p>
        </div>
        
        <ExportOptions searchQuery={searchQuery} filters={filters} />
      </div>

      {/* Search Bar */}
      <SearchBar onSearch={handleSearch} />

      {/* Advanced Filters */}
      <AdvancedFilters filters={filters} onFilterChange={setFilters} />

      {/* Search Results */}
      <SearchResultsTable
        query={searchQuery}
        filters={filters}
        sortBy={sortBy}
        onSortChange={setSortBy}
        onDocumentClick={handleDocumentClick}
      />

      {/* Document Preview Modal */}
      {showPreview && selectedDocument && (
        <DocumentPreviewModal
          document={selectedDocument}
          onClose={() => setShowPreview(false)}
        />
      )}
    </div>
  );
}


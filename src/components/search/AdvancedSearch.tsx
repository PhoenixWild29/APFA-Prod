/**
 * Advanced Search Component
 * 
 * Features:
 * - Multi-field filtering
 * - Sort options
 * - Fast, relevant results
 * - Debounced search
 */
import React, { useState, useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import debounce from 'lodash/debounce';

interface AdvancedSearchProps {
  onSearch: (query: string, filters: any, sort: any) => void;
  filterOptions?: Record<string, string[]>;
  sortOptions?: Array<{ value: string; label: string }>;
}

export const AdvancedSearch: React.FC<AdvancedSearchProps> = ({
  onSearch,
  filterOptions = {},
  sortOptions = []
}) => {
  const { t } = useTranslation();
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [sortBy, setSortBy] = useState('relevance');
  const [showFilters, setShowFilters] = useState(false);

  // Debounced search (300ms delay)
  const debouncedSearch = useMemo(
    () => debounce((q: string, f: any, s: string) => {
      onSearch(q, f, { field: s, direction: 'desc' });
    }, 300),
    [onSearch]
  );

  const handleQueryChange = useCallback((value: string) => {
    setQuery(value);
    debouncedSearch(value, filters, sortBy);
  }, [filters, sortBy, debouncedSearch]);

  const handleFilterChange = useCallback((key: string, value: string) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    debouncedSearch(query, newFilters, sortBy);
  }, [query, filters, sortBy, debouncedSearch]);

  const handleSortChange = useCallback((value: string) => {
    setSortBy(value);
    debouncedSearch(query, filters, value);
  }, [query, filters, debouncedSearch]);

  return (
    <div className="advanced-search" role="search">
      {/* Main search input */}
      <div className="search-bar">
        <input
          type="search"
          value={query}
          onChange={(e) => handleQueryChange(e.target.value)}
          placeholder={t('documents.search')}
          aria-label="Search query"
          className="search-input"
        />
        
        <button
          onClick={() => setShowFilters(!showFilters)}
          aria-label="Toggle filters"
          aria-expanded={showFilters}
        >
          🔍 Filters
        </button>
      </div>

      {/* Advanced filters */}
      {showFilters && (
        <div className="filter-panel" role="region" aria-label="Search filters">
          {Object.entries(filterOptions).map(([key, options]) => (
            <div key={key} className="filter-group">
              <label htmlFor={`filter-${key}`}>{key}</label>
              <select
                id={`filter-${key}`}
                value={filters[key] || ''}
                onChange={(e) => handleFilterChange(key, e.target.value)}
                aria-label={`Filter by ${key}`}
              >
                <option value="">All</option>
                {options.map(opt => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            </div>
          ))}

          {/* Sort options */}
          <div className="sort-group">
            <label htmlFor="sort-by">Sort by</label>
            <select
              id="sort-by"
              value={sortBy}
              onChange={(e) => handleSortChange(e.target.value)}
              aria-label="Sort results"
            >
              {sortOptions.map(opt => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}
    </div>
  );
};


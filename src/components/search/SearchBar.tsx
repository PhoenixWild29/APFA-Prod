/**
 * Search Bar Component
 * 
 * Full-text search with auto-complete and search history
 */
import React, { useState, useEffect } from 'react';
import { Search, Clock } from 'lucide-react';

interface SearchBarProps {
  onSearch: (query: string) => void;
}

export default function SearchBar({ onSearch }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  useEffect(() => {
    // Load search history from localStorage
    const history = localStorage.getItem('searchHistory');
    if (history) {
      setSearchHistory(JSON.parse(history));
    }
  }, []);

  useEffect(() => {
    if (query.length >= 3) {
      fetchSuggestions(query);
    } else {
      setSuggestions([]);
    }
  }, [query]);

  const fetchSuggestions = async (q: string) => {
    try {
      const response = await fetch(`/api/documents/search/suggestions?q=${q}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      const data = await response.json();
      setSuggestions(data.suggestions || []);
    } catch (error) {
      console.error('Error fetching suggestions:', error);
    }
  };

  const handleSearch = (searchTerm: string) => {
    if (searchTerm.length < 3) {
      return;
    }

    // Add to search history
    const newHistory = [searchTerm, ...searchHistory.filter(h => h !== searchTerm)].slice(0, 10);
    setSearchHistory(newHistory);
    localStorage.setItem('searchHistory', JSON.stringify(newHistory));

    onSearch(searchTerm);
    setShowSuggestions(false);
  };

  return (
    <div className="relative">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search documents... (min 3 characters)"
          className="w-full rounded-lg border bg-background pl-10 pr-4 py-3 text-lg"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch(query)}
          onFocus={() => setShowSuggestions(true)}
          maxLength={500}
        />
      </div>

      {/* Suggestions & History */}
      {showSuggestions && (suggestions.length > 0 || searchHistory.length > 0) && (
        <div className="absolute z-10 mt-2 w-full rounded-lg border bg-card shadow-lg">
          {/* Auto-complete Suggestions */}
          {suggestions.length > 0 && (
            <div className="border-b p-2">
              <p className="mb-2 px-2 text-xs font-semibold uppercase text-muted-foreground">
                Suggestions
              </p>
              {suggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  className="w-full rounded-md px-3 py-2 text-left hover:bg-muted"
                  onClick={() => {
                    setQuery(suggestion);
                    handleSearch(suggestion);
                  }}
                >
                  <Search className="mr-2 inline h-4 w-4" />
                  {suggestion}
                </button>
              ))}
            </div>
          )}

          {/* Search History */}
          {searchHistory.length > 0 && (
            <div className="p-2">
              <p className="mb-2 px-2 text-xs font-semibold uppercase text-muted-foreground">
                Recent Searches
              </p>
              {searchHistory.slice(0, 5).map((item, idx) => (
                <button
                  key={idx}
                  className="w-full rounded-md px-3 py-2 text-left hover:bg-muted"
                  onClick={() => {
                    setQuery(item);
                    handleSearch(item);
                  }}
                >
                  <Clock className="mr-2 inline h-4 w-4" />
                  {item}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}


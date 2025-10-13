/**
 * Optimized Component with React.memo
 * 
 * Demonstrates performance optimization:
 * - Prevents unnecessary re-renders
 * - Custom comparison function
 * - Memoized callbacks
 */
import React, { memo, useCallback, useMemo } from 'react';

interface OptimizedComponentProps {
  data: any[];
  onItemClick: (item: any) => void;
  filterCriteria?: string;
}

/**
 * Expensive component optimized with React.memo
 */
export const OptimizedDataList = memo<OptimizedComponentProps>(
  ({ data, onItemClick, filterCriteria }) => {
    // Memoize filtered data
    const filteredData = useMemo(() => {
      if (!filterCriteria) return data;
      
      return data.filter(item => 
        JSON.stringify(item).toLowerCase().includes(filterCriteria.toLowerCase())
      );
    }, [data, filterCriteria]);

    // Memoize callback
    const handleItemClick = useCallback((item: any) => {
      onItemClick(item);
    }, [onItemClick]);

    return (
      <div className="optimized-data-list" role="list">
        {filteredData.map((item, index) => (
          <OptimizedDataItem
            key={item.id || index}
            item={item}
            onClick={handleItemClick}
          />
        ))}
      </div>
    );
  },
  // Custom comparison function
  (prevProps, nextProps) => {
    return (
      prevProps.data === nextProps.data &&
      prevProps.filterCriteria === nextProps.filterCriteria &&
      prevProps.onItemClick === nextProps.onItemClick
    );
  }
);

/**
 * Optimized individual item component
 */
const OptimizedDataItem = memo<{
  item: any;
  onClick: (item: any) => void;
}>(({ item, onClick }) => {
  return (
    <div 
      className="data-item" 
      onClick={() => onClick(item)}
      role="listitem"
      tabIndex={0}
      onKeyPress={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          onClick(item);
        }
      }}
    >
      <h3>{item.title}</h3>
      <p>{item.description}</p>
    </div>
  );
});

OptimizedDataItem.displayName = 'OptimizedDataItem';
OptimizedDataList.displayName = 'OptimizedDataList';


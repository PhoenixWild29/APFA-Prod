/**
 * Virtual Scroll List Component
 * 
 * Efficient rendering for large datasets (10,000+ items)
 * using react-window for performance optimization
 */
import React from 'react';
import { FixedSizeList as List } from 'react-window';

interface VirtualScrollListProps<T> {
  items: T[];
  height: number;
  itemSize: number;
  renderItem: (item: T, index: number) => React.ReactNode;
}

export function VirtualScrollList<T>({ 
  items, 
  height, 
  itemSize, 
  renderItem 
}: VirtualScrollListProps<T>) {
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => (
    <div style={style}>
      {renderItem(items[index], index)}
    </div>
  );

  return (
    <List
      height={height}
      itemCount={items.length}
      itemSize={itemSize}
      width="100%"
    >
      {Row}
    </List>
  );
}

/**
 * Example usage:
 * 
 * <VirtualScrollList
 *   items={documents}
 *   height={600}
 *   itemSize={50}
 *   renderItem={(doc, idx) => (
 *     <div key={idx}>{doc.title}</div>
 *   )}
 * />
 */


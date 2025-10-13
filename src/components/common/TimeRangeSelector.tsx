/**
 * Time Range Selector Component
 * 
 * Reusable component for:
 * - Chart filtering
 * - Time range selection
 * - Custom date range support
 */
import React, { useState } from 'react';

interface TimeRangeSelectorProps {
  onRangeChange: (range: { start: Date; end: Date; preset: string }) => void;
  defaultPreset?: string;
}

export const TimeRangeSelector: React.FC<TimeRangeSelectorProps> = ({ 
  onRangeChange,
  defaultPreset = '1h'
}) => {
  const [selectedPreset, setSelectedPreset] = useState(defaultPreset);
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');

  const presets = [
    { value: '1h', label: 'Last Hour' },
    { value: '24h', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' },
    { value: 'custom', label: 'Custom Range' }
  ];

  const handlePresetChange = (preset: string) => {
    setSelectedPreset(preset);
    
    if (preset !== 'custom') {
      const end = new Date();
      const start = new Date();
      
      switch (preset) {
        case '1h':
          start.setHours(start.getHours() - 1);
          break;
        case '24h':
          start.setHours(start.getHours() - 24);
          break;
        case '7d':
          start.setDate(start.getDate() - 7);
          break;
        case '30d':
          start.setDate(start.getDate() - 30);
          break;
      }
      
      onRangeChange({ start, end, preset });
    }
  };

  const handleCustomRange = () => {
    if (customStart && customEnd) {
      onRangeChange({
        start: new Date(customStart),
        end: new Date(customEnd),
        preset: 'custom'
      });
    }
  };

  return (
    <div className="time-range-selector">
      <div className="preset-buttons">
        {presets.map(preset => (
          <button
            key={preset.value}
            className={selectedPreset === preset.value ? 'active' : ''}
            onClick={() => handlePresetChange(preset.value)}
          >
            {preset.label}
          </button>
        ))}
      </div>
      
      {selectedPreset === 'custom' && (
        <div className="custom-range">
          <input
            type="datetime-local"
            value={customStart}
            onChange={(e) => setCustomStart(e.target.value)}
            placeholder="Start time"
          />
          <span>to</span>
          <input
            type="datetime-local"
            value={customEnd}
            onChange={(e) => setCustomEnd(e.target.value)}
            placeholder="End time"
          />
          <button onClick={handleCustomRange} className="btn-primary">
            Apply
          </button>
        </div>
      )}
    </div>
  );
};


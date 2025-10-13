/**
 * Processing History Timeline Component
 * 
 * Visualizes document processing lifecycle
 */
import React from 'react';

interface ProcessingHistoryTimelineProps {
  filters: any;
}

export default function ProcessingHistoryTimeline({ filters }: ProcessingHistoryTimelineProps) {
  const events = [
    {
      id: 1,
      stage: 'Uploaded',
      timestamp: '2025-10-12 10:00:00',
      status: 'completed',
      duration: '0s'
    },
    {
      id: 2,
      stage: 'Text Extraction',
      timestamp: '2025-10-12 10:00:05',
      status: 'completed',
      duration: '8.5s'
    },
    {
      id: 3,
      stage: 'Embedding Generation',
      timestamp: '2025-10-12 10:00:15',
      status: 'completed',
      duration: '9.2s'
    },
    {
      id: 4,
      stage: 'Indexing',
      timestamp: '2025-10-12 10:00:25',
      status: 'completed',
      duration: '4.8s'
    }
  ];

  return (
    <div className="rounded-lg border bg-card p-6">
      <h3 className="mb-6 text-lg font-semibold">Processing History</h3>
      
      <div className="relative space-y-4 pl-8">
        {/* Timeline line */}
        <div className="absolute left-3 top-0 h-full w-0.5 bg-border" />
        
        {events.map((event, index) => (
          <div key={event.id} className="relative">
            {/* Timeline dot */}
            <div className={`absolute -left-[1.6rem] top-1.5 h-3 w-3 rounded-full border-2 ${
              event.status === 'completed' ? 'border-green-500 bg-green-500' :
              event.status === 'processing' ? 'border-blue-500 bg-blue-500' :
              'border-red-500 bg-red-500'
            }`} />
            
            {/* Event card */}
            <div className="rounded-lg border bg-card p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-medium">{event.stage}</p>
                  <p className="text-sm text-muted-foreground">{event.timestamp}</p>
                </div>
                <div className="text-right">
                  <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                    event.status === 'completed' ? 'bg-green-100 text-green-800' :
                    event.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {event.status}
                  </span>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Duration: {event.duration}
                  </p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}


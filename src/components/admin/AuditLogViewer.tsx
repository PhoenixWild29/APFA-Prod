/**
 * Audit Log Viewer Component
 * 
 * Displays:
 * - Administrative action logs
 * - Timestamps and user information
 * - Filtering and search capabilities
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface AuditLogEntry {
  id: string;
  timestamp: string;
  user_id: string;
  action: string;
  resource: string;
  details: Record<string, any>;
  ip_address: string;
}

export const AuditLogViewer: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [filter, setFilter] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    fetchLogs();
  }, [page, filter]);

  const fetchLogs = async () => {
    try {
      const response = await axios.get('/admin/audit-logs', {
        params: { page, filter, per_page: 50 }
      });
      setLogs(response.data.logs);
      setTotalPages(response.data.total_pages);
    } catch (error) {
      console.error('Failed to fetch audit logs:', error);
    }
  };

  return (
    <div className="audit-log-viewer">
      <h2>Audit Logs</h2>
      
      <div className="controls">
        <input
          type="text"
          placeholder="Filter logs (user, action, resource)..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="filter-input"
        />
      </div>

      <table className="audit-table">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>User</th>
            <th>Action</th>
            <th>Resource</th>
            <th>IP Address</th>
            <th>Details</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <tr key={log.id}>
              <td>{new Date(log.timestamp).toLocaleString()}</td>
              <td>{log.user_id}</td>
              <td>
                <span className={`action-badge ${log.action}`}>
                  {log.action}
                </span>
              </td>
              <td>{log.resource}</td>
              <td>{log.ip_address}</td>
              <td>
                <details>
                  <summary>View</summary>
                  <pre>{JSON.stringify(log.details, null, 2)}</pre>
                </details>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="pagination">
        <button
          onClick={() => setPage(p => Math.max(1, p - 1))}
          disabled={page === 1}
        >
          Previous
        </button>
        <span>Page {page} of {totalPages}</span>
        <button
          onClick={() => setPage(p => Math.min(totalPages, p + 1))}
          disabled={page === totalPages}
        >
          Next
        </button>
      </div>
    </div>
  );
};


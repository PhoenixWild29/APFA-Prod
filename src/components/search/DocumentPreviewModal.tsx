/**
 * Document Preview Modal
 * 
 * Preview document content without download
 */
import React, { useState, useEffect } from 'react';
import { X, Download, History, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface DocumentPreviewModalProps {
  document: any;
  onClose: () => void;
}

export default function DocumentPreviewModal({ document, onClose }: DocumentPreviewModalProps) {
  const [activeTab, setActiveTab] = useState<'preview' | 'versions' | 'audit'>('preview');
  const [versions, setVersions] = useState([]);
  const [auditTrail, setAuditTrail] = useState([]);

  useEffect(() => {
    if (activeTab === 'versions') {
      fetchVersionHistory();
    } else if (activeTab === 'audit') {
      fetchAuditTrail();
    }
  }, [activeTab]);

  const fetchVersionHistory = async () => {
    try {
      const response = await fetch(
        `/api/documents/${document.document_id}/versions`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );
      const data = await response.json();
      setVersions(data.versions || []);
    } catch (error) {
      console.error('Error fetching versions:', error);
    }
  };

  const fetchAuditTrail = async () => {
    try {
      const response = await fetch(
        `/api/documents/${document.document_id}/audit-trail`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );
      const data = await response.json();
      setAuditTrail(data.audit_trail || []);
    } catch (error) {
      console.error('Error fetching audit trail:', error);
    }
  };

  const handleDownload = () => {
    window.open(`/api/documents/${document.document_id}/download`, '_blank');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="h-[90vh] w-[90vw] max-w-6xl rounded-lg bg-card">
        {/* Header */}
        <div className="flex items-center justify-between border-b p-4">
          <div>
            <h2 className="text-xl font-bold">{document.document_metadata.filename}</h2>
            <p className="text-sm text-muted-foreground">
              {document.document_metadata.document_type} • {(document.relevance_score * 100).toFixed(0)}% match
            </p>
          </div>
          
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleDownload}>
              <Download className="mr-2 h-4 w-4" />
              Download
            </Button>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b">
          <div className="flex gap-4 px-4">
            <button
              className={`border-b-2 px-4 py-3 text-sm font-medium ${
                activeTab === 'preview'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
              onClick={() => setActiveTab('preview')}
            >
              Preview
            </button>
            <button
              className={`border-b-2 px-4 py-3 text-sm font-medium ${
                activeTab === 'versions'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
              onClick={() => setActiveTab('versions')}
            >
              <History className="mr-2 inline h-4 w-4" />
              Version History
            </button>
            <button
              className={`border-b-2 px-4 py-3 text-sm font-medium ${
                activeTab === 'audit'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
              onClick={() => setActiveTab('audit')}
            >
              <Clock className="mr-2 inline h-4 w-4" />
              Audit Trail
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="overflow-y-auto p-6" style={{ height: 'calc(90vh - 160px)' }}>
          {activeTab === 'preview' && (
            <div className="prose max-w-none">
              <p className="whitespace-pre-wrap">{document.snippet}</p>
              <p className="mt-4 text-sm text-muted-foreground">
                Full content preview would appear here
              </p>
            </div>
          )}

          {activeTab === 'versions' && (
            <div className="space-y-4">
              {versions.length === 0 ? (
                <p className="text-center text-muted-foreground">No version history available</p>
              ) : (
                versions.map((version: any, idx: number) => (
                  <div key={idx} className="rounded-lg border p-4">
                    <p className="font-semibold">Version {version.version}</p>
                    <p className="text-sm text-muted-foreground">{version.timestamp}</p>
                    <p className="mt-2 text-sm">{version.changes}</p>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'audit' && (
            <div className="space-y-4">
              {auditTrail.length === 0 ? (
                <p className="text-center text-muted-foreground">No audit trail available</p>
              ) : (
                auditTrail.map((entry: any, idx: number) => (
                  <div key={idx} className="flex gap-4 rounded-lg border p-4">
                    <div className="flex-1">
                      <p className="font-semibold">{entry.action}</p>
                      <p className="text-sm text-muted-foreground">
                        by {entry.user} • {new Date(entry.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


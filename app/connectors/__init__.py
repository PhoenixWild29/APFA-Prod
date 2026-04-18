"""APFA data pipeline connectors.

Two connector families:
- RAGSource: text documents → chunk → embed → DeltaTable → FAISS
  (Google Drive, YouTube transcripts)
- StructuredDataSource: numeric data → structured store → agent tools
  (Finnhub, Mboum, CoinMarketCap)

All connectors are admin-only (single curator model, not per-tenant).
"""

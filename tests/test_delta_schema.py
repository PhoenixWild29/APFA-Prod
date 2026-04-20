"""Tests for DELTA_SCHEMA round-trip: NormalizedRecord → DataFrame → Arrow.

Verifies that:
1. build_delta_schema produces a valid PyArrow schema
2. A NormalizedRecord can be converted to a DataFrame that conforms to the schema
3. The Arrow table preserves types correctly (especially embedding_vector as list<float32>)
4. _conform_df_to_schema adds missing columns and drops extras
"""

import numpy as np
import pandas as pd
import pyarrow as pa
import pytest


def test_build_delta_schema_structure():
    """Schema has all expected columns with correct types."""
    from app.connectors.base import build_delta_schema

    schema = build_delta_schema(embedding_dim=384)

    # Check key columns exist
    names = [f.name for f in schema]
    assert "document_id" in names
    assert "chunk_id" in names
    assert "profile" in names
    assert "embedding_vector" in names
    assert "content_hash" in names
    assert "source_connector" in names
    assert "metadata_json" in names

    # Check embedding_vector type is fixed-size list of float32
    emb_field = schema.field("embedding_vector")
    assert isinstance(emb_field.type, pa.FixedSizeListType)
    assert emb_field.type.value_type == pa.float32()
    assert emb_field.type.list_size == 384


def test_normalized_record_to_arrow_round_trip():
    """NormalizedRecord → dict → DataFrame → Arrow → types match."""
    from app.connectors.base import NormalizedRecord, build_delta_schema
    from app.services.delta_writer import _conform_df_to_schema

    schema = build_delta_schema(embedding_dim=3)  # small dim for test

    record = NormalizedRecord(
        external_id="test:abc:0",
        source_type="manual",
        source_url="https://example.com",
        title="Test Doc",
        author="Test Author",
        published_at="2026-04-20T00:00:00Z",
        fetched_at="2026-04-20T00:00:00Z",
        freshness_class="static",
        content_kind="doc_section",
        text="This is test content.",
        chunk_index=0,
        total_chunks=1,
        parent_document_id="test:abc",
    )

    # Build a row dict matching what delta_writer produces
    row = {
        "document_id": record.parent_document_id,
        "chunk_id": record.external_id,
        "filename": record.title,
        "document_type": record.content_kind,
        "source": record.author,
        "creation_date": "2026-04-20",
        "file_size_bytes": len(record.text.encode()),
        "profile": record.text,
        "embedding_vector": [0.1, 0.2, 0.3],  # 3-dim for test
        "embedding_model": "test-model",
        "content_hash": "abc123",
        "embedded_at": "2026-04-20T00:00:00Z",
        "external_id": record.external_id,
        "source_connector": record.source_type,
        "source_url": record.source_url,
        "parent_document_id": record.parent_document_id,
        "chunk_index": record.chunk_index,
        "total_chunks": record.total_chunks,
        "ingested_at": "2026-04-20T00:00:00Z",
        "ttl_hours": None,
        "freshness_class": record.freshness_class,
        "content_kind": record.content_kind,
        "metadata_json": "{}",
    }

    df = pd.DataFrame([row])
    conformed = _conform_df_to_schema(df, schema)
    table = pa.Table.from_pandas(conformed, schema=schema, preserve_index=False)

    # Verify types
    assert table.schema.field("embedding_vector").type == pa.list_(pa.float32(), 3)
    assert table.schema.field("profile").type == pa.string()
    assert table.schema.field("chunk_index").type == pa.int64()
    assert table.num_rows == 1

    # Verify embedding values survived
    emb = table.column("embedding_vector")[0].as_py()
    assert len(emb) == 3
    assert all(isinstance(v, float) for v in emb)


def test_conform_adds_missing_columns():
    """_conform_df_to_schema adds missing columns with None."""
    from app.connectors.base import build_delta_schema
    from app.services.delta_writer import _conform_df_to_schema

    schema = build_delta_schema(embedding_dim=3)
    df = pd.DataFrame([{"chunk_id": "test", "profile": "hello"}])

    conformed = _conform_df_to_schema(df, schema)
    assert set(conformed.columns) == {f.name for f in schema}
    assert conformed["document_id"].iloc[0] is None


def test_conform_drops_extra_columns():
    """_conform_df_to_schema drops columns not in schema (with warning)."""
    from app.connectors.base import build_delta_schema
    from app.services.delta_writer import _conform_df_to_schema

    schema = build_delta_schema(embedding_dim=3)
    df = pd.DataFrame([{
        "chunk_id": "test",
        "profile": "hello",
        "totally_fake_column": "should be dropped",
    }])

    conformed = _conform_df_to_schema(df, schema)
    assert "totally_fake_column" not in conformed.columns


def test_embedding_float32_enforcement():
    """_conform_df_to_schema converts embedding vectors to float32."""
    from app.connectors.base import build_delta_schema
    from app.services.delta_writer import _conform_df_to_schema

    schema = build_delta_schema(embedding_dim=3)
    df = pd.DataFrame([{
        "chunk_id": "test",
        "profile": "hello",
        "embedding_vector": [1.0, 2.0, 3.0],  # Python floats (float64)
    }])

    conformed = _conform_df_to_schema(df, schema)
    vec = conformed["embedding_vector"].iloc[0]
    arr = np.array(vec)
    assert arr.dtype == np.float32

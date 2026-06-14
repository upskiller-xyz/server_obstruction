"""Unit tests for NpyMeshDecoder (binary mesh decoding + safety guards)."""

import gzip
import io

import numpy as np
import pytest
from werkzeug.exceptions import BadRequest

from src.server.services.mesh_decoder import NpyMeshDecoder


def _npy(verts) -> bytes:
    buf = io.BytesIO()
    np.save(buf, np.asarray(verts, dtype=np.float32))
    return buf.getvalue()


@pytest.fixture
def decoder():
    return NpyMeshDecoder()


def test_decodes_npy_to_vertex_list(decoder):
    out = decoder.decode(_npy([[0, 0, 0], [1, 0, 0], [0, 1, 0]]))
    assert out == [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]


def test_decodes_gzipped_npy(decoder):
    out = decoder.decode(gzip.compress(_npy([[0, 0, 0], [1, 0, 0], [0, 1, 0]])))
    assert len(out) == 3


def test_empty_payload_rejected(decoder):
    with pytest.raises(BadRequest):
        decoder.decode(b"")


def test_corrupt_gzip_rejected(decoder):
    with pytest.raises(BadRequest):
        decoder.decode(b"\x1f\x8bnot-a-real-gzip-stream")


def test_npz_archive_rejected(decoder):
    buf = io.BytesIO()
    np.savez(buf, a=np.zeros((3, 3), dtype=np.float32))
    with pytest.raises(BadRequest):
        decoder.decode(buf.getvalue())


def test_wrong_shape_rejected(decoder):
    with pytest.raises(BadRequest):
        decoder.decode(_npy([[0, 0], [1, 0], [0, 1]]))  # (N, 2), not (N, 3)


def test_zip_bomb_capped(decoder, monkeypatch):
    """A gzip payload whose output exceeds the cap is rejected (DoS guard)."""
    # Lower the cap so the test stays cheap; 1 MB of zeros gzips to a few KB.
    monkeypatch.setattr(decoder, "_MAX_MESH_BYTES", 1024)
    big = gzip.compress(_npy(np.zeros((30000, 3))))  # well over 1 KB decompressed
    with pytest.raises(BadRequest):
        decoder.decode(big)


def test_raw_npy_size_capped(decoder, monkeypatch):
    """An oversized *uncompressed* .npy payload is rejected (DoS guard)."""
    monkeypatch.setattr(decoder, "_MAX_MESH_BYTES", 1024)
    with pytest.raises(BadRequest):
        decoder.decode(_npy(np.zeros((30000, 3))))

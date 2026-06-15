"""Mesh payload decoders (Strategy Pattern).

The binary obstruction endpoint accepts the mesh as a NumPy ``.npy`` payload
(optionally gzip-compressed) in a multipart body instead of an inline JSON
array. These decoders return the mesh as an ``(N, 3)`` numpy array; the
validation pipeline and ``Mesh`` are numpy-aware, so the binary path stays numpy
end-to-end (no list round-trip). The JSON contract path is untouched.
"""

import gzip
import io
from abc import ABC, abstractmethod

import numpy as np
from werkzeug.exceptions import BadRequest


class MeshDecoder(ABC):
    """Decode a raw mesh payload into an (N, 3) vertex array."""

    @abstractmethod
    def decode(self, payload: bytes) -> np.ndarray:
        ...


class NpyMeshDecoder(MeshDecoder):
    """Decode a NumPy ``.npy`` mesh payload, transparently gunzipping it.

    The mesh is an ``(N, 3)`` float array of vertices (three per triangle).
    Returns the array as-is — the validators and ``Mesh`` consume numpy directly,
    so there is no list↔array round-trip (the old ~1.5s validation + 0.1s rebuild).
    """

    _GZIP_MAGIC = b"\x1f\x8b"
    # Cap the mesh size to bound memory (DoS guard). Applies to both a raw .npy
    # payload and the *decompressed* output of a gzip payload (which can expand
    # enormously — zip bomb). 512 MB comfortably fits real meshes (a 474k-triangle
    # mesh is ~17 MB as float32 .npy) while rejecting pathological input.
    _MAX_MESH_BYTES = 512 * 1024 * 1024

    def decode(self, payload: bytes) -> np.ndarray:
        if not payload:
            raise BadRequest("Mesh payload cannot be empty")

        if payload[:2] == self._GZIP_MAGIC:
            payload = self._gunzip_bounded(payload)

        # Bound the raw (uncompressed) payload too — np.load on a huge buffer would
        # otherwise spike memory. (The gzip path is already bounded above.)
        if len(payload) > self._MAX_MESH_BYTES:
            raise BadRequest("Mesh payload exceeds the maximum allowed size")

        try:
            array = np.load(io.BytesIO(payload), allow_pickle=False)
        except Exception as e:
            raise BadRequest(f"Invalid .npy mesh payload: {e}")

        # np.load also accepts .npz archives (→ NpzFile, not an ndarray); reject
        # those explicitly so we don't fail later with an opaque AttributeError.
        if not isinstance(array, np.ndarray):
            raise BadRequest(
                "Mesh payload must be a single .npy array, not an .npz archive"
            )

        if array.ndim != 2 or array.shape[1] != 3:
            raise BadRequest(
                f"Mesh array must have shape (N, 3), got {tuple(array.shape)}"
            )

        return array

    def _gunzip_bounded(self, payload: bytes) -> bytes:
        """Decompress a gzip payload, capping output to guard against zip bombs.

        Reads at most ``_MAX_DECOMPRESSED_BYTES + 1`` so memory stays bounded even
        for a malicious payload; exceeding the cap (or a corrupt stream) is a 400.
        """
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(payload)) as gz:
                data = gz.read(self._MAX_MESH_BYTES + 1)
        except (OSError, EOFError) as e:
            raise BadRequest(f"Invalid gzip mesh payload: {e}")

        if len(data) > self._MAX_MESH_BYTES:
            raise BadRequest("Decompressed mesh exceeds the maximum allowed size")

        return data

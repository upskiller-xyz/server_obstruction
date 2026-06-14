"""Mesh payload decoders (Strategy Pattern).

The binary obstruction endpoint accepts the mesh as a NumPy ``.npy`` payload
(optionally gzip-compressed) in a multipart body instead of an inline JSON
array. These decoders turn that payload into the plain list-of-vertices
structure the existing validation pipeline and ``Mesh.from_vertices`` expect,
so the JSON contract path stays completely untouched — only transport differs.
"""

import gzip
import io
from abc import ABC, abstractmethod
from typing import List

import numpy as np
from werkzeug.exceptions import BadRequest


class MeshDecoder(ABC):
    """Decode a raw mesh payload into a list of ``[x, y, z]`` vertices."""

    @abstractmethod
    def decode(self, payload: bytes) -> List[list]:
        ...


class NpyMeshDecoder(MeshDecoder):
    """Decode a NumPy ``.npy`` mesh payload, transparently gunzipping it.

    The mesh is an ``(N, 3)`` float array of vertices (three per triangle).
    Returns a plain Python list because the validators mutate it in place and
    ``Mesh.from_vertices`` indexes it row-wise — keeping behaviour identical to
    the JSON path, only without the multi-second JSON parse.
    """

    _GZIP_MAGIC = b"\x1f\x8b"
    # Cap the decompressed mesh to bound memory: a small gzip payload can expand
    # enormously (zip-bomb / DoS). 512 MB comfortably fits real meshes (a 474k-
    # triangle mesh is ~17 MB as float32 .npy) while rejecting pathological input.
    _MAX_DECOMPRESSED_BYTES = 512 * 1024 * 1024

    def decode(self, payload: bytes) -> List[list]:
        if not payload:
            raise BadRequest("Mesh payload cannot be empty")

        if payload[:2] == self._GZIP_MAGIC:
            payload = self._gunzip_bounded(payload)

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

        return array.tolist()

    def _gunzip_bounded(self, payload: bytes) -> bytes:
        """Decompress a gzip payload, capping output to guard against zip bombs.

        Reads at most ``_MAX_DECOMPRESSED_BYTES + 1`` so memory stays bounded even
        for a malicious payload; exceeding the cap (or a corrupt stream) is a 400.
        """
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(payload)) as gz:
                data = gz.read(self._MAX_DECOMPRESSED_BYTES + 1)
        except (OSError, EOFError) as e:
            raise BadRequest(f"Invalid gzip mesh payload: {e}")

        if len(data) > self._MAX_DECOMPRESSED_BYTES:
            raise BadRequest("Decompressed mesh exceeds the maximum allowed size")

        return data

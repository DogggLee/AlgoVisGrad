from __future__ import annotations

import base64
import io
import json

import numpy as np
from PIL import Image

from utils.resource_utils import load_manifest, pack_resource


def test_load_manifest_reads_resource_items(tmp_path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            [
                {
                    "id": "street_001",
                    "name": "Street 001",
                    "preview": "images/street_001.png",
                    "data": "images/street_001.png",
                    "content_type": "image/png",
                }
            ]
        ),
        encoding="utf-8",
    )

    items = load_manifest(tmp_path)

    assert items == [
        {
            "id": "street_001",
            "name": "Street 001",
            "preview": "images/street_001.png",
            "data": "images/street_001.png",
            "content_type": "image/png",
        }
    ]


def test_pack_resource_encodes_image_file_as_base64_payload(tmp_path) -> None:
    image_path = tmp_path / "street_001.png"
    image = Image.new("RGB", (2, 2), color=(0, 255, 0))
    image.save(image_path)

    payload = pack_resource(
        tmp_path,
        {
            "id": "street_001",
            "name": "Street 001",
            "preview": "street_001.png",
            "data": "street_001.png",
            "content_type": "image/png",
        },
    )

    decoded = Image.open(io.BytesIO(base64.b64decode(payload["data"])))
    assert payload["content_type"] == "image/png"
    assert payload["filename"] == "street_001.png"
    assert decoded.size == (2, 2)

def test_pack_resource_keeps_array_list_data_as_json_value(tmp_path) -> None:
    map_path = tmp_path / "warehouse_01.json"
    map_path.write_text(json.dumps([[[0, 0, 0], [255, 255, 255]]]), encoding="utf-8")

    payload = pack_resource(
        tmp_path,
        {
            "id": "warehouse_01",
            "name": "Warehouse 01",
            "preview": "warehouse_01.png",
            "data": "warehouse_01.json",
            "content_type": "array/list",
            "shape": [1, 2, 3],
            "dtype": "uint8",
        },
    )

    assert payload == {
        "content_type": "array/list",
        "filename": "warehouse_01.json",
        "shape": [1, 2, 3],
        "dtype": "uint8",
        "data": [[[0, 0, 0], [255, 255, 255]]],
    }

def test_pack_resource_encodes_array_npy_file_as_base64_payload(tmp_path) -> None:
    map_path = tmp_path / "warehouse_01.npy"
    array = np.array([[[1, 2, 3], [4, 5, 6]]], dtype=np.uint8)
    np.save(map_path, array)

    payload = pack_resource(
        tmp_path,
        {
            "id": "warehouse_01",
            "name": "Warehouse 01",
            "preview": "warehouse_01.png",
            "data": "warehouse_01.npy",
            "content_type": "array/npy",
            "shape": [1, 2, 3],
            "dtype": "uint8",
        },
    )

    decoded_path = tmp_path / "decoded.npy"
    decoded_path.write_bytes(base64.b64decode(payload["data"]))
    decoded_array = np.load(decoded_path)

    assert payload["content_type"] == "array/npy"
    assert payload["filename"] == "warehouse_01.npy"
    assert payload["shape"] == [1, 2, 3]
    assert payload["dtype"] == "uint8"
    assert np.array_equal(decoded_array, array)


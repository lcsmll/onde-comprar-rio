"""
Funcoes para baixar camadas do servidor ArcGIS da Prefeitura do Rio (pgeo3.rio.rj.gov.br),
que e onde o Data.Rio guarda os mapas.

Por que existe: o ArcGIS devolve no maximo ~1000-2000 registros por pedido.
Esta funcao pede em "paginas" ate acabar e junta tudo num GeoDataFrame.
"""
import json
import time
import urllib.parse
from datetime import datetime, timezone

import geopandas as gpd
import requests

BASE = "https://pgeo3.rio.rj.gov.br/arcgis/rest/services"
HEADERS = {"User-Agent": "onde-comprar-rio-etl/0.1"}


def layer_url(path: str) -> str:
    """path no formato 'Pasta/Servico/MapServer/4'."""
    return f"{BASE}/{urllib.parse.quote(path)}"


def layer_info(path: str) -> dict:
    """Metadados da camada: campos, tipo de geometria e data da ultima edicao."""
    r = requests.get(layer_url(path), params={"f": "json"}, headers=HEADERS, timeout=60)
    r.raise_for_status()
    info = r.json()
    last = (info.get("editingInfo") or {}).get("lastEditDate")
    info["_last_edit_iso"] = (
        datetime.fromtimestamp(last / 1000, tz=timezone.utc).date().isoformat() if last else None
    )
    return info


def download_layer(path: str, where: str = "1=1", out_fields: str = "*", page_size: int = 1000,
                   max_records: int | None = None) -> gpd.GeoDataFrame:
    """Baixa a camada inteira (ou ate max_records) em WGS84 (EPSG:4326)."""
    url = layer_url(path) + "/query"
    feats, offset = [], 0
    while True:
        params = {
            "where": where, "outFields": out_fields, "outSR": 4326, "f": "geojson",
            "resultOffset": offset, "resultRecordCount": page_size,
        }
        for tentativa in range(3):
            try:
                r = requests.get(url, params=params, headers=HEADERS, timeout=180)
                r.raise_for_status()
                data = r.json()
                break
            except Exception:
                if tentativa == 2:
                    raise
                time.sleep(3)
        batch = data.get("features", [])
        feats.extend(batch)
        offset += len(batch)
        if not batch or len(batch) < page_size and not data.get("exceededTransferLimit"):
            break
        if max_records and offset >= max_records:
            break
    if not feats:
        return gpd.GeoDataFrame(geometry=[], crs=4326)
    return gpd.GeoDataFrame.from_features(feats, crs=4326)


def save_geojson(gdf: gpd.GeoDataFrame, filename: str, meta: dict | None = None) -> None:
    gdf.to_file(filename, driver="GeoJSON")
    if meta:
        with open(filename + ".meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

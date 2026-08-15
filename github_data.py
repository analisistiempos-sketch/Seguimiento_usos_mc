import base64
from pathlib import Path

import requests

import config

_API = "https://api.github.com"


def _repo():
    if not config.GITHUB_REPO:
        raise RuntimeError("Falta GITHUB_REPO (formato: usuario/repositorio).")
    return config.GITHUB_REPO.strip("/")


def _headers():
    if not config.GITHUB_TOKEN:
        raise RuntimeError("Falta GITHUB_TOKEN (personal access token de GitHub).")
    return {
        "Authorization": f"Bearer {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _url(nombre=None):
    base = f"{_API}/repos/{_repo()}/contents/{config.GITHUB_RUTA.strip('/')}"
    return f"{base}/{nombre}" if nombre else base


def listar_parquets():
    r = requests.get(_url(), headers=_headers(), timeout=30)
    if r.status_code == 404:
        return []
    r.raise_for_status()
    return [
        e["name"]
        for e in r.json()
        if e.get("type") == "file" and e["name"].lower().endswith(".parquet")
    ]


def descargar_parquet(nombre, destino):
    r = requests.get(_url(nombre), headers=_headers(), timeout=60)
    r.raise_for_status()
    data = r.json()
    if data.get("encoding") == "base64":
        contenido = base64.b64decode(data["content"])
    else:
        r = requests.get(data["download_url"], headers=_headers(), timeout=60)
        r.raise_for_status()
        contenido = r.content
    Path(destino).write_bytes(contenido)
    return destino


def subir_parquet(nombre, origen):
    r = requests.get(_url(nombre), headers=_headers(), timeout=30)
    if r.status_code == 200:
        sha = r.json().get("sha")
    elif r.status_code == 404:
        sha = None
    else:
        r.raise_for_status()
    with open(origen, "rb") as f:
        contenido = base64.b64encode(f.read()).decode()
    payload = {
        "message": f"Actualizar {nombre}",
        "content": contenido,
        "branch": config.GITHUB_BRANCH,
    }
    if sha:
        payload["sha"] = sha
    r = requests.put(_url(nombre), json=payload, headers=_headers(), timeout=60)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Subida a GitHub fallida ({nombre}): {r.status_code} {r.text[:300]}")
    return nombre


def sync_desde_github(destino_dir):
    destino = Path(destino_dir)
    destino.mkdir(parents=True, exist_ok=True)
    for nombre in listar_parquets():
        local = destino / nombre
        if local.exists() and local.stat().st_size > 0:
            continue
        try:
            descargar_parquet(nombre, local)
            print(f"[github] descargado {nombre}")
        except Exception as e:
            print(f"[github] error descargando {nombre}: {e}")
    return destino

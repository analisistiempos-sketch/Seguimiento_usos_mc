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


def _listar_parquets_tree():
    """Respaldo: lista los .parquet usando la API de arboles (recursiva).

    Necesario cuando la carpeta tiene mas de 1000 entradas, porque la API de
    contenidos trunca la respuesta y NO soporta paginacion real.
    """
    info = requests.get(f"{_API}/repos/{_repo()}", headers=_headers(), timeout=30)
    info.raise_for_status()
    branch = config.GITHUB_BRANCH or info.json().get("default_branch", "main")
    r = requests.get(
        f"{_API}/repos/{_repo()}/git/trees/{branch}",
        headers=_headers(), params={"recursive": "1"}, timeout=60,
    )
    r.raise_for_status()
    prefijo = config.GITHUB_RUTA.strip("/")
    resultado = {}
    for nodo in r.json().get("tree", []):
        if nodo.get("type") != "blob":
            continue
        path = nodo["path"]
        if prefijo and not path.startswith(prefijo + "/"):
            continue
        nombre = path.split("/")[-1]
        if nombre.lower().endswith(".parquet"):
            resultado[nombre] = nodo.get("size", 0)
    return resultado


def listar_parquets():
    """Lista los .parquet de GITHUB_RUTA (nombre -> tamano).

    La API de contenidos devuelve hasta 1000 entradas en una sola respuesta y
    trunca el resto. Si se alcanza ese limite, se usa la API de arboles.
    """
    r = requests.get(_url(), headers=_headers(), params={"per_page": 1000}, timeout=30)
    if r.status_code == 404:
        return {}
    r.raise_for_status()
    items = r.json()
    if not isinstance(items, list):
        return {}
    if len(items) < 1000:
        return {
            e["name"]: e["size"]
            for e in items
            if e.get("type") == "file" and e["name"].lower().endswith(".parquet")
        }
    return _listar_parquets_tree()


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
    parquets = listar_parquets()
    for nombre, size_remoto in parquets.items():
        local = destino / nombre
        if local.exists() and local.stat().st_size == size_remoto:
            continue
        try:
            descargar_parquet(nombre, local)
            print(f"[github] descargado {nombre}")
        except Exception as e:
            print(f"[github] error descargando {nombre}: {e}")
    for nombre in ("dim_estacion.csv", "dim_Calendario.xlsx"):
        local = destino / nombre
        if local.exists() and local.stat().st_size > 0:
            continue
        try:
            descargar_parquet(nombre, local)
            print(f"[github] descargado {nombre}")
        except Exception:
            pass
    return destino

"""Sube al repo de datos de GitHub los parquet locales que falten en la nube.

Contexto
--------
La app en Streamlit Cloud lee los datos desde el repo de GitHub configurado en
`GITHUB_REPO` / `GITHUB_RUTA` (los mismos Secrets del panel). Si ese repo no tiene
todos los dias de 2026, el "Top 10" anual se calcula sobre pocos dias y da un
valor equivocado (p. ej. 262.581 en vez de 298.803).

Este script compara tus parquet locales (carpeta 2026/ + Actual/) contra lo que
hay en el repo y sube los que faltan.

Uso (PowerShell)
----------------
  $env:GITHUB_REPO = "analisistiempos-sketch/Seguimiento_usos"
  $env:GITHUB_RUTA = "datos"
  $env:GITHUB_TOKEN = "ghp_...tu_token_con_permiso_de_escritura..."

  # 1) Ver que se subiria (no sube nada):
  uv run --with pandas --with requests --with pyarrow python subir_datos_github.py --dry-run

  # 2) Subir solo los que faltan de 2026:
  uv run --with pandas --with requests --with pyarrow python subir_datos_github.py

  # 3) Forzar subida de todo un rango:
  uv run --with pandas --with requests --with pyarrow python subir_datos_github.py --desde 2026-01-01 --hasta 2026-06-30 --todos
"""
import argparse
import datetime

import config
import data_loader
import github_data


def _locales(anios):
    """Devuelve {nombre_archivo: (fecha, ruta_local)} de los parquet diarios locales."""
    vistos = {}
    carpetas = [config.DATOS_ACTUAL_DIR] + [config.SHAREPOINT_DIR / str(a) for a in anios]
    for carpeta in carpetas:
        if not carpeta.exists():
            continue
        for f in carpeta.rglob("*.parquet"):
            d = data_loader._parse_fecha_nombre(f.name)
            if d is not None and d.year in anios:
                vistos[f.name] = (d, f)
    return vistos


def main():
    ap = argparse.ArgumentParser(description="Sube parquet faltantes al repo de datos de GitHub.")
    ap.add_argument("--anio", type=int, default=2026, help="Anio a completar (por defecto 2026).")
    ap.add_argument("--desde", type=str, default=None, help="Fecha minima AAAA-MM-DD.")
    ap.add_argument("--hasta", type=str, default=None, help="Fecha maxima AAAA-MM-DD.")
    ap.add_argument("--todos", action="store_true", help="Subir todos (no solo los que faltan).")
    ap.add_argument("--dry-run", action="store_true", help="Solo mostrar, sin subir nada.")
    args = ap.parse_args()

    print(f"Repo: {config.GITHUB_REPO or '(falta GITHUB_REPO)'} | Ruta: {config.GITHUB_RUTA}")
    if not config.GITHUB_REPO or not config.GITHUB_TOKEN:
        raise SystemExit("Faltan GITHUB_REPO y/o GITHUB_TOKEN en el entorno.")

    remotos = github_data.listar_parquets()
    print(f"Parquet en el repo (remotos): {len(remotos)}")

    locales = _locales({args.anio})
    print(f"Parquet locales de {args.anio}: {len(locales)}")

    desde = datetime.date.fromisoformat(args.desde) if args.desde else None
    hasta = datetime.date.fromisoformat(args.hasta) if args.hasta else None

    a_subir = {}
    for nombre, (d, f) in locales.items():
        if desde and d < desde:
            continue
        if hasta and d > hasta:
            continue
        if args.todos or nombre not in remotos:
            a_subir[nombre] = (d, f)

    if a_subir:
        fechas = sorted(d for d, _ in a_subir.values())
        print(f"A subir: {len(a_subir)} archivos ({fechas[0]} -> {fechas[-1]})")
        for nombre, (d, f) in sorted(a_subir.items(), key=lambda kv: kv[1][0]):
            print(f"  + {d}  {nombre}  ({f.stat().st_size} bytes)")
    else:
        print("No hay archivos por subir (ya estan todos).")

    if args.dry_run or not a_subir:
        print("Modo solo lectura: no se subio nada." if args.dry_run else "Nada que hacer.")
        return

    ok, errores = 0, []
    for nombre, (d, f) in sorted(a_subir.items(), key=lambda kv: kv[1][0]):
        try:
            github_data.subir_parquet(nombre, str(f))
            ok += 1
            print(f"[ok] {nombre}")
        except Exception as e:  # noqa: BLE001
            errores.append((nombre, str(e)))
            print(f"[error] {nombre}: {e}")

    print(f"\nSubidos: {ok}/{len(a_subir)}")
    if errores:
        print(f"Errores: {len(errores)}")
        for nombre, err in errores:
            print(f"  - {nombre}: {err}")


if __name__ == "__main__":
    main()

# spec: 002-ui-redesign
"""Preparar un cliente de Flet con el icono de Habits App (solo macOS).

Flet ignora `Window.icon` en macOS: el icono del Dock y el nombre de la app
provienen del bundle del cliente de escritorio. Este script copia el cliente
cacheado por Flet en `build/macos/Habits App.app`, sustituye su `AppIcon.icns`
por `img/icon.icns`, ajusta el nombre y el identificador y vuelve a firmarlo
en modo ad-hoc. Después, `python -m habits.app` usa ese bundle automáticamente.

Uso:
    python scripts/prepare_macos_bundle.py [--force]
"""

import argparse
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ICON_PATH = ROOT / "img" / "icon.icns"
BUNDLE_DIR = ROOT / "build" / "macos"
BUNDLE_NAME = "Habits App"
BUNDLE_ID = "com.habits.app"


def find_client_bundle() -> Path:
    """Localizar el bundle del cliente de Flet en la caché local.

    Returns:
        Ruta al `Flet.app` cacheado; si no existe, Flet lo descarga antes.

    Raises:
        FileNotFoundError: Si el cliente no contiene ningún bundle `.app`.
    """
    import flet_desktop

    client_dir = flet_desktop.ensure_client_cached()
    app_path = flet_desktop.find_macos_app_bundle(client_dir)
    if app_path is None:
        raise FileNotFoundError(
            f"No se encontró ningún .app en el cliente de Flet: {client_dir}"
        )
    return Path(app_path)


def read_bundle_version(bundle: Path) -> str:
    """Leer el `CFBundleShortVersionString` de un bundle.

    Args:
        bundle: Ruta al bundle `.app`.

    Returns:
        La versión declarada, o una cadena vacía si no está presente.
    """
    with (bundle / "Contents" / "Info.plist").open("rb") as info_file:
        info = plistlib.load(info_file)
    return str(info.get("CFBundleShortVersionString", ""))


def patch_info_plist(bundle: Path) -> None:
    """Renombrar la app y darle un identificador propio.

    Args:
        bundle: Ruta al bundle `.app` que se va a modificar.
    """
    info_path = bundle / "Contents" / "Info.plist"
    with info_path.open("rb") as info_file:
        info = plistlib.load(info_file)

    info["CFBundleName"] = BUNDLE_NAME
    info["CFBundleDisplayName"] = BUNDLE_NAME
    info["CFBundleIdentifier"] = BUNDLE_ID

    with info_path.open("wb") as info_file:
        plistlib.dump(info, info_file, fmt=plistlib.FMT_BINARY)


def resign_bundle(bundle: Path) -> None:
    """Volver a firmar el bundle en modo ad-hoc tras modificarlo.

    Args:
        bundle: Ruta al bundle `.app` que se va a firmar.

    Raises:
        subprocess.CalledProcessError: Si `codesign` falla.
    """
    subprocess.run(
        ["codesign", "--force", "--deep", "--sign", "-", str(bundle)],
        check=True,
    )


def prepare_bundle(force: bool = False) -> Path:
    """Crear o actualizar el bundle de macOS con el icono personalizado.

    Args:
        force: Si es True, regenera el bundle aunque la versión de Flet
            coincida con la del cliente cacheado.

    Returns:
        Ruta al bundle preparado.

    Raises:
        SystemExit: Si el sistema no es macOS o falta `img/icon.icns`.
        FileNotFoundError: Si el cliente de Flet no contiene un bundle.
    """
    if sys.platform != "darwin":
        raise SystemExit(
            "Este script solo es necesario en macOS; en Windows y Linux "
            "basta con page.window.icon."
        )
    if not ICON_PATH.exists():
        raise SystemExit(
            f"Falta {ICON_PATH}. Genera el .icns a partir de img/icon.jpg."
        )

    source = find_client_bundle()
    destination = BUNDLE_DIR / f"{BUNDLE_NAME}.app"

    if (
        destination.exists()
        and not force
        and read_bundle_version(destination) == read_bundle_version(source)
    ):
        print(f"Ya está preparado: {destination}")
        return destination

    if destination.exists():
        shutil.rmtree(destination)
    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)

    shutil.copytree(source, destination, symlinks=True)
    shutil.copy2(ICON_PATH, destination / "Contents" / "Resources" / "AppIcon.icns")
    patch_info_plist(destination)
    resign_bundle(destination)

    print(f"Bundle preparado: {destination}")
    return destination


def main() -> None:
    """Punto de entrada del script."""
    parser = argparse.ArgumentParser(
        description="Prepara el cliente de Flet con el icono de Habits App."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="regenera el bundle aunque la versión de Flet no cambie",
    )
    args = parser.parse_args()

    prepare_bundle(force=args.force)


if __name__ == "__main__":
    main()

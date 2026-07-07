#!/usr/bin/env python3
"""Build KiCad 10 PCM v2 artifacts for adamjvr/kiCAD-Altium.

This script builds the real KiCad-installable ZIP archive, then writes:

  repository.json       PCM v2 repository index for KiCad 10+
  packages.json         PCM v2 package list for KiCad 10+
  repository-v1.json    optional legacy repository index for KiCad 6-9
  packages-v1.json      optional legacy package list for KiCad 6-9
  dist/*.zip            install archives

The GitHub raw URL for KiCad 10+ users is:

  https://raw.githubusercontent.com/adamjvr/kiCAD-Altium/main/repository.json
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile

DEFAULT_OWNER_REPO = "adamjvr/kiCAD-Altium"
DEFAULT_BRANCH = "main"
PACKAGE_ID = "com.github.adamjvr.kicad-altium"
PACKAGE_NAME = "Altium Inspired Theme"
THEME_SOURCE = Path("src/Altium.json")
THEME_NAME = "Altium.json"
ICON_SOURCE = Path("resources/icon.png")
V2_SCHEMA = "https://go.kicad.org/pcm/schemas/v2"
V1_SCHEMA = "https://go.kicad.org/pcm/schemas/v1"


def die(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        die(f"missing required file: {path}")
    except json.JSONDecodeError as exc:
        die(f"invalid JSON in {path}: {exc}")


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_epoch_for_source_files() -> int | None:
    candidates = [
        "src/Altium.json",
        "resources/icon.png",
        "scripts/build-pcm.py",
        "scripts/build-pcm.sh",
        "scripts/validate-pcm.py",
        "README.md",
    ]
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", *candidates],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except Exception:
        return None
    value = result.stdout.strip()
    return int(value) if value.isdigit() else None


def epoch_to_utc(epoch: int) -> str:
    return _dt.datetime.fromtimestamp(epoch, tz=_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def install_size(root: Path) -> int:
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file())


def base_metadata(*, schema: str, kicad_min: str) -> dict:
    return {
        "$schema": schema,
        "name": PACKAGE_NAME,
        "description": "Altium-inspired color theme for KiCad's PCB, schematic, GerbView, and 3D viewer editors.",
        "description_full": (
            "Altium Inspired Theme is an unofficial KiCad color theme intended to give KiCad "
            "a dark PCB editor palette reminiscent of Altium Designer while also providing "
            "schematic, GerbView, and 3D viewer colors. This project is not affiliated with, "
            "endorsed by, or sponsored by Altium Limited."
        ),
        "identifier": PACKAGE_ID,
        "type": "colortheme",
        "author": {
            "name": "Adam Vadala-Roth",
            "contact": {"web": "https://github.com/adamjvr/kiCAD-Altium"},
        },
        "maintainer": {
            "name": "Adam Vadala-Roth",
            "contact": {"web": "https://github.com/adamjvr/kiCAD-Altium"},
        },
        "license": "MIT",
        "resources": {
            "homepage": "https://github.com/adamjvr/kiCAD-Altium",
            "repository": "https://github.com/adamjvr/kiCAD-Altium",
            "issues": "https://github.com/adamjvr/kiCAD-Altium/issues",
        },
        "tags": ["theme", "colors", "altium"],
        "versions": [
            {
                "version": "0.0.0",  # overwritten by build_package_zip()
                "status": "stable",
                "kicad_version": kicad_min,
            }
        ],
    }


def make_archive_root(repo_root: Path, theme: dict, metadata: dict, build_root: Path) -> int:
    if build_root.exists():
        shutil.rmtree(build_root)
    (build_root / "colors").mkdir(parents=True, exist_ok=True)
    (build_root / "resources").mkdir(parents=True, exist_ok=True)

    (build_root / "colors" / THEME_NAME).write_text(
        json.dumps(theme, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_json(build_root / "metadata.json", metadata)

    icon = repo_root / ICON_SOURCE
    if icon.exists():
        shutil.copy2(icon, build_root / "resources" / "icon.png")

    return install_size(build_root)


def zip_archive(build_root: Path, package_zip: Path) -> None:
    if package_zip.exists():
        package_zip.unlink()
    package_zip.parent.mkdir(parents=True, exist_ok=True)

    ordered = [build_root / "metadata.json", build_root / "colors" / THEME_NAME]
    icon = build_root / "resources" / "icon.png"
    if icon.exists():
        ordered.append(icon)

    with zipfile.ZipFile(package_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in ordered:
            zf.write(path, path.relative_to(build_root).as_posix())


def build_package_zip(
    *,
    repo_root: Path,
    theme: dict,
    version: str,
    schema: str,
    kicad_min: str,
    zip_name: str,
    build_subdir: str,
) -> tuple[dict, Path, int, int, str]:
    metadata = base_metadata(schema=schema, kicad_min=kicad_min)
    metadata["versions"][0]["version"] = version

    build_root = repo_root / "build" / build_subdir
    package_zip = repo_root / "dist" / zip_name
    extracted_size = make_archive_root(repo_root, theme, metadata, build_root)
    zip_archive(build_root, package_zip)

    digest = sha256_file(package_zip)
    download_size = package_zip.stat().st_size
    return metadata, package_zip, extracted_size, download_size, digest


def repository_doc(*, schema_url: str, packages_url: str, packages_sha: str, epoch: int, v2: bool) -> dict:
    doc = {
        "$schema": f"{schema_url}#/definitions/Repository",
        "name": "AdamJVR KiCad Addons",
        "maintainer": {
            "name": "Adam Vadala-Roth",
            "contact": {"web": "https://github.com/adamjvr"},
        },
        "packages": {
            "url": packages_url,
            "sha256": packages_sha,
            "update_timestamp": epoch,
            "update_time_utc": epoch_to_utc(epoch),
        },
    }
    if v2:
        doc["schema_version"] = 2
    return doc


def build(args: argparse.Namespace) -> None:
    repo_root = Path.cwd()
    theme = read_json(repo_root / THEME_SOURCE)

    if "meta" not in theme or "name" not in theme.get("meta", {}):
        die(f"{THEME_SOURCE} does not look like a KiCad color theme; missing meta.name")

    owner_repo = args.github_repository or os.environ.get("GITHUB_REPOSITORY") or DEFAULT_OWNER_REPO
    branch = args.branch or os.environ.get("GITHUB_REF_NAME") or DEFAULT_BRANCH
    version = args.version

    raw_base = f"https://raw.githubusercontent.com/{owner_repo}/{branch}"
    packages_url_v2 = f"{raw_base}/packages.json"
    packages_url_v1 = f"{raw_base}/packages-v1.json"

    v2_zip_name = f"{PACKAGE_ID}_v{version}_kicad10_pcm.zip"
    v1_zip_name = f"{PACKAGE_ID}_v{version}_legacy_pcm.zip"

    dist = repo_root / "dist"
    dist.mkdir(exist_ok=True)

    v2_metadata, v2_zip, v2_install_size, v2_download_size, v2_sha = build_package_zip(
        repo_root=repo_root,
        theme=theme,
        version=version,
        schema=V2_SCHEMA,
        kicad_min="10.0",
        zip_name=v2_zip_name,
        build_subdir="pcm-package-v2",
    )

    v2_repo_package = json.loads(json.dumps(v2_metadata))
    v2_repo_package["versions"][0].update(
        {
            "download_url": f"{raw_base}/dist/{v2_zip_name}",
            "download_sha256": v2_sha,
            "download_size": v2_download_size,
            "install_size": v2_install_size,
        }
    )
    write_json(repo_root / "packages.json", {"packages": [v2_repo_package]})
    packages_sha_v2 = sha256_file(repo_root / "packages.json")

    # Optional legacy files for users who explicitly need KiCad 6-9. GitHub Raw cannot do
    # the official KiCad server's Accept-header negotiation, so the main URL stays v2.
    v1_metadata, v1_zip, v1_install_size, v1_download_size, v1_sha = build_package_zip(
        repo_root=repo_root,
        theme=theme,
        version=version,
        schema=V1_SCHEMA,
        kicad_min="6.0",
        zip_name=v1_zip_name,
        build_subdir="pcm-package-v1",
    )
    v1_repo_package = json.loads(json.dumps(v1_metadata))
    v1_repo_package["versions"][0].update(
        {
            "download_url": f"{raw_base}/dist/{v1_zip_name}",
            "download_sha256": v1_sha,
            "download_size": v1_download_size,
            "install_size": v1_install_size,
        }
    )
    write_json(repo_root / "packages-v1.json", {"packages": [v1_repo_package]})
    packages_sha_v1 = sha256_file(repo_root / "packages-v1.json")

    epoch = args.timestamp
    if epoch is None:
        env_epoch = os.environ.get("SOURCE_DATE_EPOCH")
        epoch = int(env_epoch) if env_epoch and env_epoch.isdigit() else git_epoch_for_source_files()
    if epoch is None:
        existing = repo_root / "repository.json"
        if existing.exists():
            try:
                epoch = int(read_json(existing)["packages"]["update_timestamp"])
            except Exception:
                epoch = None
    if epoch is None:
        epoch = int(time.time())

    write_json(
        repo_root / "repository.json",
        repository_doc(schema_url=V2_SCHEMA, packages_url=packages_url_v2, packages_sha=packages_sha_v2, epoch=epoch, v2=True),
    )
    write_json(
        repo_root / "repository-v1.json",
        repository_doc(schema_url=V1_SCHEMA, packages_url=packages_url_v1, packages_sha=packages_sha_v1, epoch=epoch, v2=False),
    )

    print(f"Built KiCad 10 PCM package: {v2_zip}")
    print(f"  SHA256: {v2_sha}")
    print(f"  Download size: {v2_download_size} bytes")
    print(f"  Install size: {v2_install_size} bytes")
    print(f"Built legacy PCM package: {v1_zip}")
    print(f"  SHA256: {v1_sha}")
    print(f"KiCad 10+ repository URL: {raw_base}/repository.json")
    print(f"Legacy KiCad 6-9 repository URL: {raw_base}/repository-v1.json")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build KiCad PCM v2 artifacts for kiCAD-Altium.")
    parser.add_argument("--version", default=os.environ.get("PCM_VERSION", "1.0.0"))
    parser.add_argument("--github-repository", default=None, help="owner/repo; defaults to GITHUB_REPOSITORY or adamjvr/kiCAD-Altium")
    parser.add_argument("--branch", default=None, help="branch name used for raw.githubusercontent.com URLs")
    parser.add_argument("--timestamp", type=int, default=None, help="repository update timestamp; defaults to source git timestamp")
    args = parser.parse_args()
    build(args)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Offline sanity checks for kiCAD-Altium KiCad PCM v2 repository files."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import zipfile

PACKAGE_ID = "com.github.adamjvr.kicad-altium"
V2_SCHEMA = "https://go.kicad.org/pcm/schemas/v2"
V1_SCHEMA = "https://go.kicad.org/pcm/schemas/v1"


def fail(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(1)


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"could not read {path}: {exc}")


def check_sha(path: Path, expected: str, label: str) -> None:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected:
        fail(f"{label} SHA256 mismatch: expected {expected}, got {digest}")


def validate_repository(repo_path: Path, packages_path: Path, *, schema: str, expect_schema_version_2: bool) -> None:
    repo = load(repo_path)
    packages = load(packages_path)

    if repo.get("$schema") != f"{schema}#/definitions/Repository":
        fail(f"{repo_path} has wrong $schema")
    if expect_schema_version_2 and repo.get("schema_version") != 2:
        fail(f"{repo_path} must include schema_version: 2")
    if not expect_schema_version_2 and "schema_version" in repo:
        fail(f"{repo_path} should not include schema_version")

    package_ref = repo.get("packages", {})
    if not package_ref.get("url", "").endswith(packages_path.name):
        fail(f"{repo_path} packages.url does not point at {packages_path.name}")
    if package_ref.get("sha256"):
        check_sha(packages_path, package_ref["sha256"], str(packages_path))

    pkg_list = packages.get("packages", [])
    if len(pkg_list) != 1:
        fail(f"{packages_path} should contain exactly one package")

    pkg = pkg_list[0]
    if pkg.get("$schema") != schema:
        fail(f"{packages_path} package has wrong $schema")
    if pkg.get("identifier") != PACKAGE_ID:
        fail(f"{packages_path} has unexpected package identifier")
    if pkg.get("type") != "colortheme":
        fail(f"{packages_path} package type must be colortheme")

    version = pkg.get("versions", [{}])[0]
    for key in ("download_url", "download_sha256", "download_size", "install_size"):
        if key not in version:
            fail(f"{packages_path} version missing {key}")

    zip_path = Path("dist") / version["download_url"].rsplit("/", 1)[-1]
    if not zip_path.exists():
        fail(f"missing package ZIP: {zip_path}")
    check_sha(zip_path, version["download_sha256"], str(zip_path))
    if zip_path.stat().st_size != version["download_size"]:
        fail(f"{zip_path} byte size does not match package metadata")

    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
        required = {"metadata.json", "colors/Altium.json"}
        missing = required - names
        if missing:
            fail(f"{zip_path} missing required files: {sorted(missing)}")
        forbidden = [name for name in names if name.startswith("package/") or name.startswith("src/")]
        if forbidden:
            fail(f"{zip_path} contains files outside the KiCad package root: {forbidden}")
        metadata = json.loads(zf.read("metadata.json"))
        theme = json.loads(zf.read("colors/Altium.json"))

    if metadata.get("$schema") != schema:
        fail(f"{zip_path} archive metadata.json has wrong schema")
    if metadata.get("type") != "colortheme":
        fail(f"{zip_path} archive metadata.json type must be colortheme")
    archive_version = metadata.get("versions", [{}])[0]
    for forbidden_key in ("download_url", "download_sha256", "download_size", "install_size"):
        if forbidden_key in archive_version:
            fail(f"{zip_path} archive metadata.json must not contain {forbidden_key}")
    if theme.get("meta", {}).get("name") != "Altium":
        fail(f"{zip_path} theme meta.name should be Altium")


def main() -> None:
    validate_repository(Path("repository.json"), Path("packages.json"), schema=V2_SCHEMA, expect_schema_version_2=True)
    validate_repository(Path("repository-v1.json"), Path("packages-v1.json"), schema=V1_SCHEMA, expect_schema_version_2=False)
    print("PCM v2 validation passed. Legacy v1 fallback validation passed.")


if __name__ == "__main__":
    main()

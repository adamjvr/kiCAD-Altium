# kiCAD-Altium

Altium Inspired Theme is an unofficial color theme for KiCad. It gives KiCad a dark PCB editor palette reminiscent of Altium Designer while also providing schematic, GerbView, and 3D viewer colors.

This project is not affiliated with, endorsed by, or sponsored by Altium Limited.

## Install from inside KiCad 10+

Add this third-party repository URL to KiCad's **Plugin and Content Manager**:

```text
https://raw.githubusercontent.com/adamjvr/kiCAD-Altium/main/repository.json
```

Then install **Altium Inspired Theme** from the repository.

### KiCad UI steps

1. Open KiCad.
2. Open **Plugin and Content Manager**.
3. Click **Manage...** or **Manage repositories**.
4. Add the repository URL above.
5. Select **AdamJVR KiCad Addons**.
6. Install **Altium Inspired Theme**.
7. Restart KiCad if the theme does not appear immediately.
8. Select the theme in KiCad's color preferences.

## Why this repo uses PCM v2

KiCad 10 introduced PCM schema v2. New packages should target v2, and a KiCad 10 PCM repository should advertise that by including `schema_version: 2` in `repository.json`.

This repo is therefore KiCad 10-first:

```text
repository.json      KiCad 10+ PCM v2 repository index
packages.json        KiCad 10+ PCM v2 package list
```

The installable KiCad 10 archive in `dist/` contains v2 package metadata and declares `kicad_version: "10.0"`.

## Legacy KiCad 6-9 fallback

The theme itself is still just a KiCad color theme, so this repo also generates a separate legacy PCM v1 fallback:

```text
repository-v1.json   Optional legacy repository index for KiCad 6-9
packages-v1.json     Optional legacy package list for KiCad 6-9
```

Legacy users can add this URL instead:

```text
https://raw.githubusercontent.com/adamjvr/kiCAD-Altium/main/repository-v1.json
```

KiCad's official addon server can serve v1 or v2 from one URL by inspecting the HTTP `Accept` header. GitHub Raw cannot do that kind of server-side content negotiation, so this repository exposes two explicit URLs: the main one for KiCad 10+, and the `repository-v1.json` one for old KiCad installs.

## What this repository contains

```text
src/Altium.json                                      Source KiCad color theme
resources/icon.png                                   PCM package icon
repository.json                                      KiCad 10+ PCM v2 repository index
packages.json                                        KiCad 10+ PCM v2 package list
repository-v1.json                                   Optional legacy KiCad 6-9 repository index
packages-v1.json                                     Optional legacy KiCad 6-9 package list
scripts/build-pcm.py                                 Builds install archives and metadata
scripts/build-pcm.sh                                 Shell wrapper for the build script
scripts/validate-pcm.py                              Offline validation checks
dist/com.github.adamjvr.kicad-altium_v1.0.1_kicad10_pcm.zip      KiCad 10+ install archive
dist/com.github.adamjvr.kicad-altium_v1.0.1_legacy_pcm.zip       Legacy KiCad 6-9 install archive
.github/workflows/build-pcm.yml                      GitHub Actions automation
```

## Package archive format

KiCad color theme packages are ZIP files with this layout:

```text
Archive root/
├── colors/
│   └── Altium.json
├── resources/
│   └── icon.png
└── metadata.json
```

The ZIP archives in `dist/` follow that layout exactly. The archive root contains `metadata.json`, not a nested project folder.

The root-level `packages.json` points KiCad at the KiCad 10 package ZIP and includes the ZIP SHA256, download size, and install size. The root-level `repository.json` points KiCad at `packages.json` and includes `schema_version: 2`.

The legacy `packages-v1.json` does the same thing for the legacy v1 ZIP.

## Updating an already-installed package

If the icon, theme file, or metadata changes after users have already installed the package, bump the package version before publishing. KiCad may keep showing cached package data when the repository still advertises the same package version.

For an icon-only update, build the next patch version:

```bash
./scripts/build-pcm.sh --version 1.0.1
./scripts/validate-pcm.py
```

Then have users refresh the repository in Plugin and Content Manager, apply the update, and restart KiCad if the old icon is still visible.

## Rebuild after editing the theme

After changing `src/Altium.json`, rebuild the PCM artifacts:

```bash
./scripts/build-pcm.sh
./scripts/validate-pcm.py
```

Then commit the generated files:

```bash
git add src/Altium.json resources/icon.png repository.json packages.json repository-v1.json packages-v1.json dist scripts README.md .github .gitignore PCM_OVERLAY_NOTES.md
git commit -m "Update Altium KiCad color theme package"
git push
```

The public KiCad 10+ repository URL stays the same:

```text
https://raw.githubusercontent.com/adamjvr/kiCAD-Altium/main/repository.json
```

## Versioning

The default package version is `1.0.1`. To build another version:

```bash
./scripts/build-pcm.sh --version 1.0.1
```

or:

```bash
PCM_VERSION=1.0.1 ./scripts/build-pcm.sh
```

If you change the version, commit the new ZIP files in `dist/` along with the regenerated JSON files.

## GitHub Actions

This repo includes `.github/workflows/build-pcm.yml`. When files such as `src/Altium.json`, the build scripts, icon, or README change on `main`, the workflow rebuilds the PCM artifacts, validates them, and commits the generated `repository.json`, `packages.json`, `repository-v1.json`, `packages-v1.json`, and `dist/` package ZIPs back to the repo.

The workflow intentionally builds from the source-file git timestamp instead of wall-clock time so it does not create an endless commit loop.

## Manual install without PCM

If someone does not want to use the Plugin and Content Manager, they can manually copy:

```text
src/Altium.json
```

into their KiCad user color theme directory. The exact path depends on OS and KiCad version, but it is the `colors` directory inside the KiCad user configuration directory.

## License

MIT License. See `LICENSE`.

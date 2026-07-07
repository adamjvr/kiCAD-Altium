# PCM overlay notes

This overlay converts `adamjvr/kiCAD-Altium` to a KiCad 10-first PCM v2 third-party repository.

Extract the ZIP at the root of the `kiCAD-Altium` working tree, then run:

```bash
./scripts/validate-pcm.py
git add .
git commit -m "Add KiCad 10 PCM v2 packaging"
git push
```

The KiCad 10+ repository URL is:

```text
https://raw.githubusercontent.com/adamjvr/kiCAD-Altium/main/repository.json
```

The optional legacy KiCad 6-9 URL is:

```text
https://raw.githubusercontent.com/adamjvr/kiCAD-Altium/main/repository-v1.json
```

GitHub Raw cannot implement KiCad's official `Accept`-header based schema negotiation, so this repo publishes the v2 URL as the primary install path and keeps a separate v1 fallback URL.

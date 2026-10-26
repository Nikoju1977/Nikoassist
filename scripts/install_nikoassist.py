#!/usr/bin/env python3
"""Apply NikoAssist to an existing nanoMuse checkout: staged, idempotent overlay.

No dependencies/secrets downloaded. Validate before writing. On write failure,
best-effort rollback restores original files. GPL notices preserved.
"""
from __future__ import annotations

import argparse
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
INSTALL_MARK = "# NIKOASSIST_AGENT_TEAM_V1"


def _replace(text: str, before: str, after: str, *, required: bool = False) -> str:
    if before in text:
        return text.replace(before, after)
    if required and after not in text:
        raise ValueError(f"Required integration point not found: {before[:80]}")
    return text


def plan(target: Path, *, brand: bool = True) -> dict[Path, bytes]:
    root = target.expanduser().resolve()
    app = root / "nanomuse/app.py"
    if not app.is_file() or not (root / "android/src").is_dir():
        raise FileNotFoundError("--target doit être la racine d'un clone nano-muse/nanoMuse")
    result: dict[Path, bytes] = {}

    def stage(relative: str, transform, *, required: bool = False, xml: bool = False) -> None:
        path = root / relative
        if not path.is_file():
            if required:
                raise FileNotFoundError(path)
            return
        previous = path.read_text(encoding="utf-8")
        updated = transform(previous)
        if updated != previous:
            if xml:
                ET.fromstring(updated)
            result[path] = updated.encode("utf-8")

    source = HERE / "nanomuse/nikoassist"
    for file in sorted(source.glob("*.py")):
        destination = root / "nanomuse/nikoassist" / file.name
        content = file.read_bytes()
        if not destination.exists() or destination.read_bytes() != content:
            result[destination] = content

    anchor = "        self.tools = self._build_tools()\n"
    team_line = "        self.tools.add(NikoAssistTeamTool(app=self))\n"
    montage_lines = (
        "        from nanomuse.nikoassist.openmontage_tool import OpenMontageTool\n"
        "        self.tools.add(OpenMontageTool(app=self))\n"
    )
    insert = (
        "        " + INSTALL_MARK + "\n"
        "        from nanomuse.nikoassist.tool import NikoAssistTeamTool\n"
        + team_line + montage_lines
    )

    def integrate(text: str) -> str:
        if "self.tools.add(OpenMontageTool(app=self))" in text:
            return text
        if INSTALL_MARK in text:
            if team_line not in text:
                raise ValueError("Existing NikoAssist integration point changed")
            return text.replace(team_line, team_line + montage_lines, 1)
        return _replace(text, anchor, anchor + insert, required=True)

    stage("nanomuse/app.py", integrate, required=True)

    if brand:
        stage("nanomuse/config.py", lambda s: _replace(
            s, 'name: str = "nanoMuse"', 'name: str = "NikoAssist"'
        ))
        res = root / "android/src/android/app/src/main/res"
        for path in sorted(res.glob("values*/strings.xml")):
            rel = str(path.relative_to(root))
            def branding(s: str, locale=path.parent.name) -> str:
                s = re.sub(
                    r'(<string name="(?:app_name|onboarding_welcome_title|settings_about_minis)">)([^<]*)(</string>)',
                    lambda m: m.group(1) + m.group(2).replace("nanoMuse", "NikoAssist") + m.group(3), s,
                )
                credit = ("NikoAssist — par Niko Studio Design" if locale == "values-fr" else
                          "NikoAssist — by Niko Studio Design")
                return re.sub(r'(<string name="about_minis_tagline">)[^<]*(</string>)',
                              lambda m: m.group(1) + credit + m.group(2), s)
            stage(rel, branding, xml=True)

        stage("android/src/android/app/src/main/java/com/openminis/app/agent/SoulStore.kt",
              lambda s: s.replace('name = "nanoMuse"', 'name = "NikoAssist"')
                         .replace('name: "nanoMuse"', 'name: "NikoAssist"')
                         .replace('.ifEmpty { "nanoMuse" }', '.ifEmpty { "NikoAssist" }'))
        stage("android/src/ios/Minis.xcodeproj/project.pbxproj",
              lambda s: s.replace('INFOPLIST_KEY_CFBundleDisplayName = nanoMuse;',
                                  'INFOPLIST_KEY_CFBundleDisplayName = NikoAssist;')
                         .replace('INFOPLIST_KEY_CFBundleDisplayName = "Share to nanoMuse";',
                                  'INFOPLIST_KEY_CFBundleDisplayName = "Share to NikoAssist";'))
        stage("android/src/ios/NanoMuse/NanoMuseFirstRun.swift",
              lambda s: s.replace('title: AppLocalized("Welcome to nanoMuse"),',
                                  'title: "NikoAssist",')
                         .replace('subtitle: AppLocalized("An open-source personal agent for every device you own."),',
                                  'subtitle: "par Niko Studio Design",'))
        stage("android/src/ios/NanoMuse/NanoMuseSettings.swift",
              lambda s: s.replace('NanoMuseLinkRow(title: AppLocalized("About nanoMuse"))',
                                  'NanoMuseLinkRow(title: "NikoAssist — par Niko Studio Design")'))
        stage("android/src/ios/NanoMuse/NanoMuseAgentPage.swift",
              lambda s: s.replace('return n.isEmpty ? "nanoMuse" : n',
                                  'return n.isEmpty ? "NikoAssist" : n'))
        stage("android/src/ios/Agent/Session/SoulStore.swift",
              lambda s: s.replace('static let `default` = SoulMetadata(\n        name: "nanoMuse",',
                                  'static let `default` = SoulMetadata(\n        name: "NikoAssist",'))
    return result


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=f".{path.name}.niko-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        if path.exists():
            os.chmod(temp, path.stat().st_mode & 0o777)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def apply(target: Path, *, brand: bool = True, dry_run: bool = False) -> list[str]:
    root = target.expanduser().resolve()
    changes = plan(root, brand=brand)
    names = [str(path.relative_to(root)) for path in changes]
    if dry_run:
        return names
    backup: dict[Path, bytes | None] = {}
    try:
        for path, content in changes.items():
            backup[path] = path.read_bytes() if path.exists() else None
            _atomic_write(path, content)
    except Exception:
        for path, original in reversed(list(backup.items())):
            if original is None:
                path.unlink(missing_ok=True)
            else:
                _atomic_write(path, original)
        raise
    return names


def main() -> None:
    parser = argparse.ArgumentParser(description="Installer NikoAssist dans nanoMuse")
    parser.add_argument("--target", type=Path, required=True, help="répertoire nanoMuse")
    parser.add_argument("--no-brand", action="store_true", help="conserver le nom d'origine")
    parser.add_argument("--dry-run", action="store_true", help="liste des modifications seulement")
    args = parser.parse_args()
    changes = apply(args.target, brand=not args.no_brand, dry_run=args.dry_run)
    for name in changes:
        print("Prévu :" if args.dry_run else "Modifié :", name)
    print(f"{len(changes)} fichier(s). Builds Android/iOS à vérifier séparément.")


if __name__ == "__main__":
    main()

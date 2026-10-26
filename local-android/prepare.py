#!/usr/bin/env python3
"""Prepare a reproducible NikoAssist Local build from llama.cpp's official Android sample.

Pinned upstream includes Android-native GGUF inference. No cloud SDK or model/API
credentials are added to the APK. This overlays only a GPL NikoAssist chat UI,
brand and conservative device settings; upstream MIT LICENSE is retained.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

LLAMA_COMMIT = "c6fb3b5be2209f6c12339833198190f6f6829581"
APP_ID = "fr.nikostudio.nikoassist.local"


def substitute(path: Path, needle: str, replacement: str) -> None:
    original = path.read_text(encoding="utf-8")
    if original.count(needle) != 1:
        raise SystemExit(f"Expected exactly one match in {path}: {needle!r}")
    path.write_text(original.replace(needle, replacement), encoding="utf-8")


def prepare(root: Path, overlay: Path) -> None:
    root = root.resolve()
    actual = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual != LLAMA_COMMIT:
        raise SystemExit(
            f"Unexpected llama.cpp revision {actual}; expected pinned {LLAMA_COMMIT}"
        )

    project = root / "examples" / "llama.android"
    app = project / "app"
    lib = project / "lib"

    substitute(
        app / "build.gradle.kts",
        'applicationId = "com.example.llama.aichat"',
        f'applicationId = "{APP_ID}"',
    )
    # Android 13 or later on the S20 FE 5G (min SDK inherited from upstream).
    # Target SDK 35 avoids Android 16 behavior changes in the offline MVP.
    substitute(app / "build.gradle.kts", "targetSdk = 36", "targetSdk = 35")
    substitute(
        lib / "build.gradle.kts",
        'ndkVersion = "29.0.13113456"',
        'ndkVersion = "29.0.14206865"',
    )
    # Only build native ARM64 libraries: Snapdragon 865 and other arm64 phones.
    substitute(
        lib / "build.gradle.kts",
        'abiFilters += listOf("arm64-v8a", "x86_64")',
        'abiFilters += listOf("arm64-v8a")',
    )

    # Prevent Android cloud backup of model data or in-app conversation state.
    substitute(
        app / "src/main/AndroidManifest.xml",
        'android:allowBackup="true"',
        'android:allowBackup="false"',
    )
    # The stock Android sample deliberately requests no INTERNET permission.
    if "android.permission.INTERNET" in (
        app / "src/main/AndroidManifest.xml"
    ).read_text(encoding="utf-8"):
        raise SystemExit("Refusing to build a network-enabled local-only APK")

    target = app / "src/main/java/com/example/llama/MainActivity.kt"
    source = overlay / "app/MainActivity.kt"
    if not source.is_file():
        raise SystemExit(f"Missing first-party chat implementation: {source}")
    shutil.copy2(source, target)

    (app / "src/main/res/values/strings.xml").write_text(
        '<resources>\n'
        '    <string name="app_name">NikoAssist Local</string>\n'
        '</resources>\n',
        encoding="utf-8",
    )
    substitute(
        app / "src/main/res/layout/activity_main.xml",
        'android:text="Selected GGUF model\'s metadata will show here."',
        'android:text="NikoAssist Local — importer un modèle GGUF pour discuter hors ligne."',
    )
    substitute(
        app / "src/main/res/layout/activity_main.xml",
        'android:hint="Please first pick a GGUF model file to import."',
        'android:hint="Choisis un modèle GGUF depuis ton téléphone"',
    )
    print(
        f"Prepared NikoAssist Local ({APP_ID}) from "
        f"llama.cpp {LLAMA_COMMIT[:12]} — arm64 only, no Internet permission"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--llama", required=True, type=Path)
    parser.add_argument(
        "--overlay", type=Path, default=Path(__file__).resolve().parent
    )
    args = parser.parse_args()
    prepare(args.llama, args.overlay)


if __name__ == "__main__":
    main()

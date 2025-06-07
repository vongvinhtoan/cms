#!/usr/bin/env python3
"""Convert test input files from {i:02d}.txt to {prefix}{i}.txt format."""

import argparse
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Copy files from --indir ({i:02d}.txt) to --outdir ({prefix}{i}.txt)"
    )
    parser.add_argument("--indir", required=True, help="Input directory")
    parser.add_argument("--outdir", required=True, help="Output directory")
    parser.add_argument("--prefix", default="input", help="Output filename prefix (default: input)")
    args = parser.parse_args()

    indir = Path(args.indir)
    outdir = Path(args.outdir)
    prefix = args.prefix
    outdir.mkdir(parents=True, exist_ok=True)

    i = 0
    while True:
        src = indir / f"{i:02d}.txt"
        if not src.exists():
            break
        dst = outdir / f"{prefix}{i}.txt"
        shutil.copy2(src, dst)
        print(f"{src} -> {dst}")
        i += 1

    if i == 0:
        print(f"No files matching {{0..}}.txt found in {indir}")
    else:
        print(f"Copied {i} file(s)")


if __name__ == "__main__":
    main()

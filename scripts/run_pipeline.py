#!/usr/bin/env python3
"""
Sentinel NIDS - Pipeline Orchestration CLI.

Usage:
    python scripts/run_pipeline.py --stage validate
    python scripts/run_pipeline.py --stage process
    python scripts/run_pipeline.py --fast
    python scripts/run_pipeline.py --full
"""

import argparse
import sys

from nids.common.errors import DatasetMissingError, NIDSError
from nids.data.validate import validate_dataset


def parse_args():
    parser = argparse.ArgumentParser(description="Sentinel NIDS Pipeline Runner")
    parser.add_argument(
        "--stage",
        choices=["validate", "process", "train", "evaluate"],
        help="Execute a specific pipeline stage",
    )
    parser.add_argument(
        "--fast", action="store_true", help="Run pipeline on subsampled data for rapid testing"
    )
    parser.add_argument(
        "--full", action="store_true", help="Execute the full end-to-end pipeline"
    )
    return parser.parse_args()


def run_validate():
    print("[*] Stage: Validating CIC-IDS2017 raw datasets in data/raw/cicids2017/...")
    try:
        report = validate_dataset()
    except DatasetMissingError as exc:
        print(f"[!] {exc}")
        return 2
    except NIDSError as exc:
        print(f"[!] Dataset validation stopped: {exc}")
        return 2
    print(f"[+] Dataset schema validated: {len(report['files'])} files.")
    print("[+] Wrote reports/schema_report.json and reports/schema_report.md.")
    return 0


def run_process(fast: bool = False):
    del fast
    print("[!] Processing is not implemented yet; no Parquet artifacts were created.")
    return 2


def run_train(fast: bool = False):
    del fast
    print("[!] Training is not implemented yet; no model bundle was created.")
    return 2


def run_evaluate():
    print("[!] Evaluation is not implemented yet; no test metrics were generated.")
    return 2


def main():
    args = parse_args()
    print("=" * 60)
    print(" 🛡️  SENTINEL NIDS - ML PIPELINE RUNNER")
    print("=" * 60)

    if args.stage == "validate":
        return run_validate()
    elif args.stage == "process":
        if run_validate() != 0:
            return 2
        return run_process(fast=args.fast)
    elif args.stage == "train":
        return run_train(fast=args.fast)
    elif args.stage == "evaluate":
        return run_evaluate()
    elif args.fast or args.full:
        if run_validate() != 0:
            return 2
        if run_process(fast=args.fast) != 0:
            return 2
        if run_train(fast=args.fast) != 0:
            return 2
        return run_evaluate()
    else:
        print("[!] No stage specified. Use --help to see available options.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

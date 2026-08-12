#!/usr/bin/env python3
import sys

from botjobs.app import main


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)

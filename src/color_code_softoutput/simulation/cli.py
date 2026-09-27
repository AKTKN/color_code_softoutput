"""Command line entry point for the canonical YAML experiment."""

import argparse

from .runner import run_experiment


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the color-code YAML simulation sweep")
    parser.add_argument("--config", required=True, help="validated YAML configuration")
    args = parser.parse_args(argv)
    root = run_experiment(args.config)
    print(f"completed: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

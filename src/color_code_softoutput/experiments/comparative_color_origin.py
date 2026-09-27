"""Backfill comparative candidate weights and report correction-origin colors."""
import argparse
from pathlib import Path
from ..analysis.circuit_level import (
    CircuitLevelDataset,
    comparative_correction_color_summary,
)


def main() -> None:
    """Generate/validate candidate sidecars for a completed circuit-memory run."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("--workers", type=int)
    parser.add_argument("--read-only", action="store_true",
                        help="Fail instead of generating missing candidate sidecars")
    args = parser.parse_args()
    dataset = CircuitLevelDataset(args.run_directory)
    summary = comparative_correction_color_summary(
        dataset, generate=not args.read_only, num_workers=args.workers
    )
    print(summary.to_string(index=False, formatters={
        "same_color_fraction": lambda value: f"{value:.2%}",
        "different_color_fraction": lambda value: f"{value:.2%}",
    }))


if __name__ == "__main__":
    main()

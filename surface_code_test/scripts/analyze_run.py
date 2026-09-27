"""Audit/replot saved shots: python -m surface_code_test.scripts.analyze_run RUN."""
import argparse
from pathlib import Path
import sys

if __package__ in (None,''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from surface_code_test.analysis import SurfaceDataset, standard_analysis
from surface_code_test.experiment import audit_run


def main() -> None:
    """Audit a completed run and regenerate all three plots without new sampling."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',type=Path)
    parser.add_argument('--units',choices=['natural','dB'],default='dB')
    parser.add_argument('--replay',action='store_true')
    parser.add_argument('--archived-sources',action='store_true',help='Verify archive only; allow current source drift')
    args = parser.parse_args()
    print(audit_run(args.run,replay=args.replay,check_current_sources=not args.archived_sources))
    standard_analysis(SurfaceDataset(args.run,units=args.units))


if __name__ == '__main__':
    main()

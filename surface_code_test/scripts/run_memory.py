"""CLI: python -m surface_code_test.scripts.run_memory [--shots 2000 --analyze]."""
import argparse
from pathlib import Path
import sys

if __package__ in (None,''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from surface_code_test.simulation import SurfaceConfig
from surface_code_test.experiment import run_experiment


def main() -> None:
    """Parse explicit distance/noise/round/shot settings and print the saved run path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--distances',type=int,nargs='+',default=[3,5,7])
    parser.add_argument('--p',type=float,default=.001)
    parser.add_argument('--rounds-factor',type=int,default=2)
    parser.add_argument('--shots',type=int,default=2000)
    parser.add_argument('--batch-size',type=int,default=250)
    parser.add_argument('--workers',type=int,default=3)
    parser.add_argument('--seed',type=int,default=20260916)
    parser.add_argument('--output-root',type=Path,default=SurfaceConfig().output_root)
    parser.add_argument('--analyze',action='store_true')
    parser.add_argument('--quiet',action='store_true')
    args = parser.parse_args()
    config = SurfaceConfig(distances=tuple(args.distances),physical_error_rate=args.p,rounds_factor=args.rounds_factor,
        shots_per_point=args.shots,batch_size=args.batch_size,num_workers=args.workers,master_seed=args.seed,output_root=args.output_root)
    print(run_experiment(config,analyze=args.analyze,verbose=not args.quiet))


if __name__ == '__main__':
    main()

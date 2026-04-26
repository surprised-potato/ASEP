"""Entry point for Bar project Howe truss analysis.
Usage: python -m src.run_bar [--project_name ...] [--chord_family ...] [--web_family ...]
"""
import sys
from .bar_optimizer import run_bar_optimization
from .warren_optimizer import run_warren_optimization
from .bar_report import generate_bar_report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run Bar Howe Truss Optimization")
    parser.add_argument("--project_name", type=str, default="Bar_Project",
                        help="Output directory name")
    parser.add_argument("--chord_family", type=str, default="2L",
                        help="Family for chord members (2L, WT, L)")
    parser.add_argument("--web_family", type=str, default="L",
                        help="Family for web members (L, 2L, HSS)")
    parser.add_argument("--num_panels", type=int, default=21,
                        help="Number of truss panels (default 21 for 1m panels)")
    args = parser.parse_args()

    print(f"=== Bar Project -- Level Bottom Chord Howe Truss Analysis ===")
    print(f"  Project: '{args.project_name}'")
    print(f"  21m Span | Two-Slope Top | Level Bottom | {args.chord_family} Chords | {args.web_family} Webs | N={args.num_panels}")
    print(f"  2 Interior Columns at 7.0m and 14.0m\n")

    truss_data = run_bar_optimization(
        target_ltod=240,
        max_iter=15,
        chord_family=args.chord_family,
        web_family=args.web_family,
        N=args.num_panels
    )

    # Warren Transfer Truss — uses interior column reaction as point load
    warren_data = None
    gov_react_int = truss_data.get('gov_react_y_int', 0)
    if gov_react_int > 0:
        print(f"\n=== Warren Transfer Truss (10m Span) ===")
        print(f"  Point load from interior column reaction: {gov_react_int:.2f} kN")
        warren_data = run_warren_optimization(
            point_load_kN=gov_react_int,
            span=10.0,
            depth=1.4,
            n_bays=4,
            chord_family=args.chord_family,
            web_family=args.web_family,
            target_ltod=360
        )

    print("\nGenerating Report...")
    generate_bar_report(truss_data, warren_data=warren_data, project_name=args.project_name)


if __name__ == "__main__":
    main()

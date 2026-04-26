"""Entry point for Bar project — LONG SPAN variant (No interior columns).
"""
import sys
import os
from .bar_optimizer import run_bar_optimization
from .bar_report import generate_bar_report

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run Long Span Bar Howe Truss Optimization")
    parser.add_argument("--project_name", type=str, default="Bar_Project_Long_Span",
                        help="Output directory name")
    parser.add_argument("--chord_family", type=str, default="2L",
                        help="Family for chord members (2L, WT)")
    parser.add_argument("--web_family", type=str, default="HSS",
                        help="Family for web members (L, 2L, HSS)")
    parser.add_argument("--num_panels", type=int, default=21,
                        help="Number of truss panels (default 21)")
    args = parser.parse_args()

    print(f"=== Bar Project — LONG SPAN (No Interior Columns) Analysis ===")
    print(f"  Project: '{args.project_name}'")
    print(f"  21m Span | 2.0m FIXED Depth | {args.chord_family} Chords | {args.web_family} Webs | N={args.num_panels}")
    print(f"  NO INTERIOR COLUMNS\n")

    truss_data = run_bar_optimization(
        target_ltod=240,
        max_iter=15,
        chord_family=args.chord_family,
        web_family=args.web_family,
        N=args.num_panels,
        has_int_cols=False
    )

    print("\nGenerating Long Span Report...")
    generate_bar_report(truss_data, project_name=args.project_name)

if __name__ == "__main__":
    main()

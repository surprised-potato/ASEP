"""Entry point for pickleball court truss analysis.
Usage: python -m src.run_pickleball [project_name]
"""
import sys
from .optimizer import run_pickleball_optimization
from .pickleball_report import generate_pickleball_report

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run Pickleball Truss Optimization")
    parser.add_argument("--project_name", type=str, default="Pickleball_Court", help="Output directory name")
    parser.add_argument("--chord_family", type=str, default="WT", help="Family for chord members")
    parser.add_argument("--web_family", type=str, default="L", help="Family for web members")
    parser.add_argument("--num_panels", type=int, default=16, help="Number of truss panels (must be even)")
    args = parser.parse_args()
    
    print(f"=== Pickleball Court Truss Analysis — Project: '{args.project_name}' ===\n")
    print(f"Optimizing 24m Symmetrical Pratt Truss ({args.chord_family} Chords, {args.web_family} Webs, N={args.num_panels})...")
    
    truss_data = run_pickleball_optimization(
        target_ltod=240, 
        max_iter=15, 
        chord_family=args.chord_family, 
        web_family=args.web_family,
        N=args.num_panels
    )
    
    print("\nGenerating Report...")
    generate_pickleball_report(truss_data, project_name=args.project_name)

if __name__ == "__main__":
    main()

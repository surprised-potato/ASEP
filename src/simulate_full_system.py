import sys
from .optimizer import (
    run_longitudinal_optimization,
    run_transverse_frame
)
from .report_generator import generate_markdown_report

def main(project_name=None):
    """Main pipeline entry point. Accepts an optional project name for output isolation."""
    if project_name is None:
        # Check CLI args: python -m src.simulate_full_system <project_name>
        project_name = sys.argv[1] if len(sys.argv) > 1 else "default"
    
    print(f"Starting Structural Analysis Pipeline for project: '{project_name}'\n")
    
    # 1. Optimize Longitudinal Truss (Original WT)
    print("1a. Optimizing Longitudinal Truss (WT Chords with L Webs)...")
    longitudinal_data = run_longitudinal_optimization(target_ltod=240, max_iter=15, chord_family="WT", web_family="L")
    
    # 1b. Optimize Longitudinal Truss (Alternative 2L)
    print("1b. Optimizing Longitudinal Truss (2L Chords)...")
    longitudinal_data_2l = run_longitudinal_optimization(target_ltod=240, max_iter=15, chord_family="2L")
    

    # 3. Analyze Transverse Frame
    print("\n3. Analyzing Transverse Moment Frame...")
    frame_data = run_transverse_frame()
    
    # 4. Generate Markdown Report into output/<project_name>/
    print("\n4. Generating Markdown Report...")
    generate_markdown_report(longitudinal_data, longitudinal_data_2l, frame_data, project_name=project_name)
    
if __name__ == "__main__":
    main()

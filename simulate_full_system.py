from optimizer import (
    run_longitudinal_optimization,
    run_transverse_frame
)
from report_generator import generate_markdown_report

def main():
    print("Starting Structural Analysis Pipeline...\n")
    
    # 1. Optimize Longitudinal Truss (Original WT)
    print("1a. Optimizing Longitudinal Truss (WT Chords with L Webs)...")
    longitudinal_data = run_longitudinal_optimization(target_ltod=240, max_iter=15, chord_family="WT", web_family="L")
    
    # 1b. Optimize Longitudinal Truss (Alternative 2L)
    print("1b. Optimizing Longitudinal Truss (2L Chords)...")
    longitudinal_data_2l = run_longitudinal_optimization(target_ltod=240, max_iter=15, chord_family="2L")
    

    # 3. Analyze Transverse Frame
    print("\n3. Analyzing Transverse Moment Frame...")
    frame_data = run_transverse_frame()
    
    # 4. Generate Markdown Report
    print("\n4. Generating Markdown Report...")
    generate_markdown_report(longitudinal_data, longitudinal_data_2l, frame_data)
    
if __name__ == "__main__":
    main()

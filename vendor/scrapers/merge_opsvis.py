#!/usr/bin/env python3

"""
A Python script to merge all .py files from the opsvis_scripts directory 
into a single, large text file for LLM context.
"""

import os

# --- Configuration ---

# The directory where your opsvis scripts were downloaded
SCRIPT_DIR = "opsvis_scripts"

# The name of the final merged file
MERGED_FILE = "merged_opsvis_examples.txt"

# --- Main Execution ---

def main():
    """
    Main function to find, read, and merge all .py files.
    """
    
    all_code_blocks = []
    print(f"Starting to merge files from '{SCRIPT_DIR}'...")
    
    try:
        filenames = os.listdir(SCRIPT_DIR)
        py_files = sorted([f for f in filenames if f.endswith(".py")])
        
        if not py_files:
            print(f"No .py files found in '{SCRIPT_DIR}'. Exiting.")
            return

        print(f"Found {len(py_files)} .py files to merge.")
        
        for filename in py_files:
            filepath = os.path.join(SCRIPT_DIR, filename)
            
            # Add a clear header for the LLM
            header = f"# === START: {filename} ==="
            all_code_blocks.append(header)
            
            # Read and add the file's content
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    all_code_blocks.append(f.read().strip())
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
                all_code_blocks.append(f"# ERROR READING {filename}")
            
            # Add a clear footer for the LLM
            footer = f"# === END: {filename} ==="
            all_code_blocks.append(footer)
            
        # Write everything to the single merged file
        print(f"\nWriting all content to {MERGED_FILE}...")
        with open(MERGED_FILE, "w", encoding="utf-8") as f:
            f.write("\n\n".join(all_code_blocks))
            
        print("--- Merging complete! ---")
        print(f"File created: {MERGED_FILE}")

    except FileNotFoundError:
        print(f"Error: The directory '{SCRIPT_DIR}' was not found.")
        print(f"Please run the download script first or ensure this script is in the correct parent directory.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
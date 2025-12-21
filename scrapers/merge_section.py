#!/usr/bin/env python3

"""
A Python script to merge all .py files from the sectionproperties_scripts directory 
into a single, large text file for LLM context.
"""

import os

# --- Configuration ---

# The directory where your sectionproperties scripts were downloaded
SCRIPT_DIR = "sectionproperties_scripts" # Changed directory name

# The name of the final merged file
MERGED_FILE = "merged_sectionproperties_examples.txt" # Changed output filename

# --- Main Execution ---

def main():
    """
    Main function to find, read, and merge all .py files.
    """
    
    # A list to hold the content of all files
    all_code_blocks = []
    
    print(f"Starting to merge files from '{SCRIPT_DIR}'...")
    
    try:
        # Get a list of all files in the directory
        filenames = os.listdir(SCRIPT_DIR)
        
        # Filter for .py files and sort them (optional, but nice)
        py_files = sorted([f for f in filenames if f.endswith(".py")])
        
        if not py_files:
            print(f"No .py files found in '{SCRIPT_DIR}'. Exiting.")
            return

        print(f"Found {len(py_files)} .py files to merge.")
        
        # Loop through each python file
        for filename in py_files:
            filepath = os.path.join(SCRIPT_DIR, filename)
            
            # 1. Add a clear header for the LLM
            header = f"""
# ==============================================================================
# START: {filename}
# ==============================================================================
            """.strip()
            all_code_blocks.append(header)
            
            # 2. Read and add the file's content
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    all_code_blocks.append(f.read())
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
            
            # 3. Add a clear footer for the LLM
            footer = f"""
# ==============================================================================
# END: {filename}
# ==============================================================================
            """.strip()
            all_code_blocks.append(footer)
            
        # Write everything to the single merged file
        print(f"\nWriting all content to {MERGED_FILE}...")
        with open(MERGED_FILE, "w", encoding="utf-8") as f:
            # Join all blocks with two newlines for readability
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
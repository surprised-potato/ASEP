#!/usr/bin/env python3

"""
A Python script to parse a local HTML file (anastruct_examples.html),
extract Python code blocks, remove line numbers, and save them to a Markdown file.
"""

import os
import re
from bs4 import BeautifulSoup

# --- Configuration ---

# The file containing the HTML you provided
INPUT_HTML_FILE = "anastruct_downloads/anastruct_examples.html"

# Changed extension to .md for Markdown support
OUTPUT_FILE = "merged_anastruct_examples.md"

# --- Helper Functions ---

def clean_code_block(raw_code: str) -> str:
    """
    Removes leading line numbers (e.g., ' 1', '2', '10 ') from code lines.
    This handles the specific Sphinx formatting in the provided HTML.
    """
    cleaned_lines = []
    # Regex to match start of line + optional whitespace + digits + optional space
    line_number_pattern = re.compile(r"^\s*\d+\s*") 
    
    for line in raw_code.splitlines():
        # Remove the line number pattern
        cleaned_line = line_number_pattern.sub("", line)
        
        # Only add non-empty lines or genuine spacing
        if cleaned_line.strip() or line.strip() == "": 
            cleaned_lines.append(cleaned_line)

    return "\n".join(cleaned_lines)

def main():
    print(f"Reading local file: {INPUT_HTML_FILE}...")
    
    if not os.path.exists(INPUT_HTML_FILE):
        print(f"Error: Could not find '{INPUT_HTML_FILE}'.")
        print("Please save the HTML content into a file with this name first.")
        return

    try:
        with open(INPUT_HTML_FILE, "r", encoding="utf-8") as f:
            html_content = f.read()
            
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Select code blocks
        code_blocks = soup.select("div.highlight-python pre")
        if not code_blocks:
            code_blocks = soup.select("div.highlight pre")

        print(f"Found {len(code_blocks)} code blocks.")
        
        extracted_content = []
        
        # Markdown Header
        extracted_content.append(f"# Extracted Examples from {INPUT_HTML_FILE}\n")

        for i, block in enumerate(code_blocks):
            raw_text = block.get_text()
            clean_text = clean_code_block(raw_text)
            
            if clean_text.strip():
                # Added Markdown Heading and Code Fences
                extracted_content.append(f"## Example Block {i+1}")
                extracted_content.append("```python")
                extracted_content.append(clean_text)
                extracted_content.append("```")
                extracted_content.append("\n---\n") # Visual separator in Markdown

        # Write to output file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(extracted_content))
            
        print(f"Successfully created: {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3

"""
A Python script to scrape all code examples from the opsvis
ReadTheDocs website and save each example as a separate .py file.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Set
import os
import time
import re

# --- Configuration ---

# The main "Examples" page URL for opsvis
START_PAGE_URL = "https://opsvis.readthedocs.io/en/latest/examples.html"

# The directory to save the downloaded .py scripts
DOWNLOAD_DIR = "opsvis_scripts"

# Set a User-Agent to be polite
HEADERS = {
    "User-Agent": "Opsvis-Script-Downloader-Bot (https://github.com/)"
}

# --- Helper Functions ---

def get_example_links(page_url: str) -> List[str]:
    """
    Fetches the main examples page and extracts the direct URLs 
    for all individual example pages.
    """
    print(f"Fetching main examples page: {page_url}")
    example_urls = []
    try:
        response = requests.get(page_url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # The links are in the main article body
        article_body = soup.find("div", itemprop="articleBody")
        if not article_body:
            print("Error: Could not find the main article body on the examples page.")
            return []

        links = article_body.find_all("a", href=True)
        for link in links:
            href = link.get("href")
            # Filter for relative links to .html files
            if href and href.endswith(".html") and not href.startswith(("../", "http:", "https:", "#")):
                full_url = urljoin(page_url, href)
                if full_url not in example_urls:
                    example_urls.append(full_url)

        print(f"Found {len(example_urls)} example pages to scrape.")
        return example_urls

    except requests.RequestException as e:
        print(f"Error fetching page {page_url}: {e}")
        return []
    except Exception as e:
        print(f"Error parsing page {page_url}: {e}")
        return []

def clean_code_block(raw_code: str) -> str:
    """Removes leading line numbers from code lines."""
    cleaned_lines = []
    # Regex to find optional leading space, digits, then an optional single space
    line_number_pattern = re.compile(r"^\s*\d+\s?") 
    
    for line in raw_code.splitlines():
        cleaned_line = line_number_pattern.sub("", line)
        cleaned_lines.append(cleaned_line)
        
    return "\n".join(cleaned_lines)


def save_script_from_page(page_url: str, save_directory: str) -> None:
    """
    Fetches an example page, extracts and cleans Python code,
    and saves it as a .py file.
    """
    try:
        print(f"--- Processing: {page_url} ---")
        time.sleep(0.5) 
        response = requests.get(page_url, headers=HEADERS)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Selectors for code blocks
        code_blocks_raw = soup.select("div.highlight-default pre, div.highlight-python pre")
        
        if not code_blocks_raw:
            print(f"No code blocks found on {page_url}.")
            return

        all_cleaned_code = []
        for block in code_blocks_raw:
            raw_text = block.get_text()
            if raw_text.strip():
                cleaned_text = clean_code_block(raw_text)
                if cleaned_text.strip(): 
                    all_cleaned_code.append(cleaned_text)
        
        if not all_cleaned_code:
             print(f"No valid code found after cleaning on {page_url}.")
             return
             
        script_content = "\n\n".join(all_cleaned_code)
        
        html_filename = page_url.split("/")[-1]
        py_filename = os.path.splitext(html_filename)[0] + ".py"
        save_path = os.path.join(save_directory, py_filename)
        
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(f"# Script content scraped from: {page_url}\n\n")
            f.write(script_content)
            
        print(f"Successfully saved cleaned script to: {save_path}")

    except requests.RequestException as e:
        print(f"Error downloading {page_url}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred for {page_url}: {e}")

# --- Main Execution ---

def main():
    """ Main function """
    print(f"Ensuring script directory exists: ./{DOWNLOAD_DIR}")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    example_links = get_example_links(START_PAGE_URL)
    if not example_links:
        print("No example links found. Exiting.")
        return
        
    print(f"\n--- Starting to scrape code from {len(example_links)} pages ---")
    
    for link in sorted(example_links): 
        save_script_from_page(link, DOWNLOAD_DIR)
        
    print("\n--- Script download complete! ---")
    print(f"All .py files saved in the '{DOWNLOAD_DIR}' folder.")

if __name__ == "__main__":
    main()
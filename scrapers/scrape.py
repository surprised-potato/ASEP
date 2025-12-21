#!/usr/bin/env python3

"""
A Python script to scrape all code examples from the concrete-properties
ReadTheDocs website and save each example as a separate .py file.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List
import os

# --- Configuration ---

# The main "Examples" page URL
START_PAGE_URL = "https://concrete-properties.readthedocs.io/en/stable/examples.html"

# The directory to save the downloaded .py scripts
DOWNLOAD_DIR = "python_scripts"

# Set a User-Agent to be polite
HEADERS = {
    "User-Agent": "Concrete-Properties-Script-Downloader (https://github.com/)"
}

# --- Helper Functions ---

def get_example_links(page_url: str) -> List[str]:
    """
    Fetches the main examples page and extracts the URLs 
    for all individual example notebooks.
    
    Args:
        page_url: The URL of the main "Examples" index page.
    
    Returns:
        A list of absolute URLs for each example page.
    """
    print(f"Fetching main examples page: {page_url}")
    try:
        response = requests.get(page_url, headers=HEADERS)
        response.raise_for_status()  # Raise an exception for bad status codes

        # --- UPDATED LINE ---
        # Changed "lxml" to "html.parser" (Python's built-in parser)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find the gallery container
        gallery = soup.find("div", class_="nbsphinx-gallery")
        
        if not gallery:
            print("Error: Could not find the 'nbsphinx-gallery' container.")
            return []

        # Find all <a> tags within the gallery
        links = gallery.find_all("a")
        
        # Create absolute URLs from the relative 'href' attributes
        example_urls = []
        for link in links:
            href = link.get("href")
            if href:
                # Use urljoin to safely combine the base URL and the relative link
                full_url = urljoin(page_url, href)
                if full_url not in example_urls:
                    example_urls.append(full_url)
        
        print(f"Found {len(example_urls)} example pages to scrape.")
        return example_urls

    except requests.RequestException as e:
        print(f"Error fetching main page: {e}")
        return []
    except Exception as e:
        print(f"Error parsing main page: {e}")
        return []

def save_script_from_page(page_url: str, save_directory: str) -> None:
    """
    Fetches an individual example page, extracts all Python code,
    and saves it as a single .py file.
    
    Args:
        page_url: The URL of a specific example page.
        save_directory: The folder to save the .py file in.
    """
    try:
        print(f"--- Processing: {page_url} ---")
        response = requests.get(page_url, headers=HEADERS)
        response.raise_for_status()
        
        # --- UPDATED LINE ---
        # Changed "lxml" to "html.parser"
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Code blocks are in <pre> tags inside <div class="input_area">
        code_blocks = soup.select("div.input_area pre")
        
        if not code_blocks:
            print(f"No code blocks found on {page_url}.")
            return

        # Combine all code blocks into one string
        all_code = [block.get_text() for block in code_blocks]
        script_content = "\n\n".join(all_code)
        
        # Get a filename from the URL (e.g., "area_properties.html")
        html_filename = page_url.split("/")[-1]
        # Change the extension to .py (e.g., "area_properties.py")
        py_filename = os.path.splitext(html_filename)[0] + ".py"
        
        # Create the full path to save the file
        save_path = os.path.join(save_directory, py_filename)
        
        # Save the combined code as a .py file
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(f"# Script content scraped from: {page_url}\n\n")
            f.write(script_content)
            
        print(f"Successfully saved script to: {save_path}")

    except requests.RequestException as e:
        print(f"Error downloading {page_url}: {e}")
    except IOError as e:
        print(f"Error saving file for {page_url}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred for {page_url}: {e}")

# --- Main Execution ---

def main():
    """
    Main function to orchestrate the scraping and saving process.
    """
    # Create the download directory if it doesn't exist
    print(f"Ensuring script directory exists: ./{DOWNLOAD_DIR}")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    # 1. Scrape the links
    example_links = get_example_links(START_PAGE_URL)
    
    if not example_links:
        print("No example links found. Exiting.")
        return
        
    print(f"\n--- Starting to scrape {len(example_links)} scripts ---")
    
    # 2. Visit each link, extract code, and save as .py
    for link in example_links:
        save_script_from_page(link, DOWNLOAD_DIR)
        
    print("\n--- Script download complete! ---")
    print(f"All .py files saved in the '{DOWNLOAD_DIR}' folder.")

if __name__ == "__main__":
    main()
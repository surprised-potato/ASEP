#!/usr/bin/env python3

"""
A Python script to scrape all code examples from the OpenSeesPy
ReadTheDocs website, following category links, and save each 
final example as a separate, cleaned .py file (removing line numbers).
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Set
import os
import time
import re # Import the regular expression module

# --- Configuration ---

# The main "Examples" index page URL for OpenSeesPy
START_PAGE_URL = "https://openseespydoc.readthedocs.io/en/latest/src/examples.html"

# The directory to save the downloaded .py scripts
DOWNLOAD_DIR = "openseespy_scripts" 

# Set a User-Agent to be polite
HEADERS = {
    "User-Agent": "OpenSeesPy-Script-Downloader-Bot (https://github.com/)"
}

# --- Helper Functions ---

def get_category_links(page_url: str) -> List[str]:
    """
    Fetches the main examples index page and extracts URLs for category pages.
    """
    print(f"Fetching main examples index page: {page_url}")
    category_urls = []
    try:
        response = requests.get(page_url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        article_body = soup.find("div", itemprop="articleBody")
        if not article_body:
            print("Error: Could not find the main article body on index page.")
            return []

        links = article_body.find_all("a", href=True)
        for link in links:
            href = link.get("href")
            if href and href.endswith(".html") and not href.startswith(("../", "http:", "https:", "#")):
                 full_url = urljoin(page_url, href)
                 if full_url != page_url:
                    category_urls.append(full_url)

        print(f"Found {len(category_urls)} category pages.")
        return category_urls

    except requests.RequestException as e:
        print(f"Error fetching index page {page_url}: {e}")
        return []
    except Exception as e:
        print(f"Error parsing index page {page_url}: {e}")
        return []


def get_final_example_links(category_urls: List[str]) -> Set[str]:
    """
    Fetches each category page and extracts the final example page URLs.
    Uses a set to avoid duplicates.
    """
    final_urls = set()
    print("\n--- Fetching links from category pages ---")
    for cat_url in category_urls:
        print(f"Checking category: {cat_url}")
        try:
            time.sleep(0.5) 
            response = requests.get(cat_url, headers=HEADERS)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            article_body = soup.find("div", itemprop="articleBody")
            if not article_body:
                print(f"Warning: Could not find article body on {cat_url}")
                continue

            links = article_body.find_all("a", href=True)
            found_on_page = 0
            for link in links:
                href = link.get("href")
                if href and href.endswith(".html") and not href.startswith(("../", "http:", "https:", "#")):
                    full_url = urljoin(cat_url, href)
                    if full_url != cat_url: 
                        final_urls.add(full_url)
                        found_on_page += 1
            print(f"Found {found_on_page} example links on {cat_url}")

        except requests.RequestException as e:
            print(f"Error fetching category page {cat_url}: {e}")
        except Exception as e:
            print(f"Error parsing category page {cat_url}: {e}")
            
    print(f"\nTotal unique example pages found: {len(final_urls)}")
    return final_urls

# --- UPDATED FUNCTION ---
def clean_code_block(raw_code: str) -> str:
    """Removes leading line numbers like ' 1', '2', '10 ' etc. from code lines."""
    cleaned_lines = []
    # Refined regex: Start of line, optional space, digits, optional single space
    line_number_pattern = re.compile(r"^\s*\d+\s?") 
    
    for line in raw_code.splitlines():
        # Remove the matched pattern from the beginning of the line
        cleaned_line = line_number_pattern.sub("", line)
        # Only add the line if it's not empty after cleaning (handles lines with only numbers)
        if cleaned_line.strip():
            cleaned_lines.append(cleaned_line)
        # Keep empty lines that were originally empty (don't strip them)
        elif not line.strip(): 
             cleaned_lines.append(line)


    return "\n".join(cleaned_lines)
# --- END UPDATED FUNCTION ---


def save_script_from_page(page_url: str, save_directory: str) -> None:
    """
    Fetches an individual example page, extracts and cleans Python code,
    and saves it as a single .py file.
    """
    try:
        print(f"--- Processing: {page_url} ---")
        time.sleep(0.5) 
        response = requests.get(page_url, headers=HEADERS)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        code_blocks_raw = soup.select("div.highlight-default pre, div.highlight-python pre") 
        
        if not code_blocks_raw:
            article_body = soup.find("div", itemprop="articleBody")
            if article_body:
                 code_blocks_raw = article_body.select('div[class*="highlight"] pre')
                 if not code_blocks_raw:
                      code_blocks_raw = article_body.select('pre') 
                      if not code_blocks_raw:
                          print(f"No code blocks found on {page_url}.")
                          return
            else:
                print(f"No article body or code blocks found on {page_url}.")
                return

        all_cleaned_code = []
        for block in code_blocks_raw:
            raw_text = block.get_text()
            if raw_text.strip(): # Only process non-empty blocks
                cleaned_text = clean_code_block(raw_text)
                # Ensure something remains after cleaning before adding
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
    except IOError as e:
        print(f"Error saving file for {page_url}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred for {page_url}: {e}")

# --- Main Execution ---

def main():
    """ Main function """
    print(f"Ensuring script directory exists: ./{DOWNLOAD_DIR}")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    category_links = get_category_links(START_PAGE_URL)
    if not category_links:
        print("No category links found. Exiting.")
        return

    final_example_links = get_final_example_links(category_links)
    if not final_example_links:
        print("No final example links found after checking categories. Exiting.")
        return
        
    print(f"\n--- Starting to scrape code from {len(final_example_links)} final example pages ---")
    
    for link in sorted(list(final_example_links)): 
        save_script_from_page(link, DOWNLOAD_DIR)
        
    print("\n--- Script download complete! ---")
    print(f"All .py files saved in the '{DOWNLOAD_DIR}' folder.")

if __name__ == "__main__":
    main()
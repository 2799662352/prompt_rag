#!/usr/bin/env python3

import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import argparse
import time

class WebsiteDownloader:
    def __init__(self, delay=1):
        """Initialize the website downloader with options."""
        self.delay = delay  # Delay between requests to be respectful
        self.visited_urls = set()  # Keep track of URLs already visited
        self.page_count = 0
        self.skipped_count = 0
        
    def download_page(self, url):
        """Download a single page and save it to the output directory."""
        try:
            # Create a path for saving the file
            parsed_url = urlparse(url)
            path = parsed_url.path
            
            # Handle the root path
            if path == "" or path == "/":
                filepath = os.path.join(self.output_dir, "index.html")
            else:
                # Remove leading slash and create directory structure
                if path.startswith("/"):
                    path = path[1:]
                
                # Handle trailing slash (directory index)
                if path.endswith("/"):
                    path = os.path.join(path, "index.html")
                elif "." not in os.path.basename(path):
                    path = os.path.join(path, "index.html")
                
                filepath = os.path.join(self.output_dir, path)
            
            # Check if file already exists, skip if it does
            if os.path.exists(filepath):
                print(f"Skipping (already exists): {url} -> {filepath}")
                self.skipped_count += 1
                
                # Still need to return content for link extraction
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        return f.read()
                except:
                    # If we can't read the existing file, download it anyway
                    pass
            
            # If the file doesn't exist, download it
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                # Save the content
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                print(f"Downloaded: {url} -> {filepath}")
                return response.text
            else:
                print(f"Failed to download {url}: HTTP {response.status_code}")
                return None
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return None

    def extract_links(self, html, base_url, scope_path):
        """Extract links from HTML content that match the scope path."""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        parsed_base = urlparse(base_url)
        base_domain = parsed_base.netloc
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            
            # Skip anchor links (links with # that point to sections within the same page)
            if '#' in href:
                continue
                
            full_url = urljoin(base_url, href)
            
            parsed_url = urlparse(full_url)
            
            # Only include links from the same domain and within the scope path
            if parsed_url.netloc == base_domain and parsed_url.path.startswith(scope_path):
                links.append(full_url)
                
        return links

    def process_url_list(self, url_list_file):
        """Process a list of URLs and download pages within each URL's scope."""        
        # Read URLs from the file
        with open(url_list_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        total_downloaded = 0
        
        for start_url in urls:
            print(f"\nProcessing URL: {start_url}")
            
            # Parse the URL to determine the scope
            parsed_url = urlparse(start_url)
            path = parsed_url.path
            
            # Sanitize the domain name by replacing dots with hyphens
            domain_folder = parsed_url.netloc.replace('.', '-')
            
            # Current output directory for the current URL
            self.output_dir = "artifacts/downloaded_sites/" + domain_folder
            # Create output directory if it doesn't exist
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Determine the scope path (directory containing the index.html)
            if path.endswith('index.html'):
                scope_path = path[:-10]  # Remove 'index.html'
            elif path.endswith('/'):
                scope_path = path
            else:
                scope_path = path + '/'
            
            # Reset visited URLs for each new scope
            self.visited_urls = set()
            
            # Queue of URLs to visit
            queue = [start_url]
            
            # Process the queue
            while queue:
                url = queue.pop(0)
                
                # Skip if already visited
                if url in self.visited_urls:
                    continue
                
                # Mark as visited
                self.visited_urls.add(url)
                
                # Download the page
                html_content = self.download_page(url)
                
                if html_content:
                    total_downloaded += 1
                    # Extract links and add to queue if they're within scope
                    new_links = self.extract_links(html_content, url, scope_path)
                    for link in new_links:
                        if link not in self.visited_urls and link not in queue:
                            queue.append(link)
                
                # Be nice to the server
                time.sleep(self.delay)
        
        print(f"\nDownloading completed. Total pages: {total_downloaded}")
        print(f"Downloaded: {total_downloaded - self.skipped_count}, Skipped: {self.skipped_count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download pages from specified URLs and their subdirectories.")
    parser.add_argument("--delay", "-d", type=float, default=1.0,
                        help="Delay between requests in seconds (default: 1.0)")
    
    args = parser.parse_args()
    
    downloader = WebsiteDownloader(
        delay=args.delay
    )
    
    downloader.process_url_list("websites_to_download.txt")
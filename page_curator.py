#!/usr/bin/env python3

import os
import re
import argparse
from bs4 import BeautifulSoup

class PageCurator:
    def __init__(self, input_dir):
        """Initialize the curator with input and output directories."""
        self.input_dir = input_dir
        self.output_dir = os.path.join("artifacts", "curated")
        
        # Extract the domain name to preserve folder structure
        if os.path.basename(os.path.dirname(input_dir)) == "downloaded_sites":
            # If input is directly a domain folder under downloaded_sites
            self.domain = os.path.basename(input_dir)
        else:
            # In case input path is deeper (e.g., downloaded_sites/domain/en/stable)
            # Extract the first folder after downloaded_sites
            parts = input_dir.split(os.sep)
            if "downloaded_sites" in parts:
                idx = parts.index("downloaded_sites")
                if idx + 1 < len(parts):
                    self.domain = parts[idx + 1]
                else:
                    self.domain = None
            else:
                self.domain = None
        
    def clean_html(self, html_content):
        """Clean the HTML content by removing scripts, styles, and unnecessary navigation elements."""
        # Clean non-UTF8 and special characters first
        html_content = re.sub(r'[^\x00-\x7F]+', '', html_content) 
        
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style tags
        for tag in soup(['script', 'style', 'iframe', 'noscript']):
            tag.decompose()
        
        # Remove navigation elements, search boxes, etc.
        selectors_to_remove = [
            'nav',                     # Navigation menus
            '.nav',                    # Navigation classes
            '.navigation',
            '.navbar',
            '.sidebar',
            '.menu',
            '.header',                 # Headers often contain navigation
            '.footer',                 # Footers often contain irrelevant links
            '.search',                 # Search forms
            '.pagination',             # Next/prev links
            '[role="search"]',         # Elements with search role
            '[role="navigation"]',     # Elements with navigation role
            '.wy-nav-side',           # ReadTheDocs specific
            '.wy-side-scroll',
            '.wy-side-nav-search',
            '.wy-menu',
            '.rst-versions',
            '.wy-nav-top',
            '.toc',                    # Table of contents (often in sidebar)
            '.breadcrumb',            # Breadcrumbs navigation
            '.toctree',               # Documentation table of contents
            '.toctree-l1',           # Documentation TOC levels
            '.toctree-l2',
            '.toctree-l3',
            '.toctree-l4',
            '.contents',              # Alternative name for table of contents
            '#table-of-contents',     # Common TOC id
            '[role="contentinfo"]'    # Often contains TOC or navigation
        ]
        
        for selector in selectors_to_remove:
            for element in soup.select(selector):
                element.decompose()
        
        # Remove links that are likely navigation or external
        for a_tag in soup.find_all('a'):
            href = a_tag.get('href', '')
            
            # Check if link is likely to be navigation or external
            is_nav_link = False
            nav_patterns = ['search', 'next', 'prev', 'previous', 'index', 'home', 'contact', 'about']
            
            # Check text content of the link
            if a_tag.text and any(pattern in a_tag.text.lower() for pattern in nav_patterns):
                is_nav_link = True
            
            # Check href attribute
            if href and (href.startswith('http') or any(pattern in href.lower() for pattern in nav_patterns)):
                is_nav_link = True
            
            # Replace navigation links with just their text content
            if is_nav_link:
                a_tag.replace_with(a_tag.text)
        
        # Remove empty containers
        for tag in soup.find_all():
            if tag.name != 'br' and tag.name != 'img' and not tag.text.strip() and not tag.contents:
                tag.decompose()
                
        # Get the main content - focus on main, article, or content sections if available
        main_content = None
        for selector in ['main', 'article', '#content', '.content', '.main-content', '.document', '.section']:
            content_section = soup.select_one(selector)
            if content_section:
                main_content = content_section
                break
        
        # If we found a main content area, use it; otherwise use the whole body
        if main_content:
            cleaned_html = str(main_content)
        else:
            # If no clear main content, use the body or just everything if body is not found
            body = soup.body or soup
            cleaned_html = str(body)
            
        return cleaned_html
    
    def html_to_markdown(self, html_content):
        """Convert cleaned HTML content to Markdown format."""
        # Convert HTML to Markdown using html2text
        try:
            import html2text
            h = html2text.HTML2Text()
            h.ignore_links = True
            h.ignore_images = True
            h.ignore_tables = False
            h.ignore_emphasis = True
            markdown_content = h.handle(html_content)
            return markdown_content
        except ImportError:
            # Fallback to using BeautifulSoup for basic text extraction
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract text with some structure preservation
            markdown_lines = []
            
            # Process headings
            for i in range(1, 7):
                for heading in soup.find_all(f'h{i}'):
                    markdown_lines.append(f"{'#' * i} {heading.text.strip()}\n")
            
            # Process paragraphs
            for p in soup.find_all('p'):
                markdown_lines.append(f"{p.text.strip()}\n\n")
            
            # Process lists
            for ul in soup.find_all('ul'):
                for li in ul.find_all('li'):
                    markdown_lines.append(f"* {li.text.strip()}\n")
                markdown_lines.append("\n")
            
            for ol in soup.find_all('ol'):
                for i, li in enumerate(ol.find_all('li')):
                    markdown_lines.append(f"{i+1}. {li.text.strip()}\n")
                markdown_lines.append("\n")
            
            return ''.join(markdown_lines)
    
    def process_file(self, filepath):
        """Process a single HTML file."""
        try:
            # Read the file
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            
            # Clean the HTML
            cleaned_html = self.clean_html(html_content)
            
            # Convert to Markdown
            markdown_content = self.html_to_markdown(cleaned_html)
            
            # Determine the output path
            rel_path = os.path.relpath(filepath, self.input_dir)
            
            # If we have a domain, include it in the output path
            if self.domain:
                output_path = os.path.join(self.output_dir, self.domain, rel_path)
            else:
                output_path = os.path.join(self.output_dir, rel_path)
            
            # Change file extension to .md
            output_path = os.path.splitext(output_path)[0] + '.md'
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write the markdown content
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"Processed: {filepath} -> {output_path}")
            return True
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
            return False

    def process_directory(self):
        """Process all HTML files in the input directory."""
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Count for statistics
        processed_files = 0
        failed_files = 0
        
        # Walk through the input directory
        for root, dirs, files in os.walk(self.input_dir):
            for file in files:
                if file.endswith('.html'):
                    filepath = os.path.join(root, file)
                    success = self.process_file(filepath)
                    if success:
                        processed_files += 1
                    else:
                        failed_files += 1
        
        print(f"\nCuration completed. Processed {processed_files} files. Failed: {failed_files}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean up downloaded web pages for embedding.")
    parser.add_argument("--input", "-i", 
                        help="Input directory containing downloaded website")
   
    args = parser.parse_args()
    
    curator = PageCurator(input_dir=args.input)
    curator.process_directory()
from habanero import Crossref
from arxiv import Search
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import json
import html
from typing import List, Optional, Dict, Any, Tuple

class CitationFormatter:
    """A class to handle creation of APA citations for different types of sources."""
    
    def __init__(self):
        self.crossref = Crossref()
    
    @staticmethod
    def format_author_name(author_name: str) -> str:
        """Format an author name into APA style (Last, F.M.)."""
        parts = author_name.strip().split()
        if len(parts) < 2:
            return author_name
        
        last_name = parts[-1]
        first_names = parts[:-1]
        initials = '.'.join(name[0].upper() for name in first_names)
        return f"{last_name}, {initials}."
    
    @staticmethod
    def format_author_list(authors: List[str]) -> Optional[str]:
        """Format a list of authors according to APA style."""
        if not authors:
            return None
            
        formatted_authors = [CitationFormatter.format_author_name(author) for author in authors]
        
        if len(formatted_authors) == 1:
            return formatted_authors[0]
        elif len(formatted_authors) == 2:
            return f"{formatted_authors[0]} & {formatted_authors[1]}"
        else:
            return f"{formatted_authors[0]} et al."
    
    def create_doi_citation(self, doi: str) -> str:
        """Create an APA citation for a DOI."""
        try:
            work = self.crossref.works(ids=doi)['message']
            
            # Extract authors
            authors = work.get('author', [])
            if authors:
                if len(authors) == 1:
                    author_text = f"{authors[0]['family']}, {authors[0]['given'][0]}."
                elif len(authors) == 2:
                    author_text = f"{authors[0]['family']}, {authors[0]['given'][0]}., & {authors[1]['family']}, {authors[1]['given'][0]}."
                else:
                    author_text = f"{authors[0]['family']}, {authors[0]['given'][0]}., et al."
            else:
                author_text = ""
            
            # Extract metadata
            title = work.get('title', [''])[0]
            journal = work.get('container-title', [''])[0]
            year = work.get('published-print', {}).get('date-parts', [['']])[0][0]
            volume = work.get('volume', '')
            issue = work.get('issue', '')
            pages = work.get('page', '')
            
            # Format citation
            citation = f"{author_text} ({year}). {title}. "
            if journal:
                citation += f"<i>{journal}</i>"
                if volume:
                    citation += f", <i>{volume}</i>"
                if issue:
                    citation += f"({issue})"
                if pages:
                    citation += f", {pages}"
            citation += f". https://doi.org/{doi}"
            
            return citation
        except Exception as e:
            raise ValueError(f"Error processing DOI citation: {str(e)}")
    
    def create_arxiv_citation(self, arxiv_id: str) -> str:
        """Create an APA citation for an arXiv paper."""
        try:
            search = Search(id_list=[arxiv_id])
            paper = next(search.results())
            
            # Convert arxiv Author objects to strings and format them
            author_names = [str(author) for author in paper.authors]
            author_text = self.format_author_list(author_names)
            if not author_text:
                author_text = ""
            
            return f"{author_text} ({paper.published.year}). {paper.title}. <i>arXiv preprint arXiv:{arxiv_id}</i>"
        except Exception as e:
            raise ValueError(f"Error processing arXiv citation: {str(e)}")
    
    def extract_webpage_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract metadata from a webpage."""
        metadata = {
            'title': None,
            'authors': [],
            'pub_date': None,
            'site_name': None
        }
        
        # Extract title
        title_meta = (
            soup.find('meta', property='og:title')
            or soup.find('meta', property='twitter:title')
            or soup.find('meta', {'name': 'title'})
        )
        metadata['title'] = title_meta['content'] if title_meta else (soup.title.string if soup.title else None)
        
        # Extract authors from various sources
        authors = []
        
        # Schema.org metadata
        schema_authors = soup.find_all('meta', {'itemprop': 'author'}) or []
        authors.extend(author['content'] for author in schema_authors if author.get('content'))
        
        # Article and Dublin Core metadata
        if not authors:
            author_metas = (
                soup.find_all('meta', property='article:author') +
                soup.find_all('meta', {'name': 'author'}) +
                soup.find_all('meta', {'name': 'dc.creator'}) +
                soup.find_all('meta', {'name': 'citation_author'})
            )
            authors.extend(meta['content'] for meta in author_metas if meta.get('content'))
        
        # JSON-LD metadata
        if not authors:
            for script in soup.find_all('script', {'type': 'application/ld+json'}):
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'author' in data:
                        author_data = data['author']
                        if isinstance(author_data, list):
                            authors.extend(author['name'] for author in author_data if isinstance(author, dict) and 'name' in author)
                        elif isinstance(author_data, dict) and 'name' in author_data:
                            authors.append(author_data['name'])
                        elif isinstance(author_data, str):
                            authors.append(author_data)
                except:
                    continue
        
        metadata['authors'] = authors
        
        # Extract publication date
        pub_date_meta = (
            soup.find('meta', property='article:published_time')
            or soup.find('meta', property='og:article:published_time')
            or soup.find('meta', {'name': 'publication_date'})
        )
        metadata['pub_date'] = pub_date_meta['content'] if pub_date_meta else None
        
        # Extract site name
        site_name_meta = (
            soup.find('meta', property='og:site_name')
            or soup.find('meta', {'name': 'application-name'})
        )
        if site_name_meta:
            metadata['site_name'] = site_name_meta['content']
        else:
            domain = urlparse(url).netloc
            metadata['site_name'] = re.sub(r'^www\.', '', domain).replace('.', ' ').title()
        
        return metadata
    
    def create_webpage_citation(self, url: str) -> str:
        """Create an APA citation for a webpage."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            metadata = self.extract_webpage_metadata(soup, url)
            
            citation_parts = []
            
            # Add authors if available
            author_text = self.format_author_list(metadata['authors'])
            if author_text:
                citation_parts.append(html.escape(author_text))
            
            # Add year
            current_year = datetime.now().year
            if metadata['pub_date']:
                try:
                    pub_datetime = datetime.fromisoformat(metadata['pub_date'].replace('Z', '+00:00'))
                    citation_parts.append(f"({pub_datetime.year})")
                except ValueError:
                    citation_parts.append(f"({current_year})")
            else:
                citation_parts.append(f"({current_year})")
            
            # Add title if available
            if metadata['title']:
                citation_parts.append(html.escape(metadata['title'].strip()))
            
            # Add site name and retrieval date
            citation_parts.append(f"<i>{html.escape(metadata['site_name'])}</i>")
            citation_parts.append(f"Retrieved {datetime.now().strftime('%B %d, %Y')}, from {url}")
            
            return ". ".join(citation_parts)
            
        except Exception as e:
            # Fallback to basic citation
            domain = re.sub(r'^www\.', '', re.sub(r'https?://', '', url)).split('/')[0]
            site_name = domain.replace('.', ' ').title()
            return f"<i>{site_name}</i>. ({datetime.now().year}). Retrieved {datetime.now().strftime('%B %d, %Y')}, from {url}"

def create_apa_citation(identifier: str) -> str:
    """
    Creates an APA citation in HTML format for DOIs, arXiv IDs, or URLs.
    
    Args:
        identifier (str): DOI, arXiv ID, URL, or full link
        
    Returns:
        str: HTML formatted APA citation
    """
    formatter = CitationFormatter()
    
    # Check for DOI
    doi_match = re.search(r'(10\.\d{4,}/[-._;()/:\w]+)', identifier)
    if doi_match:
        try:
            return formatter.create_doi_citation(doi_match.group(1))
        except ValueError as e:
            return f"Error creating citation: {str(e)}"
    
    # Check for arXiv ID
    arxiv_match = re.search(r'(\d{4}\.\d{4,}|[a-z\-]+(\.[A-Z]{2})?/\d{7})', identifier)
    if arxiv_match:
        try:
            return formatter.create_arxiv_citation(arxiv_match.group(1))
        except ValueError as e:
            return f"Error creating citation: {str(e)}"
    
    # Handle as URL
    try:
        return formatter.create_webpage_citation(identifier)
    except Exception as e:
        return f"Error creating citation: {str(e)}"

def create_citation_list(references: List[str]) -> List[str]:
    """
    Creates a list of APA citations from a list of references.
    
    Args:
        references (list): List of reference strings

    Returns:
        str: HTML formatted APA citation list
    """
    return [create_apa_citation(reference) for reference in references]

if __name__ == "__main__":
    # Example usage
    references = [
        "https://doi.org/10.1080/00461520.2012.722805",
        "https://arxiv.org/abs/2401.03428",
        "https://www.nytimes.com/2025/02/08/us/politics/treasury-systems-raised-security-concerns.html"
    ]
    citations = create_citation_list(references)
    for citation in citations:
        print(citation)
        print()

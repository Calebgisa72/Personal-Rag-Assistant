import httpx
from bs4 import BeautifulSoup
from core.logger import logger

class URLScraperService:
    def __init__(self):
        # Set custom headers to minimize being blocked
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    async def scrape(self, url: str) -> tuple[str, str]:
        """
        Fetches a URL and extracts its text content and title.
        Returns a tuple of (title, extracted_text).
        """
        try:
            async with httpx.AsyncClient(headers=self.headers, follow_redirects=True) as client:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract title
                title = soup.title.string.strip() if soup.title and soup.title.string else "Untitled Scraped Page"
                
                # Remove scripts, styles, and other non-content tags to clean up the text
                for script in soup(["script", "style", "header", "footer", "nav", "aside"]):
                    script.extract()
                    
                # Extract text
                text = soup.get_text(separator='\n', strip=True)
                
                return title, text
        except httpx.HTTPError as e:
            logger.error(f"HTTP error scraping {url}: {e}")
            raise Exception(f"Failed to scrape URL: {url}") from e
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            raise Exception(f"Failed to extract content from URL: {url}") from e

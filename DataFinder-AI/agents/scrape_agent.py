import requests
import trafilatura
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

class ScrapeAgent:
    def scrape_metadata(self, url: str) -> dict:
        try:
            response = requests.get(url, timeout=10, headers={"User-Agent": "datafinder-ai/0.1"})
            response.raise_for_status()
            html_content = response.text

            # Try to extract with trafilatura first
            extracted_text = trafilatura.extract(html_content)
            
            # Fallback to BeautifulSoup if trafilatura fails
            if not extracted_text:
                soup = BeautifulSoup(html_content, "html.parser")
                extracted_text = " ".join(p.get_text() for p in soup.find_all('p'))

            soup = BeautifulSoup(html_content, "html.parser")
            title = soup.title.string.strip() if soup.title else url

            return {
                "url": url,
                "title": title,
                "description": (extracted_text[:500] if extracted_text else "").strip(),
                "source": self._infer_source(url)
            }

        except RequestException as e:
            return {
                "url": url,
                "title": "N/A",
                "description": f"Error during request: {e}",
                "source": self._infer_source(url)
            }
        except Exception as e:
            return {
                "url": url,
                "title": "N/A",
                "description": f"Error scraping: {e}",
                "source": self._infer_source(url)
            }

    def _infer_source(self, url: str) -> str:
        if "huggingface.co" in url:
            return "huggingface"
        if "kaggle.com" in url:
            return "kaggle"
        if "roboflow.com" in url:
            return "roboflow"
        if "mendeley.com" in url:
            return "mendeley"
        return "web"
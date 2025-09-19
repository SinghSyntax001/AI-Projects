import requests
import trafilatura
from bs4 import BeautifulSoup

class ScrapeAgent:
    def scrape_metadata(self, url: str) -> dict:
        try:
            response = requests.get(url, timeout=10, headers={"User-Agent": "datafinder-ai/0.1"})
            response.raise_for_status()
            html_content = response.text

            ext = trafilatura.extract(html_content)
            soup = BeautifulSoup(html_content, "html.parser")
            title = soup.title.string.strip() if soup.title else url

            return {
                "url": url,
                "title": title,
                "description": (ext[:500] if ext else "").strip(),
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

# agents/scrape_agent.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

class ScrapeAgent:
    def __init__(self):
        pass

    def scrape_metadata(self, url):
        print(f"\n🌐 Scraping metadata from: {url}")
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            title = soup.title.string.strip() if soup.title else "Unknown Title"
            domain = urlparse(url).netloc

            # Basic description
            description_tag = soup.find('meta', attrs={'name': 'description'}) or \
                              soup.find('meta', attrs={'property': 'og:description'})
            description = description_tag['content'].strip() if description_tag else "No description found."

            # Guessing license
            license_text = ""
            if "license" in response.text.lower():
                license_text = "May mention license on page. Please verify."

            # Guessing format from visible links
            links = soup.find_all('a', href=True)
            file_formats = list({link['href'].split('.')[-1] for link in links if '.' in link['href'] and len(link['href'].split('.')[-1]) <= 5})

            return {
                "url": url,
                "source": domain,
                "title": title,
                "description": description,
                "file_formats": file_formats,
                "license_note": license_text
            }

        except Exception as e:
            print(f"❌ Failed to scrape {url}: {str(e)}")
            return {
                "url": url,
                "error": str(e)
            }

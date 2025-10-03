from bs4 import BeautifulSoup
import requests
import json
from urllib.parse import urljoin 
from base_agent import base_agent

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/117.0.0.0 Safari/537.36"
}

class Website:
    def __init__(self, url):
        self.url = url
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        self.title = soup.title.string if soup.title else "No title found"

        if soup.body:
            for irrelevant in soup.body(["script", "style", "img", "input"]):
                irrelevant.decompose()
            self.text = soup.body.get_text(separator="\n", strip=True)
        else:
            self.text = ""

        links = [link.get('href') for link in soup.find_all('a')]
        self.links = [link for link in links if link]

    def get_contents(self):
        return f"Webpage Title:\n{self.title}\nWebpage Contents:\n{self.text}\n\n"


def get_links_user_prompt(website):
    user_prompt = f"Here is the list of links on the website of {website.url} - "
    user_prompt += ("please decide which of these are relevant web links for a brochure about the company, "
                    "respond with the full https URL in JSON format. "
                    "Do not include Terms of Service, Privacy, email links.\n")
    user_prompt += "Links (some might be relative links):\n"
    user_prompt += "\n".join(website.links)
    return user_prompt


link_system_prompt = (
    "You are provided with a list of links found on webpage. "
    "You are able to decide which of the links would be most relevant to include in a brochure about the company, "
    "such as links to an About page, or a Company page, or Careers/Jobs pages.\n"
    "You should respond in JSON as in this example:\n"
    "{\n"
    '    "links": [\n'
    '        {"type": "about page", "url": "https://full.url/goes/here/about"},\n'
    '        {"type": "careers page", "url": "https://another.full.url/careers"}\n'
    "    ]\n"
    "}"
)


def get_links(url):
    website = Website(url)
    user = get_links_user_prompt(website)

    response = base_agent(link_system_prompt, user, response_format={"type": "json_object"})
    result = response.choices[0].message.content
    data = json.loads(result)


    for link in data.get("links", []):
        if "url" in link:
            link["url"] = urljoin(url, link["url"])

    return data

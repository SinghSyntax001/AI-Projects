from website_scrapper import Website, get_links
from base_agent import base_agent
from IPython.display import Markdown, display

system_prompt = (
    "You are an assistant that analyzes the contents of several relevant pages from a company website "
    "and creates a short humorous, entertaining, jokey brochure about the company for prospective customers, "
    "investors and recruits. Respond in markdown. "
    "Include details of company culture, customers and careers/jobs if you have the information."
)

def get_all_details(url):
    result = "Landing page:\n"
    result += Website(url).get_contents()
    links = get_links(url)
    print("Found links:", links)

    for link in links.get("links", []):
        link_type = link.get("type", "page") 
        result += f"\n\n{link_type}\n"
        result += Website(link["url"]).get_contents()
    return result



def get_brochure_user_prompt(company_name, url):
    user_prompt = f"You are looking at a company called: {company_name}\n"
    user_prompt += ("Here are the contents of its landing page and other relevant pages; "
                    "use this information to build a short brochure of the company in markdown.\n")
    user_prompt += get_all_details(url)
    user_prompt = user_prompt[:5000]  # truncate if longer than 5k characters
    return user_prompt


def create_brochure(company_name, url, save_path="brochure.md"):
    response = base_agent(system_prompt, get_brochure_user_prompt(company_name, url), {"type": "text"})
    result = response.choices[0].message.content

    display(Markdown(result))

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"✅ Brochure saved to {save_path}")


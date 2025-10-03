from website_scrapper import get_links
from brochure_creator import create_brochure

print(get_links("https://huggingface.co"))

create_brochure("HuggingFace", "https://huggingface.co", save_path="huggingface_brochure.md")

from agents.search_agent import SearchAgent
from agents.scrape_agent import ScrapeAgent
from agents.relevance_agent import RelevanceAgent

def main():
    print("📦 AutoDataFinder.AI – Dataset Discovery Agent")
    user_query = input("\n🧠 Describe your ML problem (e.g., 'object detection for recycling robots'): ")

    # Run Search
    search_agent = SearchAgent()
    urls = search_agent.search(user_query)
    print(f"\n[DEBUG] Found {len(urls)} URLs")


    # Run Scraping
    print("\n🔍 Scraping metadata for each dataset...")
    scraper = ScrapeAgent()
   # Scraping section in main.py
    all_metadata = []
    for url in urls:
        data = scraper.scrape_metadata(url)
        print(f"[DEBUG] Scraped data for {url}: {data}")  
        all_metadata.append(data)


    # Run Relevance Evaluation
    relevance_agent = RelevanceAgent()
    final_output = []
    print("\n🧠 Evaluating relevance of datasets...\n")
    for meta in all_metadata:
        result = relevance_agent.evaluate(user_query, meta)
        meta.update(result)
        final_output.append(meta)

    # Print everything
    print("\n📊 Final Results:\n")
    for entry in final_output:
        print("\n-----------------------------")
        for k, v in entry.items():
            print(f"{k}: {v}")

if __name__ == "__main__":
    main()

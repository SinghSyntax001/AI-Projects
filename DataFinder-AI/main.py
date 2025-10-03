# main.py

from agents.search_agent import SearchAgent
from agents.scrape_agent import ScrapeAgent
from agents.relevance_agent import RelevanceAgent
# from agents.dataset_evaluator_agent import DatasetEvaluatorAgent  # 👈 optional LLM evaluator

def run_pipeline(query: str, top_k: int = 5):
    """
    Full dataset discovery pipeline:
    1. Search across sources
    2. Scrape metadata
    3. Rank by relevance
    4. (Optional) Evaluate robustness with LLM
    """

    print("📦 AutoDataFinder.AI – Dataset Discovery Agent")
    print(f"\n🧠 Problem Statement: {query}")

    # Step 1: Search
    search_agent = SearchAgent()
    urls = search_agent.search(query)
    print(f"\n[DEBUG] Found {len(urls)} dataset candidates")

    # Step 2: Scrape
    print("\n🔍 Scraping metadata...")
    scraper = ScrapeAgent()
    all_metadata = []
    for r in urls:
        metadata = scraper.scrape_metadata(r["url"])
        all_metadata.append(metadata)
        print(f"[DEBUG] Scraped: {metadata.get('title', 'N/A')}")

    # Step 3: Relevance Evaluation
    print("\n🧠 Evaluating relevance...")
    relevance_agent = RelevanceAgent()
    scored_results = []
    for meta in all_metadata:
        score = relevance_agent.evaluate(query, meta)
        meta.update(score)
        scored_results.append(meta)

    # Sort by relevance score
    scored_results = sorted(scored_results, key=lambda x: x.get("relevance_score", 0), reverse=True)

    # Step 4: (Optional) LLM-based Robustness Evaluation
    # evaluator = DatasetEvaluatorAgent()
    # for entry in scored_results[:top_k]:
    #     eval_result = evaluator.evaluate(query, entry)
    #     entry.update(eval_result)

    return scored_results[:top_k]


def main():
    """CLI mode: ask user for a query and print results"""
    user_query = input("\n🧠 Describe your ML problem (e.g., 'object detection for recycling robots'): ")
    results = run_pipeline(user_query, top_k=5)

    print("\n📊 Final Results:\n")
    for entry in results:
        print("\n-----------------------------")
        print(f"Title: {entry.get('title', 'N/A')}")
        print(f"URL: {entry.get('url', 'N/A')}")
        print(f"Source: {entry.get('source', 'N/A')}")
        print(f"Description: {entry.get('description', '')[:200]}...")
        print(f"Relevance Score: {entry.get('relevance_score', 'N/A')}")
        print(f"Reason: {entry.get('reason', 'N/A')}")
        # print(f"Robustness Score: {entry.get('robustness_score', 'N/A')}")
        # print(f"Robustness Reason: {entry.get('reason', 'N/A')}")


if __name__ == "__main__":
    main()

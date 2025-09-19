from typing import List, Dict
from kaggle.api.kaggle_api_extended import KaggleApi

def kaggle_search(query: str, max_results: int = 10) -> List[Dict]:
    kaggleapi = KaggleApi()
    kaggleapi.authenticate()
    
    datasets = kaggleapi.dataset_list(search=query, max_results=max_results)
    results = []
    
    for dataset in datasets:
        title = dataset.title
        url = f"https://www.kaggle.com/datasets/{dataset.ref}"
        description = dataset.subtitle.replace("\n", " ").strip() if dataset.subtitle else ""
        
        results.append({
            "title": title,
            "url": url,
            "snippet": description,
            "source": "kaggle"
        })
    
    return results

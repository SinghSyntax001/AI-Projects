from typing import List, Dict
from huggingface_hub import list_datasets

def hf_search(keywords: List[str], limit: int = 20) -> List[Dict]:
    results = []
    for keyword in keywords:
        datasets = list_datasets(search=keyword, limit=limit)
        for dataset in datasets:
            description = ""
            title = dataset.id
            if dataset.cardData:
                title = dataset.cardData.get("pretty_name", dataset.id)
                description = dataset.cardData.get("description", "").replace("\n", " ").strip()
            
            results.append({
                "title": title,
                "url": f"https://huggingface.co/datasets/{dataset.id}",
                "snippet": description,
                "source": "huggingface"
            })
    return results



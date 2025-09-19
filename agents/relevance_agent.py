from sentence_transformers import SentenceTransformer, util

class RelevanceAgent:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def evaluate(self, user_query: str, metadata: dict) -> dict:
        title = metadata.get("title", "")
        description = metadata.get("description", "")
        dataset_text = f"{title}. {description}"

        query_emb = self.model.encode(user_query, convert_to_tensor=True)
        dataset_emb = self.model.encode(dataset_text, convert_to_tensor=True)

        score = util.cos_sim(query_emb, dataset_emb).item()
        relevance_score = round((score + 1) / 2, 3)

        if relevance_score > 0.7:
            reason = "Strong match between query and dataset."
        elif relevance_score > 0.4:
            reason = "Partial match; dataset may be useful."
        else:
            reason = "Weak match; likely not suitable."

        return {
            "relevance_score": relevance_score,
            "reason": reason
        }



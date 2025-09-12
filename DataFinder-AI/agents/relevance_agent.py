from sentence_transformers import SentenceTransformer, util

class RelevanceAgent:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def evaluate(self, user_query:str, metadata:dict) -> dict:
        """
        Evaluate the relevance of a dataset based on user query and metadata.
        Returns a dictionary with relevance score(0-1) and reason.
        """

        title = metadata.get("title", "")
        description = metadata.get("description", "")


        cosine_score = 0.0
        
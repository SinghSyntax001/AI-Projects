from itertools import product


def build_queries(plan):
    base = [
            "dataset", "open data", "public dataset", "benchmark", "download"
        ]
    sites = ["site:huggingface.co", "site:kaggle.com", "site:data.gov", "site:data.europa.eu"]
    kws = plan.keywords[:8]
    simple = [" ".join([kw, b]) for kw in kws for b in base]
    boolean = [f'("{kw}") AND (dataset OR benchmark)' for kw in kws]
    siteq = [f"{kw} {s}" for kw, s in product(kws, sites)]
    return simple + boolean + siteq

import streamlit as st
from main import run_pipeline

st.title("📊 DataFinder-AI")
st.subheader("Find the most relevant datasets for your ML problem")

query = st.text_area("Enter problem statement or abstract")

if st.button("Search Datasets"):
    if query.strip():
        with st.spinner("🔎 Searching datasets..."):
            results = run_pipeline(query, top_k=5)

        for r in results:
            st.markdown(f"### [{r['title']}]({r['url']})")
            st.write(f"**Relevance Score:** {r['relevance_score']}")
            st.write(r["description"])
            st.caption(f"Source: {r['source']}")
            st.markdown("---")
    else:
        st.warning("Please enter a query first.")

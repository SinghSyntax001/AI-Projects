
-----

## 📊 DataFinder.AI - Dataset Discovery Agent

### Features

  * **🔍 Multi-Source Search**: Scans for relevant datasets across Hugging Face, Kaggle, and DuckDuckGo.
  * **📄 Intelligent Scraping**: Scrapes dataset pages to extract key metadata, including title, description, and source.
  * **🧠 Two-Layer Evaluation**:
      * **Relevance Agent**: Uses a `SentenceTransformer` model to calculate a **relevance score** based on the similarity between the user query and the dataset's text.
      * **LLM Evaluator**: An optional LLM-based agent provides a **robustness score** and a detailed reason for each dataset, analyzing its suitability for an ML problem.
  * **💻 Command-Line Interface (CLI)**: Run the agent directly from your terminal.
  * **🌐 Streamlit UI**: A web-based interface for easy interaction and result viewing.

### Installation

1.  Navigate to the project directory.
    ```bash
    cd DataFinder-AI
    ```
2.  Install the required dependencies.
    ```bash
    pip install -r requirements.txt
    ```
3.  Set up your API key. Create a `.env` file in the `DataFinder-AI` directory and add your Groq API key:
    ```
    GROQ_API_KEY=your_groq_api_key_here
    ```

### Usage

This project can be run in two ways.

#### CLI

Run the main script and provide a query when prompted.

```bash
python main.py
```

#### Streamlit Web App

Launch the web interface using Streamlit.

```bash
streamlit run ui/app.py
```

The app will open in your browser, where you can enter your query.

-----

## 🤝 Contributing

Contributions are welcome\! If you have suggestions for improvement or find any issues, please feel free to open a pull request or an issue on the repository.

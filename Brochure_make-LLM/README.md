
# 🏢 AI-Powered Company Brochure Generator

Generate a **humorous, engaging, and professional company brochure** for clients, investors, or potential recruits — directly from a company’s website.

This project scrapes website content, identifies relevant links (About, Careers, Blog, etc.), and uses an **LLM (via Groq API)** to generate a **Markdown brochure** you can share or save.

---

## 🚀 Features

* 🌐 **Website Scraping**: Extracts landing page text and relevant links from company websites.
* 🤖 **LLM Integration**: Uses **Groq API** + `llama-3.1-8b-instant` to summarize company culture, careers, and offerings.
* 📑 **Automatic Link Filtering**: Identifies only relevant links (About, Careers, Blog, Docs, etc.).
* 🎭 **Engaging Style**: Brochures are generated with a humorous, investor- and recruit-friendly tone.
* 💾 **File Export**: Save brochures as `.md` or `.txt`.
* 🔧 **Modular Codebase**: Easy to extend or adapt for business use cases.

---

## 📂 Project Structure

```
sales_brochure/
│── base_agent.py          # LLM wrapper for Groq API
│── website_scrapper.py    # Scraper & link selector
│── brochure_creator.py    # Builds and saves brochure
│── config.py              # Loads API key and model config
│── main.py                # Entry point for running the pipeline
│── requirements.txt       # Project dependencies
│── README.md              # Project documentation
```

---

## ⚙️ Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/sales_brochure.git
cd sales_brochure
```

2. **Set up a virtual environment (recommended)**

```bash
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
   Create a `.env` file in the project root with:

```
GROQ_API_KEY=your_groq_api_key_here
```

---

## ▶️ Usage

Run the main script with a company URL:

```bash
python main.py
```

Example output:

```json
{
  "links": [
    {"type": "about page", "url": "https://huggingface.co/brand"},
    {"type": "careers page", "url": "https://apply.workable.com/huggingface/"}
  ]
}
```

Brochure will be generated and saved as:

```
brochure.md
```

---

## 🧩 Example: HuggingFace

Generated brochure snippet:

```markdown
# Welcome to HuggingFace 🚀
Where transformers aren’t just robots — they’re the future of AI!  

We power models, datasets, and spaces. Our careers page is full of exciting opportunities for humans who love working with machines.
```

---

## 💼 Business Applications

* 📣 Marketing teams: Quickly build creative brochures for outreach.
* 💰 Investors: Get quick summaries of target companies.
* 👩‍💻 Recruiters: Showcase culture & career opportunities in an engaging way.
* 🤝 Sales teams: Auto-generate company intro docs for pitches.

---

## 🛠️ Tech Stack

* **Python 3.9+**
* **BeautifulSoup4** – Web scraping
* **Requests** – HTTP requests
* **Groq API** – LLM completions
* **Markdown** – Output formatting

---

## 🤝 Contributing

Contributions are welcome! Please fork the repo and submit a pull request.


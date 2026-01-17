# Canadian Government AI Policy and Guidelines Explorer

A Streamlit-based application that summarizes and explores AI-related policies, frameworks, directives, and governance guidance across Canadian federal, provincial, and territorial governments.

The app is designed to help public-sector organizations, researchers, consultants, and policy professionals understand how AI is being governed in Canada, using a curated corpus of official government sources and AI-assisted synthesis.

🔗 **Live app:**  
https://canadian-ai-policy-explorer.streamlit.app

---

## Overview

The Canadian Government AI Policy and Guidelines Explorer allows users to:

- Ask questions about AI policy and governance for a single government
- Compare AI approaches across two governments/jurisdictions
- View a Canada-wide overview of AI governance trends
- Review all official source documents used by the app

All summaries are generated on demand using OpenAI models, grounded strictly in publicly available, authoritative government material.

---

## Key Features

- 🇨🇦 Coverage of the Canadian federal government and 13 provincial and territorial governments
- 📚 Manually curated corpus of official policy, directive, and guidance documents
- 🔍 Question-driven exploration (no free web crawling)
- ⚖️ Guardrails to ensure Canadian government-only scope
- 🧠 AI-assisted synthesis with transparency on limitations
- 📱 Responsive design for desktop and mobile

---

## Data Sources & Methodology

- Source URLs are manually curated and reviewed
- Only official government, regulatory, or legislative bodies are included
- The app does not dynamically crawl the web or discover new sources
- Content is fetched and parsed at runtime using:
  - `requests` + `BeautifulSoup` for HTML
  - `pdfplumber` for PDFs
- Retrieved text is cleaned to remove navigation, banners, and unrelated content

This approach prioritizes accuracy, traceability, and policy relevance over breadth.

---

## Technology Stack

- **Frontend / App framework:** Streamlit
- **Language:** Python
- **AI models:** OpenAI (via API)
- **Text extraction:** BeautifulSoup, pdfplumber
- **Deployment:** Streamlit Community Cloud
- **Source control:** GitHub

---

## Limitations & Intended Use

This application is a research and decision‑support tool. It does not provide legal advice. Its purpose is to help organizations and the general public stay informed about evolving government AI policies, regulations, and guidance in a rapidly changing landscape.

- Summaries may omit nuance present in full policy documents
- Interpretations reflect synthesized patterns, not official positions
- Users should always consult original source documents for formal compliance or legal interpretation

---

## Contributing

Contributions, suggestions, and improvements are welcome — particularly in the areas of:

- Source coverage (new official documents or authoritative government URLs)
- User interface and user experience (UI/UX) improvements
- Performance and reliability enhancements
- Comparative analysis features
- Documentation and clarity improvements

To maintain the integrity of the curated corpus:

- Please open an issue first to discuss proposed changes
- Pull requests should be well-documented, scoped, and aligned with the project's research goals
- Automated or large-scale web crawling is intentionally out of scope

---

## Roadmap (Indicative)

Future enhancements may include:

- Structured comparison tables
- Source classification and tagging
- Exportable summaries
- Usage analytics and trends
- Improved document refresh workflows
- Corpus storage/snapshotting and change tracking to support longitudinal analysis of evolving AI policy positions across Canadian governments and jurisdictions

---

## About

Developed by **Plumstead-White Analytics (PWA)** as part of ongoing work in AI governance, data strategy, and responsible AI advisory services.

For questions, feedback, or collaboration inquiries, please open an issue or contact the maintainers via GitHub.

---

## License

This project is provided for informational and research purposes.  
License details to be finalized.

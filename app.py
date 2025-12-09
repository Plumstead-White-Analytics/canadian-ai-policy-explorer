# canadian-ai-policy_explorer.py 

import os
import requests
import pdfplumber
from bs4 import BeautifulSoup
from openai import OpenAI
import streamlit as st
from datetime import datetime

# ---- Helper function for Streamlit User Interface (UI) for single goverment response ----
def set_single_question(q: str):
    st.session_state["single_gov_question"] = q

# ---- Helper function for Streamlit UI for goverment comparison ----
def set_compare_question(q: str):
    st.session_state["compare_question_area"] = q

# ---- Helper function for Streamlit UI for Canada-wide overview ----
def set_canada_question(q: str):
    st.session_state["canada_question"] = q

# ---- OpenAI client (uses your OPENAI_API_KEY env var) ----

# ---- Helper function to return to main page (single government mode) ----
def go_home():
    st.session_state["mode"] = "Ask about one government"

client = OpenAI()

# ---- Guardrail Helper ----

import re

# Terms that clearly indicate the question is about Canada
CANADIAN_HINTS = [
    "canada",
    "canadian",
    "federal",
    "province",
    "provincial",
    "territorial",
    "territory",
    # Provinces and territories
    "alberta",
    "british columbia",
    "bc",
    "saskatchewan",
    "manitoba",
    "ontario",
    "quebec",
    "québec",
    "new brunswick",
    "nova scotia",
    "prince edward island",
    "pei",
    "newfoundland",
    "labrador",
    "yukon",
    "northwest territories",
    "nunavut",
]

# Explicitly non-Canadian places to block
NON_CANADIAN_HINTS = [
    "usa", "u.s.a", "united states", "america", "american",
    "us federal", "u.s. federal",
    "uk", "united kingdom", "britain", "england",
    "europe", "european union", "eu",
    "china", "india", "japan", "germany", "france", "mexico",
    "brazil", "australia", "new zealand", "nz",
    "africa", "asia", "russia", "russian",
    "barbados", "cuba", "italy", "italian", "spain", "spanish",
    "singapore", "saudi arabia", "saudi",
    # add more as needed
]

def is_non_canadian_question(question: str) -> bool:
    """
    Return True if the question appears to be explicitly about a
    non-Canadian country or region based on simple keyword matching.

    Generic questions about 'this government' or 'AI policy' are allowed,
    even if they don't explicitly mention Canada.
    """
    q = question.lower()

    # If it clearly references Canada or a province/territory, it's allowed.
    if any(term in q for term in CANADIAN_HINTS):
        return False

    # If it clearly references a non-Canadian place, we block it.
    if any(term in q for term in NON_CANADIAN_HINTS):
        return True

    # Otherwise, we treat the question as in-scope.
    return False

# ---- 1. JURISDICTION SOURCES ----
JURISDICTION_SOURCES = {
    "Federal": [
        "https://www.canada.ca/en/government/system/digital-government/digital-government-innovations/responsible-use-ai.html",
        "https://www.canada.ca/en/government/system/digital-government/digital-government-innovations/responsible-use-ai/guide-use-generative-ai.html",
        "https://www.canada.ca/en/government/system/digital-government/digital-government-innovations/responsible-use-ai/guide-scope-directive-automated-decision-making.html",
        "https://www.canada.ca/en/government/system/digital-government/digital-government-innovations/responsible-use-ai/gc-ai-strategy-overview.html",
        "https://www.canada.ca/en/government/system/digital-government/digital-government-innovations/responsible-use-ai/principles.html",
        "https://open.canada.ca/data/en/dataset/fcbc0200-79ba-4fa4-94a6-00e32facea6b",
        "https://www.canada.ca/en/innovation-science-economic-development/news/2025/09/government-of-canada-launches-ai-strategy-task-force-and-public-engagement-on-the-development-of-the-next-ai-strategy.html",
        # Policy Horizons Canada (foresight & AI futures)
        "https://horizons.service.canada.ca/en/2025/02/10/ai-policy-consideration/index.shtml",
        # Health Canada
        "https://www.canada.ca/en/health-canada/corporate/transparency/health-agreements/pan-canadian-ai-guiding-principles.html",
        # Office of the Privacy Commissioner of Canada
        "https://www.priv.gc.ca/en/privacy-topics/technology/artificial-intelligence/gd_principles_ai/",
        # Canadian Judicial Council
        "https://cjc-ccm.ca/sites/default/files/documents/2024/AI%20Guidelines%20-%20FINAL%20-%202024-09%20-%20EN.pdf",
    ],

    "Ontario": [
        "https://www.ontario.ca/page/ontarios-trustworthy-artificial-intelligence-ai-framework",
        "https://www.ontario.ca/page/responsible-use-artificial-intelligence-directive",
        "https://www.ontario.ca/page/ontario-broader-public-sector-cyber-security-strategy-report",
        "https://www.ipc.on.ca/en/media-centre/blog/artificial-intelligence-public-sector-building-trust-now-and-future",
        "https://www.ontario.ca/page/strengthening-cyber-security-and-building-trust-public-sector",
        "https://www.ontario.ca/page/digital-ontario",
    ],
    "Alberta": [
        "https://www.alberta.ca/technology-and-innovation",
        "https://www.alberta.ca/artificial-intelligence-data-centres-strategy",
        "https://open.alberta.ca/publications/albertas-ai-data-centre-strategy",
        "https://www.alberta.ca/system/files/popa-fact-sheet-ai-automated-systems.pdf",
        "https://www.alberta.ca/lookup/imt-policy-instruments-portal.aspx",
    ],
   "British Columbia": [
        "https://digital.gov.bc.ca/policies-standards/generative-ai-policy",
        "https://digital.gov.bc.ca/ai/draft-responsible-use-principles",
        "https://www2.gov.bc.ca/assets/gov/education/administration/kindergarten-to-grade-12/ai-in-education/considerations-for-using-ai-tools-in-k-12-schools.pdf",
    ],

    "Québec": [
        "https://www.quebec.ca/en/government/policies-orientations/artificial-intelligence",
        "https://www.quebec.ca/en/government/policies-orientations/digital-strategy",
        "https://api.forum-ia.devbeet.com/app/uploads/2020/09/ai-strategy_en-acj-19-juin-v8.pdf?utm_source=chatgpt.com", 
    ],

    "Nova Scotia": [
        "https://www.novascotia.ca/digital-code-practice",
        "https://www.novascotia.ca/government/cyber-security-and-digital-solutions",
    ],

    "New Brunswick": [
        "https://www.gnb.ca/nosearch/digital-numerique/digital_new_brunswick.pdf",
    ],

    "Manitoba": [
        "https://www.gov.mb.ca/asset_library/en/proactive/20252026/innovation-and-prosperity-report.pdf",
        "https://news.gov.mb.ca/news/index.html?item=71303",
        "https://news.gov.mb.ca/news/?item=68018",
    ],

    "Saskatchewan": [
        "https://www.saskatchewan.ca/government/government-data/digital-government",
        "https://taskroom.saskatchewan.ca/services-and-support/information-technology/artificial-intelligence/generative-artificial-intelligence-guidelines",
    ],
   
    "Prince Edward Island": [
        "https://www.princeedwardisland.ca/sites/default/files/ad9e/MD2025-06ENG.pdf",
        "https://www.princeedwardisland.ca/sites/default/files/publications/pei_digital_health_strategy.pdf",
        "https://www.princeedwardisland.ca/sites/default/files/publications/2021_speech_from_the_throne.pdf",
        "https://www.princeedwardisland.ca/sites/default/files/3089/Health_PEI_Strategic_Plan_2025-2028.pdf",
    ],

    "Yukon": [
        "https://yukon.ca/en/education-and-schools/kindergarten-grade-12-curriculum/learn-about-use-artificial-intelligence-ai",

    ],

    "Nunavut":  [
        "https://www.gov.nu.ca/en/culture-language-heritage-and-art/language-preservation-and-promotion-through-technology-ms",
        "https://assembly.nu.ca/sites/default/files/2025-05/OGOPA%20Report%20-%20IPC%202023-2024%20-%20May2025%20-%20English.pdf",
    ],

    "Newfoundland and Labrador":  [
        "https://www.gov.nl.ca/releases/2025/gmsd-en/0723n01/",
        "https://www.gov.nl.ca/releases/2025/ipgs/0507n03/",
        "https://www.gov.nl.ca/releases/2023/oipc/1207n04/",
        "https://www.gov.nl.ca/releases/2025/ipgs/0416n04/",
        "https://www.gov.nl.ca/releases/2022/exec/0708n02/",
    ],

    "Northwest Territories":  [
        "https://bearnet.gov.nt.ca/sites/bearnet/files/2025-05-29_gnwt_guideline_on_use_of_generative_ai_-_signed.pdf",
        "https://www.nwtgeoscience.ca/news/canada-and-northwest-territories-partner-innovative-ai-based-core-scanning-initiative-support",
    ],

}

# Normalize lookups so internal logic can safely use lowercase keys
NORM_KEYS = {k.lower(): k for k in JURISDICTION_SOURCES.keys()}

# ---- 2. FETCH + EXTRACT TEXT ----

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-CA,en;q=0.9",
}

def fetch_text_from_url(url: str) -> str:
    """Download a URL and extract readable text from HTML or PDF."""
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=20)
    except Exception as e:
        print(f"[fetch_text_from_url] Error fetching {url}: {e}")
        return ""

    if resp.status_code != 200:
        print(f"[fetch_text_from_url] {url} returned HTTP {resp.status_code}")
        return ""

    content_type = resp.headers.get("Content-Type", "").lower()

    # PDF handling
    if "pdf" in content_type or url.lower().endswith(".pdf"):
        tmp_path = "tmp_policy.pdf"
        with open(tmp_path, "wb") as f:
            f.write(resp.content)

        pages_text = []
        
        try:
           with pdfplumber.open(tmp_path) as pdf:
               for page in pdf.pages:
                   t = page.extract_text() or ""
                   if t.strip():
                       pages_text.append(t)
        except Exception as e:
            print(f"[fetch_text_from_url] Error reading PDF {url}: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

        if not pages_text:
            print(f"[fetch_text_from_url] No text extracted from PDF {url}")

        return "\n".join(pages_text)

    # HTML handling
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()

    text_chunks = []
    for tag in soup.find_all(["p", "li"]):
        t = tag.get_text(" ", strip=True)
        if t:
            text_chunks.append(t)

    if not text_chunks:
        print(f"[fetch_text_from_url] No <p>/<li> text extracted from {url}")

    return "\n".join(text_chunks)

# ---- 3. CORPUS BUILDER (with normalization + caching) ----

# Cache so we only fetch each jurisdiction once per run
_jurisdiction_corpus_cache: dict[str, str] = {}

def get_jurisdiction_corpus(jurisdiction: str) -> str:
    """
    Build or return a cached text corpus for a given jurisdiction.

    - Accepts any capitalization (e.g., 'federal', 'Federal', 'FEDERAL').
    - Uses NORM_KEYS to map to the canonical key in JURISDICTION_SOURCES.
    - Returns an empty string for "thin" jurisdictions with no URLs configured.
    """
    if not jurisdiction:
        raise ValueError("Jurisdiction name is required.")

    # Normalize to canonical key (e.g., 'federal' -> 'Federal')
    canonical = NORM_KEYS.get(jurisdiction.lower())
    if canonical is None:
        raise ValueError(f"Unknown jurisdiction: {jurisdiction!r}")

    # Return from cache if available
    if canonical in _jurisdiction_corpus_cache:
        return _jurisdiction_corpus_cache[canonical]

    urls = JURISDICTION_SOURCES.get(canonical, [])
    # Thin jurisdictions: no URLs yet -> empty corpus (handled by callers)
    if not urls:
        _jurisdiction_corpus_cache[canonical] = ""
        return ""

    print(f"Building corpus for jurisdiction: {canonical}")
    pieces: list[str] = []

    for url in urls:
        try:
            text = fetch_text_from_url(url)
            if text:
                pieces.append(text)
        except Exception as e:
            print(f"  !! Error fetching {url}: {e}")

    corpus = "\n\n".join(pieces)
    _jurisdiction_corpus_cache[canonical] = corpus
    print(f"{len(corpus)} characters of text in the {canonical} corpus")
    return corpus

# ---- 4. SINGLE-JURISDICTION ANSWER ----
def answer_ai_policy_question(jurisdiction: str, question: str) -> str:
    """
    Use OpenAI to answer a question about AI policy for a given jurisdiction.
    Includes a 'What this means in practice' section.
    """

    # Normalize jurisdiction name (e.g., 'federal' → 'Federal')
    canonical = NORM_KEYS.get(jurisdiction.lower())
    if canonical is None:
        return f"⚠️ Unknown jurisdiction: {jurisdiction}"

    # ----GUARDRAIL: BLOCK NON-CANADIAN QUESTIONS ----
    if is_non_canadian_question(question):
        return (
            "This tool only covers AI policies and guidelines for Canadian governments "
            "(federal, provincial, and territorial). It cannot summarize AI policies "
            "for other countries or regions. Please ask about a Canadian government instead."
        )

    # Fetch or build the corpus
    corpus = get_jurisdiction_corpus(canonical)
    urls = JURISDICTION_SOURCES.get(canonical, [])

    # Case 1: thin jurisdiction (no URLs configured)
    if not urls:
        return (
        f"### AI Policy for {canonical}\n\n"
        "At this time, no official AI policy documents, directives, or frameworks "
        "were available for the app and this jurisdiction. "
        "As a result, only general high-level guidance can be provided.\n\n"
        f"**Your question:** {question}\n\n"
        "You may wish to consult:\n"
        "- The jurisdiction’s central government website\n"
        "- Digital strategy pages\n"
        "- Public service modernization or technology governance pages\n"
        "- Provincial or territorial legislation websites\n"
        )

    # Case 2: URLs exist, but corpus is empty → fetch / parsing failure
    if not corpus.strip():
        return (
        f"### AI Policy for {canonical}\n\n"
        "This app has configured official websites for this jurisdiction, "
        "but could not retrieve or parse any text from them just now.\n\n"
        "This is usually due to one of the following:\n"
        "- Temporary network issues or timeouts\n"
        "- The sites blocking automated requests\n"
        "- A change in page structure that prevents text extraction\n\n"
        "Please try again later, or consult the official sites directly:\n"
        + "\n".join(f"- {u}" for u in urls)
        )

    # Case 3: Corpus exists but is too small / not substantial enough
    if len(corpus) < 1500:   # adjust this threshold as needed
        return (
        f"### Limited AI Policy Information for {canonical}\n\n"
        "The curated sources for this jurisdiction currently contain only limited "
        "public material related to AI, and no formal AI policy, directive, or "
        "public-sector AI governance framework appears to be available.\n\n"
        "The available link(s) reviewed were:\n"
        + "\n".join(f"- {u}" for u in urls)
        + "\n\nAs more AI governance material becomes available from this jurisdiction, "
        "it will be incorporated into future summaries.\n"
        )
     
    # Limit token load for GPT
    max_chars = 16000
    trimmed_corpus = corpus[:max_chars]

    system_prompt = (
        "You are an expert assistant that summarizes and explains Canadian government "
        "AI policies, directives, and frameworks in plain, non-legal language.\n"
        "You do NOT provide legal advice. You focus on high-level practical implications "
        "for public servants, decision-makers, and the public."
    )

    user_prompt = f"""
The user is asking about AI policy for the **{canonical}** government in Canada.

**User question:**  
{question}

Below are excerpts from official policy/framework pages for this jurisdiction:
\"\"\"{trimmed_corpus}\"\"\"

Below are excerpts from official policy/framework pages for this jurisdiction:
\"\"\"{trimmed_corpus}\"\"\"

### Instructions for your answer:
- Begin with 2–4 short paragraphs that provide a clear, professional narrative response to the user’s question.
- Explain the government’s AI-related policies, directives, frameworks, or guidance, and describe what they mean in practice for:
  (a) public-sector organizations, and 
  (b) external organizations wishing to align with this government’s approach to responsible AI.
- Base all statements strictly on the excerpts provided. If the corpus does not address something the user asked about, state this clearly instead of guessing.
- After the narrative, include a section titled **"Key points"** with 3–6 bullet points summarizing the most important ideas.
- Include a section titled **"What this means in practice"** with one short paragraph and optional bullet points describing practical implications (e.g., transparency expectations, risk assessment duties, procurement considerations, disclosure rules).
- End with a section titled **"Where to read more"** listing the main policies, directives, or strategy documents referenced (use bullet points).
"""
   
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content

# ---- 5. TWO-GOVERNMENT COMPARISON (normalized + thin-aware) ----
def compare_jurisdictions(j1: str, j2: str, question: str | None = None) -> str:
    """
    Compare AI policies between two governments (e.g., 'Federal' vs 'Ontario').
    Returns a structured comparison grounded in the corpus for both.

    - Uses NORM_KEYS to normalize names.
    - If either government has no corpus, returns a helpful explanation instead
      of calling the model with empty context.
    """
    if not j1 or not j2:
        return "Please select two governments before running a comparison."

    if j1.lower() == j2.lower():
        return "Please choose two different governments to compare."

    # Guardrail: block comparisons about non-Canadian governments/regions
    if question and is_non_canadian_question(question):
        return (
            "This comparison tool only covers AI policies and guidelines for Canadian governments "
            "(federal, provincial, and territorial). It cannot compare AI policies for other "
            "countries or regions. Please ask about Canadian governments instead."
        )

    c1 = NORM_KEYS.get(j1.lower())
    c2 = NORM_KEYS.get(j2.lower())

    if c1 is None or c2 is None:
        return "One or both of the selected governments aren’t recognized in this app."

    corpus1 = get_jurisdiction_corpus(c1)
    corpus2 = get_jurisdiction_corpus(c2)

    # Handle thin or missing corpora
    missing = []
    if not corpus1.strip():
        missing.append(c1)
    if not corpus2.strip():
        missing.append(c2)

    if missing:
        if len(missing) == 2:
            return f"""
I don’t yet have detailed AI policy sources configured for **{c1}** or **{c2}**, so I can’t provide a grounded comparison.

You can still:
- Explore the **Federal** government or other provinces with richer corpora.
- Check the official websites for **{c1}** and **{c2}** for the most up-to-date AI, digital, or data strategies.
""".strip()
        else:
            missing_name = missing[0]
            present_name = c1 if missing_name == c2 else c2
            return f"""
I have detailed AI policy sources configured for **{present_name}**, but not yet for **{missing_name}**.

What this means in practice:
- I can’t provide a balanced, grounded comparison between **{present_name}** and **{missing_name}**.
- You can still ask single-government questions about **{present_name}**.
- For **{missing_name}**, please refer to its official government website for AI policy or digital strategy updates.
""".strip()

    # Trim (to avoid token overload)
    max_chars = 12000
    corpus1_trim = corpus1[:max_chars]
    corpus2_trim = corpus2[:max_chars]

    j1_label = c1
    j2_label = c2

    system_prompt = (
        "You are an expert assistant in Canadian public-sector AI governance. "
        "Compare and contrast AI policies from multiple governments based ONLY "
        "on the provided excerpts. Do not invent information."
    )

    if question is None:
        question = (
            f"How do {j1_label} and {j2_label} differ in their AI policies, "
            f"and what does this mean in practice for organizations operating in both?"
        )

    user_prompt = f"""
The user is asking for a comparison of AI policies between:

1. {j1_label}
2. {j2_label}

User question:
{question}

Below are excerpts from each government's official AI-related policy pages.

--- BEGIN {j1_label.upper()} EXCERPTS ---
{corpus1_trim}
--- END {j1_label.upper()} EXCERPTS ---

--- BEGIN {j2_label.upper()} EXCERPTS ---
{corpus2_trim}
--- END {j2_label.upper()} EXCERPTS ---

Instructions:
- Start with 2–4 short paragraphs that provide a clear, professional narrative comparison of how {j1_label} and {j2_label} approach AI policy and responsible AI, directly addressing the user’s question.
- Explain both similarities and differences in terms of what they mean for:
  (a) public-sector organizations within each jurisdiction, and
  (b) external organizations (e.g., vendors, partners, nonprofits) that operate across or interact with both governments.
- Reference the actual policy instruments by name where possible, and distinguish mandatory directives, legislation, or binding policy instruments from guidance, frameworks, or strategy documents.
- After the narrative, include a section titled **"Where the policies appear aligned"** that starts with a short paragraph followed by bullet points summarizing the main areas of alignment.
- Include a section titled **"Where the policies diverge"** that starts with a short paragraph followed by bullet points summarizing the key differences.
- Include a section titled **"Implications for organizations operating in more than one jurisdiction or across Canada"** with one short paragraph plus bullet points highlighting practical implications (e.g., compliance, transparency expectations, procurement and vendor requirements, risk management).
- If the text does not explicitly address something the user asked about, say so clearly rather than guessing.
"""
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content

# ---- CANADA-WIDE ANSWER (Updated and Consistent) ----
def answer_canada_wide(question: str) -> str:
    """
    Generate a Canada-wide overview by merging federal + all provincial/territorial corpora.
    Includes a 'What this means in practice' section and 'Where to read more'.
    """

# Guardrail: ensure the question is actually about Canada / Canadian AI governance
    if is_non_canadian_question(question):
        return (
            "This Canada-wide overview only covers AI policies and guidelines for Canadian governments "
            "(federal, provincial, and territorial). It cannot summarize AI policies for other countries "
            "or regions. Please ask a question about AI governance in Canada."
        )
    
# Collect corpora from all jurisdictions that have content
    corpora = []
    sources_used = []

    for j in JURISDICTION_SOURCES.keys():
        canonical = j  # already capitalized in our updated list
        corpus = get_jurisdiction_corpus(canonical)

        if corpus.strip():
            corpora.append(f"### {canonical}\n{corpus}\n")
            sources_used.append(canonical)

    # If for some reason everything failed
    if not corpora:
        return (
            "### Canada-Wide AI Overview\n\n"
            "At this time, the system could not retrieve any AI policy documents from the "
            "curated federal, provincial, or territorial sources. Please try again later."
        )

    # Combine and limit for GPT
    full_text = "\n\n".join(corpora)
    max_chars = 16000
    trimmed = full_text[:max_chars]

    system_prompt = (
        "You are an expert assistant that summarizes and explains Canadian AI policy, directives, "
        "frameworks, and guidelines in plain, non-legal language. You synthesize trends across federal, "
        "provincial, and territorial governments.\n\n"
        "You do NOT provide legal advice or definitive legal interpretations. You focus on high-level "
        "practical implications for public servants, technology teams, leaders, and the public. You must "
        "base your answers ONLY on the policy excerpts provided.\n\n"
        "If the question is not about Canadian public-sector AI policy, or the answer is not supported "
        "by excerpts, you must say so clearly instead of guessing.\n\n"
        "If a user asks for harmful, adversarial, or off-topic content, explain that this tool is only "
        "for understanding official Canadian government AI policies."
    )

    user_prompt = f"""
The user is asking a Canada-wide question about public-sector AI policy.

**User question:**  
{question}

Below are excerpts from curated federal, provincial, and territorial AI policy or digital-governance sources:
\"\"\"{trimmed}\"\"\"

### Instructions for your answer:
- First, write 2–4 short paragraphs giving a Canada-wide narrative overview of public-sector AI policy and responsible AI expectations, directly addressing the user’s question.
- Describe major themes shared across governments (e.g., transparency, privacy, fairness, accountability, risk mitigation) and highlight meaningful differences (for example, federal mandatory directives or stronger requirements in certain provinces).
- Explain what these patterns mean in practice for:
  (a) public-sector organizations within individual jurisdictions, and 
  (b) other organizations (e.g., vendors, partners, nonprofits) that operate across multiple jurisdictions in Canada.
- After the narrative, add a brief section titled **"Key Canada-wide themes"** with 3–7 bullet points summarizing the main cross-jurisdictional ideas.
- Include a section titled **"What this means in practice (Canada-wide)"** with one short paragraph and bullet points describing concrete implications for organizations (such as transparency expectations, disclosure practices, procurement and vendor requirements, and AI risk-management approaches).
- End with a section titled **"Where to read more"** listing, in bullet points, the main jurisdictions and/or types of documents you are drawing on (e.g., federal directives, provincial strategies).
- Do NOT guess about jurisdictions that have no corpus content — acknowledge any gaps clearly if they are relevant to the question.
"""
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content

# ---- 7. STREAMLIT UI ----
st.set_page_config(
    page_title="Canadian Government AI Policy Explorer",
    layout="wide",
)

# ---- Global CSS for note sections ----
st.markdown(
    """
    <style>
    .notes-block {
        font-size: 0.85rem;      /* slighlty smaller base size */
        max-width: 900px;
    }

    .notes-block p {
        font-size: 0.85rem;
        line-height: 1.4;
        margin-bottom: 0.35rem;  /* tighter spacing */
    }

    .notes-block h3 {
        font-size: 1.0rem;      /* smaller than default h3 */
        margin-top: 0.9rem;
        margin-bottom: 0.25rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
mode_options = [
    "Ask about one government",
    "Compare two governments",
    "Canada-wide overview",
    "Information sources",
]

# Initialize mode once (before the radio is created)
if "mode" not in st.session_state:
    st.session_state["mode"] = mode_options[0]  # "Ask about one government"

# Sidebar radio controls the mode via session_state["mode"]
mode = st.sidebar.radio(
    "Mode",
    mode_options,
    key="mode",   
)

# Show the main titles only for the 3 analysis modes
if mode != "Information sources":
    st.title("Canadian Government AI Policy and Guidelines Explorer")

    # Short static intro line (optional – keep or tweak as required)
    st.markdown(
        "Explore how federal, provincial, and territorial governments are shaping AI in Canada through "
        "policies, frameworks, guidelines, and governance."
    )

    # Collapsible "About this app" section
    with st.expander("About this app", expanded=False):
        st.markdown(
            """
This tool provides clear, accessible summaries of AI-related policies, directives, guidelines, 
and governance practices across Canadian federal, provincial, and territorial governments.

By distilling information from multiple official sources, it helps save research and analysis time, and supports open 
information-sharing in a rapidly evolving AI landscape. Summaries are synthesized using AI from 
a curated corpus of government and oversight materials, helping public-sector professionals, 
researchers, and organizations quickly understand responsible AI use and expectations across Canada.
            """
        )

# --- Custom jurisdiction ordering: Provinces alphabetized, territories at bottom ---
provinces = [
    "Alberta",
    "British Columbia",
    "Manitoba",
    "New Brunswick",
    "Newfoundland and Labrador",
    "Nova Scotia",
    "Ontario",
    "Prince Edward Island",
    "Québec",
    "Saskatchewan",
]

territories = [
    "Northwest Territories",
    "Nunavut",
    "Yukon",
]

# Final ordered list used for dropdowns everywhere
jurisdiction_keys = (
    ["Federal"] +
    sorted(provinces) +
    sorted(territories)
)

# -----------------------------
# MODE: Ask about one government
# -----------------------------
if mode == "Ask about one government":
    st.header("Explore AI policies, frameworks and governance in Canada at the federal, provincial, or territorial level")

    # --- Government selector with no double entry ---
    j = st.selectbox(
        "Choose a government (federal, provincial, or territorial):",
        jurisdiction_keys,
        index=None,                         # nothing pre-selected
        placeholder="Select a government",  # shows inside the box
        key="single_gov_select",
    )

    # Safe government label before user selection
    gov_label = j or "selected"

    default_question = (
        "Provide an overview of current AI policies, directives, and guidance for the "
        f"{gov_label} government, and what they mean in practice for public-sector organizations "
        "and others wishing to align with this government’s approach to responsible AI."
    )

    # --- Question input box ---
    question = st.text_area(
        "Your question:",
        placeholder="Enter your question about this government's AI policies, or choose one of the examples below.",
        height=120,
        key="single_gov_question",
    )

    st.markdown("### Try an example question:")

    example_questions = [
        "What AI policies, directives, or frameworks currently apply to this provincial or territorial government?",
        "How does this government expect public-sector organizations to use AI responsibly?",
        "What should my organization know to align our responsible AI practices with this government’s AI expectations?",
        "What transparency, accountability, or disclosure requirements does this government set for AI use?",
        default_question,
    ]

    cols = st.columns(2)
    for i, q in enumerate(example_questions):
        cols[i % 2].button(
            q,
            key=f"example_single_q_{i}",
            on_click=set_single_question,
            args=(q,),
        )

    # --- Get single-government answer button ---
    if st.button("Get answer", type="primary", key="single_gov_button"):

        # 1. Validate that a government is selected
        if j is None:
            st.warning("Please select a government before asking your question.")
            st.stop()

        # 2. Validate that a question is entered
        if not question or not question.strip():
            st.warning("Please enter a question, or click one of the example questions above.")
            st.stop()

        # 3. Visually separate inputs from the answer area
        st.markdown("<hr style='border: 1px solid #bbb;'>", unsafe_allow_html=True)

        # 4. Generate the answer
        try:
            with st.spinner("Analyzing policy corpus and generating answer..."):
                answer = answer_ai_policy_question(j, question.strip())
            st.markdown(answer)
        except Exception as e:
            st.error(f"Error generating answer: {e}")

    # ---------- Notes block (collapsible) ----------
    st.markdown(
        "<hr style='margin-top: 2rem; margin-bottom: 0.5rem; "
        "border: 0; border-top: 1px solid #ddd;'>",
        unsafe_allow_html=True,
    )

    with st.expander("Notes about this tool (scope, sources, and limitations)", expanded=False):
        st.markdown(
            """
            <div class="notes-block">
            ### 🔍 Scope
            This tool summarizes **AI-related policies, frameworks, guidelines, and governance practices**
            for **Canadian governments only** (federal, provincial, and territorial).  
            It does not summarize policies for other countries or international organizations.

            ### 📘 Source material
            Summaries are based solely on **official government documents** and
            **government-related publications** that have been manually curated for each jurisdiction.
            See "Information sources" for more detail.

            ### ⚠️ Not legal advice
            This tool provides **general informational summaries** only.
            It should **not** be interpreted as legal, regulatory, or compliance advice.
            Always consult the original source documents for authoritative guidance.

            ### 📉 Evolving landscape
            AI governance in Canada is **rapidly developing**.  
            While sources are reviewed regularly, the tool may not reflect the
            **most recent policy changes** or updates issued after the last corpus refresh.

            ### 😊 About the summaries
            Responses are generated by an AI model using the curated corpus.
            They model aims to provide clear and accessible explanations, but may simplify complex policy language.
            For formal decisions or detailed analysis, refer directly to the underlying government documents.
            </div>
            """,
            unsafe_allow_html=True,
        )

# -------------------------
# FOOTER - Main Page Only
# -------------------------
if mode == "Ask about one government":

    st.markdown(
        """
        <div style="
            max-width: 750px;
            margin: 3rem auto 2rem auto;
            padding: 1.2rem 1.6rem;
            color: #555;
            font-size: 0.85rem;
            line-height: 1.45;
            border-top: 1px solid #ddd;
        ">

        <div style="font-weight: 700; text-decoration: underline; margin-bottom: 0.6rem;">
            App Development
        </div>

        <p>
        <strong>Technology stack:</strong>  
        This app was developed using <strong>Python</strong> and <strong>Streamlit</strong>,  
        with <strong>OpenAI’s GPT-5.1</strong> supporting the build process and  
        <strong>GPT-4.1 mini</strong> powering the app and real-time responses  
        (via paid API subscriptions).  
        The development environment includes the <strong>Anaconda </strong> platform and  
        <strong>Jupyter Notebook</strong> for testing and to ensure stability and reliability.
        </p>

        <p>
        <strong>Developers:</strong>  
        Plumstead-White Analytics  
        &nbsp;|&nbsp;  
        <a href="https://www.plumstead-whiteanalytics.ca/" target="_blank">
            www.plumstead-whiteanalytics.ca
        </a>
        </p>

        </div>
        """,
        unsafe_allow_html=True
    )

# -----------------------------
# MODE: Compare two governments
# -----------------------------
elif mode == "Compare two governments":
    st.header("Compare AI policies, frameworks, and governance between governments")

    # --- Government selectors for comparison ---
    col1, col2 = st.columns(2)

    with col1:
        j1 = st.selectbox(
            "First government:",
            jurisdiction_keys,             
            index=None,                    
            placeholder="Select the first government",
            key="compare_j1",
        )

    with col2:
        j2 = st.selectbox(
            "Second government:",
            jurisdiction_keys,
            index=None,
            placeholder="Select the second government",
            key="compare_j2",
        )

    # Safe labels in case neither government is selected yet
    gov1_label = j1 or "first selected"
    gov2_label = j2 or "second selected"

    # Default comparison question (works before or after selection)
    default_compare_q = (
        "How do the AI governance and responsible AI requirements of "
        f"{gov1_label} and {gov2_label} differ, and what do these differences mean "
        "in practice for organizations operating in both jurisdictions?"
        )

    compare_question = st.text_area(
    "Your comparison question:",
    placeholder="Enter your question comparing these two governments, or choose one of the examples below.",
    height=140,
    key="compare_question_area",
        )

    # --- Example comparison questions (click to insert) ---
    st.markdown("### Try an example comparison question:")

    example_compare_questions = [
    "How do these two governments differ in their AI governance and responsible AI requirements for organizations?",
    "Which of these governments has more explicit rules on transparency, disclosure, or accountability for AI use?",
    "How do their AI risk-management practices compare, and what does this mean for organizations operating in both?",
    "Do both governments address generative AI specifically, or do they focus on broader AI systems for public-sector and other organizations?",
    default_compare_q,   
    ]

    cols = st.columns(2)
    for i, q in enumerate(example_compare_questions):
        cols[i % 2].button(
            q,
            key=f"example_compare_q_{i}",
            on_click=set_compare_question,
            args=(q,),
        )

    # --- Run comparison ---
    if st.button("Get answer", type="primary", key="compare_button"):    

        # Validate selections
        if j1 is None or j2 is None:
            st.warning("Please select two governments before running a comparison.")
            st.stop()

        if j1 == j2:
            st.warning("Please choose two different governments to compare.")
            st.stop()

        if not compare_question.strip():
            st.warning("Please enter a comparison question, or click one of the example questions above.")
            st.stop()

        try:
            with st.spinner("Comparing policy corpora and generating analysis..."):
                comparison = compare_jurisdictions(j1, j2, compare_question.strip())
            st.markdown("### 📘 Comparison result")
            st.markdown(comparison)
        except Exception as e:
            st.error(f"Error generating comparison: {e}")

# -----------------------------
# MODE: Canada-wide overview
# -----------------------------
elif mode == "Canada-wide overview":
    st.header("Get a Canada-wide overview of AI policies, frameworks, and governance")

    st.markdown(
        "Ask questions about Canada-wide public-sector AI policy trends across the federal, "
        "provincial, and territorial governments. The answer will synthesize patterns and "
        "differences using only the curated official sources."
    )

    # Default prompt shown as a placeholder only
    default_canada_q = (
        "Provide a Canada-wide overview of current public-sector AI policies, directives, "
        "frameworks, and guidelines, and what they mean in practice for organizations "
        "operating in Canada."
    )

    canada_question = st.text_area(
        "Your question:",
        placeholder="Enter your question on general Canada-wide AI policy or choose one of the examples below.",
        height=140,
        key="canada_question",
    )

    # --- Example Canada-wide questions (click to insert) ---
    st.markdown("### Try an example Canada-wide question:")

    example_canada_questions = [
        "Do most Canadian provincial or territorial governments have formal AI policies, directives, or frameworks in place?",
        "How aligned are provincial and territorial AI approaches with the federal government's responsible AI strategy?",
        "What should an organization operating in multiple provinces know about AI governance across Canada?",
        "Are there common principles that appear across Canadian AI policies, such as transparency, fairness, accountability, or human rights?",
        default_canada_q,
    ]

    cols = st.columns(2)
    for i, q in enumerate(example_canada_questions):
        cols[i % 2].button(
            q,
            key=f"example_canada_q_{i}",
            on_click=set_canada_question,
            args=(q,),
        )

    # --- Get Canada-wide answer button (only runs when clicked) ---
    if st.button("Get answer", type="primary", key="canada_button"):
        if not canada_question.strip():
            st.warning("Please enter a Canada-wide question, or click one of the example questions above.")
        else:
            try:
                with st.spinner("Analyzing federal, provincial, and territorial AI policies..."):
                    answer = answer_canada_wide(canada_question.strip())
                st.markdown(answer)
            except Exception as e:
                st.error(f"Error generating Canada-wide answer: {e}")

# --------------------------
# MODE: Information sources
# --------------------------
elif mode == "Information sources":
    
    # Back to main page button (uses callback)
    st.button("← Back to main page", on_click=go_home)

    # --- Header with popover on the same row ---
    header_col, popover_col = st.columns([6, 2])

    with header_col:
        st.header("Information sources")

    with popover_col:
        with st.popover("ℹ️ How sources are chosen"):
            st.markdown(
                """
This tool prioritizes **official government and government-related documents** on AI policy,
governance, and responsible AI.  

In jurisdictions where formal AI policy is limited, the corpus may also include material from:

- Independent oversight bodies (e.g., Privacy Commissioners, Auditors General)  
- Regulators and judicial governance bodies  
- Government foresight and strategic insight units  
- Official government communications indicating emerging direction

These sources are included only when they are public, authoritative, and materially relevant
to public-sector AI governance. *See the notes at the bottom of this page for additional details.*
                """
            )

    st.markdown("""
    This section provides the **official government sources** that underpin all summaries and
    analyses in this app. Each URL has been **manually selected** from federal, provincial, and
    territorial websites or publications to ensure the information is **accurate, transparent,
    and reliable**.

    The app does **not crawl the internet** or use uncontrolled external content. It relies
    solely on the curated sources listed below.

    The list is updated as governments release new AI-related policies or guidance. Some
    jurisdictions do not yet publish AI policies, but they will be added once available.

    **Source list current as of: December 8, 2025.**

    **Note:** The app automatically summarizes the most recent content available at the URLs below.
    However, the list of sources itself is curated manually, so newly published government
    materials or link changes may not appear until they are added in a future update.
    """)

    st.markdown("---")

    for jurisdiction, urls in JURISDICTION_SOURCES.items():
        with st.expander(jurisdiction):
            if urls:
                st.markdown("**Official sources used for this jurisdiction:**")
                for url in urls:
                    st.markdown(f"- [{url}]({url})")
            else:
                st.info(
                    "No official AI policy or guidance sources are currently configured "
                    "for this jurisdiction yet."
                )

    # --- Notes on Information Sources ---
    st.markdown("---")
    st.subheader("Notes on information sources")

    st.markdown(
        """
        <div class="notes-block">

        This tool aggregates **government and government-related sources** on AI policy, governance,
        and responsible AI practices across Canada.

        Most sources are issued directly by **federal, provincial, or territorial governments**
        (e.g., legislation, directives, strategies, and official policy frameworks).

        To provide a more accurate picture in jurisdictions where formal AI policy is still emerging,
        the corpus may also include AI-related material from:

        🛡️ **Independent officers of the legislature**  
          e.g., Information and Privacy Commissioners, Auditors General, and similar oversight bodies.

        ⚖️ **Regulatory and judicial governance bodies**  
          e.g., Health Canada, the Canadian Judicial Council, and other institutions whose guidance
          materially affects public-sector use of AI.

        🔮 **Government foresight and strategic insight units**  
          e.g., Policy Horizons Canada and similar organizations whose analyses help shape long-term
          AI and digital-governance directions.

        🧩 **Official government communications and initiatives**  
          e.g., technology or language-preservation projects that demonstrate how governments are
          beginning to use AI or related technologies, even where no formal AI framework exists.

        📘 **Reports or guidance documents that reflect intent or emerging direction**  
          Documents that, while not Cabinet or ministry policy, significantly influence how public
          institutions govern or deploy AI systems.

        <div style="margin-top: 1rem;">
        All sources included in the corpus are publicly available and have been manually curated
        to maintain accuracy, relevance, and to avoid speculation.

        If you are aware of other official sources that should be added, or if you notice a link or
        detail that needs correction, we welcome your feedback at
        <a href="mailto:info@plumstead-whiteanalytics.ca">info@plumstead-whiteanalytics.ca</a>.
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )
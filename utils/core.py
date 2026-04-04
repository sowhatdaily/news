APP_TITLE = "Anonimous AI"

PERSONAS = [
    "B-school Student",
    "College Student",
    "Executive / Professional",
    "Founder / Entrepreneur",
    "Investor / Analyst",
    "Consultant / Researcher",
    "Policy / Public Affairs Professional",
    "Other",
]

EXPERIENCE_LEVELS = [
    "Just exploring",
    "0-2 years",
    "3-5 years",
    "6-10 years",
    "10+ years",
]

GEOGRAPHIES = [
    "Global",
    "India",
    "US",
    "Europe",
    "China",
    "Middle East",
    "Southeast Asia",
    "Mixed / Multi-region",
]

OUTPUT_PREFERENCES = [
    "Short summaries",
    "Key points + why it matters",
    "Video-style scripts",
    "Executive briefings",
    "All of the above",
]

SECTOR_OPTIONS = [
    "Technology",
    "AI",
    "Banking/Finance",
    "Consumer & Retail",
    "Industry & Manufacturing",
    "Energy & Utilities",
    "Healthcare",
    "Telecommunications & Media",
    "Real Estate & Infrastructure",
    "Mobility & Transportation",
    "Agriculture",
    "Education",
    "Govt., Policy & Economy",
    "ESG & Sustainability",
    "Entertainment & Lifestyle",
]

SECTOR_SUBINTERESTS = {
    "Technology": [
        "Cloud computing", "SaaS", "Enterprise software", "Cybersecurity",
        "Developer tools", "Data infrastructure", "Semiconductors",
        "Consumer tech", "Hardware devices", "Big Tech", "Startups",
        "Open-source ecosystem", "Digital transformation", "Product management", "IT services",
    ],
    "AI": [
        "Generative AI", "AI agents", "LLMs", "Multimodal AI",
        "Open-source AI models", "AI startups", "AI regulation", "AI safety",
        "India AI", "China AI", "US AI", "GPU economy",
        "Semiconductors for AI", "AI infrastructure / data centers",
        "Robotics + AI", "AI in enterprise", "AI in healthcare",
        "AI in finance", "Computer vision", "Voice AI",
    ],
    "Banking/Finance": [
        "Banking", "NBFCs", "Insurance", "Asset management", "Stock markets",
        "Private equity", "Venture capital", "Fintech", "Payments",
        "Credit markets", "Macroeconomics", "Interest rates",
        "RBI / central bank policy", "Global markets", "Wealth management",
        "Risk management", "IPOs / listings", "Corporate finance", "Financial regulation",
    ],
    "Consumer & Retail": [
        "E-commerce", "FMCG", "D2C brands", "Retail chains", "Quick commerce",
        "Consumer behavior", "Brand strategy", "Luxury retail", "Grocery retail",
        "Fashion retail", "Beauty & personal care", "Marketplaces",
        "Omnichannel commerce", "Pricing and promotions", "Retail supply chain",
    ],
    "Industry & Manufacturing": [
        "Industrial production", "Factory automation", "Smart manufacturing",
        "Supply chains", "Electronics manufacturing", "Auto manufacturing",
        "Heavy industry", "Capital goods", "Industrial robotics",
        "Process engineering", "Quality systems", "Exports", "Industrial policy",
        "Contract manufacturing", "MSME manufacturing",
    ],
    "Energy & Utilities": [
        "Oil and gas", "Renewable energy", "Solar", "Wind", "Battery storage",
        "Power generation", "Power distribution", "Grid infrastructure",
        "EV energy ecosystem", "Nuclear energy", "LNG", "Carbon transition",
        "Utilities regulation", "Energy trading", "Energy security", "Hydrogen economy",
    ],
    "Healthcare": [
        "Hospitals", "Pharma", "Biotech", "Diagnostics", "Medical devices",
        "Health insurance", "Public health", "Healthtech", "Digital health",
        "Genomics", "Drug discovery", "Clinical trials", "Healthcare policy",
        "Preventive care", "Telemedicine", "AI in healthcare",
    ],
    "Telecommunications & Media": [
        "Telecom operators", "5G / 6G", "Network infrastructure", "Broadband",
        "Satellite internet", "OTT platforms", "Digital media", "Advertising",
        "Content platforms", "Streaming wars", "Creator economy", "News media",
        "Sports media rights", "Media regulation", "Audio / podcast ecosystem",
    ],
    "Real Estate & Infrastructure": [
        "Residential real estate", "Commercial real estate", "Warehousing / logistics parks",
        "Construction", "Smart cities", "Roads and highways", "Airports", "Railways",
        "Ports", "Urban infrastructure", "REITs", "Affordable housing",
        "Construction materials", "Infra financing", "Government projects",
    ],
    "Mobility & Transportation": [
        "Electric vehicles", "Automotive", "Autonomous mobility", "Ride-hailing",
        "Public transport", "Logistics", "Freight", "Aviation", "Shipping",
        "Rail transport", "Battery ecosystem", "Mobility startups",
        "Fleet management", "Charging infrastructure", "Last-mile delivery",
    ],
    "Agriculture": [
        "Agritech", "Food supply chains", "Farm policy", "Crop markets",
        "Commodities", "Precision agriculture", "Irrigation", "Fertilizers",
        "Seeds", "Dairy", "Food processing", "Rural economy", "Agri exports",
        "Sustainable farming", "Climate impact on agriculture",
    ],
    "Education": [
        "Edtech", "Higher education", "K-12", "Test prep", "Skill development",
        "Online learning", "Vocational learning", "AI in education",
        "University policy", "Student economy", "Professional education",
        "Upskilling / reskilling", "Learning platforms", "Study abroad", "Education policy",
    ],
    "Govt., Policy & Economy": [
        "Public policy", "Indian economy", "Global economy", "Industrial policy",
        "Trade policy", "Taxation", "Budget / fiscal policy", "Elections and governance",
        "Regulation", "Geopolitics", "Diplomacy", "Defense policy", "Labor policy",
        "Economic reforms", "Inflation / employment",
    ],
    "ESG & Sustainability": [
        "Climate change", "Carbon markets", "Clean energy transition", "ESG investing",
        "Sustainability reporting", "Circular economy", "Waste management",
        "Water management", "Green buildings", "Supply chain sustainability",
        "Climate policy", "Social impact", "Governance standards",
        "Corporate responsibility", "Biodiversity",
    ],
    "Entertainment & Lifestyle": [
        "Films and streaming", "Music industry", "Celebrity business", "Sports business",
        "Gaming", "Fashion", "Luxury lifestyle", "Travel", "Food and hospitality",
        "Wellness", "Creator economy", "Social media culture",
        "Events and festivals", "Beauty", "Pop culture trends",
    ],
}

NEWS_LIBRARY = {
    "Executive / Professional": [
        {"title": "AI copilots in enterprise workflows", "category": "AI", "blurb": "How teams are using AI assistants to reduce repetitive work."},
        {"title": "What leaders should track in a volatile economy", "category": "Govt., Policy & Economy", "blurb": "Rates, demand, cash flow pressure, and execution discipline."},
        {"title": "The new playbook for strategic communication", "category": "Technology", "blurb": "How leaders can communicate clearly during uncertainty."},
    ],
    "Founder / Entrepreneur": [
        {"title": "Finding product-market fit faster", "category": "Technology", "blurb": "Ways founders can learn faster from customer signals."},
        {"title": "AI as a distribution advantage", "category": "AI", "blurb": "How startups can use AI for leverage in sales and operations."},
        {"title": "Unit economics every founder should know", "category": "Banking/Finance", "blurb": "CAC, payback period, retention, and gross margin still matter."},
    ],
    "Investor / Analyst": [
        {"title": "Why market narratives shift faster now", "category": "Banking/Finance", "blurb": "Positioning, rates, AI optimism, and liquidity are reshaping reratings."},
        {"title": "The second-order effects of AI infrastructure spending", "category": "AI", "blurb": "Capital is flowing into chips, data centers, power, and cloud."},
        {"title": "A sector view on energy transition", "category": "Energy & Utilities", "blurb": "How transition themes are changing capex and policy focus."},
    ],
    "Other": [
        {"title": "The fastest-moving stories in business and technology", "category": "Technology", "blurb": "A broad look at shifts in technology, markets, and consumer behavior."},
        {"title": "Why AI is influencing every industry now", "category": "AI", "blurb": "The effects of AI are no longer limited to software companies."},
        {"title": "How macro trends shape daily business news", "category": "Govt., Policy & Economy", "blurb": "Rates, inflation, regulation, and geopolitics sit in the background."},
    ],
}


def split_sentences(text):
    text = (text or "").replace("\n", " ").strip()
    if not text:
        return []
    sentences, current = [], ""
    for ch in text:
        current += ch
        if ch in [".", "!", "?"]:
            candidate = current.strip()
            if len(candidate) > 20:
                sentences.append(candidate)
            current = ""
    if current.strip():
        sentences.append(current.strip())
    return sentences


def persona_angle(persona):
    mapping = {
        "B-school Student": "career growth, learning, and business understanding",
        "College Student": "learning, opportunity discovery, and future career relevance",
        "Executive / Professional": "strategy, execution, and business impact",
        "Founder / Entrepreneur": "opportunity, risk, growth, and product implications",
        "Investor / Analyst": "valuation, market signals, and second-order effects",
        "Consultant / Researcher": "structural shifts and implications across sectors",
        "Policy / Public Affairs Professional": "governance, regulation, and institutional impact",
        "Other": "practical relevance and broader business context",
    }
    return mapping.get(persona, mapping["Other"])


def flatten_user_interests(user_profile):
    onboarding = user_profile.get("onboarding", {})
    sectors = onboarding.get("main_sectors", [])
    sub_interests = onboarding.get("sub_interests", {})
    flat = []
    for sector in sectors:
        flat.append(sector)
        flat.extend(sub_interests.get(sector, []))
    flat.extend(user_profile.get("interests", []))
    seen = set()
    ordered = []
    for item in flat:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def generate_ai_outputs(article_text, user_profile):
    sentences = split_sentences(article_text)
    first_three = sentences[:3] if sentences else [article_text[:200]]

    persona = user_profile.get("persona", "Other")
    geography = user_profile.get("geography", "Global")
    interest_stack = flatten_user_interests(user_profile)
    interest_text = ", ".join(interest_stack[:5]) if interest_stack else "business and world affairs"

    summary = (
        f"In simple terms, this story appears important for someone with a {persona.lower()} profile because it connects to "
        f"{persona_angle(persona)}. The core development is: {first_three[0] if first_three else article_text[:200]} "
        f"This may especially matter across {interest_text}, with relevance to {geography}."
    )

    key_points = [f"Point {i}: {s}" for i, s in enumerate(first_three, start=1)]

    why_it_matters = (
        f"For your profile, the biggest takeaway is how this development could influence {interest_text} through "
        f"changes in market expectations, industry structure, policy direction, or operating priorities."
    )

    video_script = [
        {"scene": 1, "visual": f"Premium opening card with {APP_TITLE} branding", "voiceover": "Here's your smart brief in under a minute."},
        {"scene": 2, "visual": "Breaking-news style headline block", "voiceover": first_three[0] if len(first_three) > 0 else article_text[:140]},
        {"scene": 3, "visual": "Context slide with sector tags and cues", "voiceover": first_three[1] if len(first_three) > 1 else "Here is the context behind the story."},
        {"scene": 4, "visual": "Personal relevance card matched to the reader profile", "voiceover": why_it_matters},
        {"scene": 5, "visual": f"Closing takeaway card with {APP_TITLE} end screen", "voiceover": f"That's your brief from {APP_TITLE}."},
    ]

    storyboard_text = "\n".join(
        [f"Scene {item['scene']}: {item['visual']} | VO: {item['voiceover']}" for item in video_script]
    )

    return {
        "title": first_three[0][:90] if first_three else "Untitled article",
        "summary": summary,
        "key_points": key_points,
        "why_it_matters": why_it_matters,
        "video_script": video_script,
        "storyboard_text": storyboard_text,
    }


def get_personalized_news(user_profile):
    persona = user_profile.get("persona", "Other")
    base_news = NEWS_LIBRARY.get(persona, NEWS_LIBRARY["Other"])
    sectors = set(user_profile.get("onboarding", {}).get("main_sectors", []))

    def score(item):
        return -1 if item["category"] in sectors else 0

    return sorted(base_news, key=score)

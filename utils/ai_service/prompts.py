"""
Centralised prompt templates for all AI/LLM calls.

Import and use these variables throughout the codebase.
To tweak any prompt, edit ONLY this file.
"""

# ─────────────────────────────────────────────────────────────────────────────
# Phase 1 — Article-level structured summary
# ─────────────────────────────────────────────────────────────────────────────

ARTICLE_STRUCTURED_SUMMARY = """\
Article: "{title}"
Source: {source} | Published: {published_date}

Exa AI analysis:
{raw_summary}

From the analysis above, extract and consolidate into this exact JSON (no markdown, no code fences):
{{
  "impact_score": <single integer -10 to +10 representing net India impact>,
  "signal_direction": "<positive | negative | mixed>",
  "signal_reason": "<one sentence explaining why this score and direction>",
  "impact_summary": "<one plain sentence: what happened and what it means for India>",
  "impact_chain": "<one sentence causal path using → arrows>",
  "affected_sectors": ["<up to 4 Indian sectors or industries most affected>"],
  "what_happened": "<2-3 sentence factual description of the core development — do NOT repeat the headline>",
  "so_what": "<2-3 sentences explaining the strategic significance — economic, regulatory, market, or geopolitical relevance>",
  "who_is_affected": ["<up to 5 specific stakeholder groups, industries, or player types affected>"],
  "what_to_watch": ["<up to 4 forward-looking items: upcoming decisions, milestones, risks, or follow-on events to monitor>"]
}}

Rules:
- impact_score: -10 = severely harmful to India, 0 = neutral, +10 = strongly beneficial to India
- If the raw analysis lists multiple scores, average them and round to the nearest integer
- signal_direction: use "mixed" only when there are both meaningful upside and downside effects
- impact_summary: exactly one sentence, plain prose, no bullet points
- impact_chain: must use → arrows, end with India consequence
- what_happened: factual, concise, do NOT repeat the headline verbatim
- so_what: explain WHY this matters, not just WHAT happened
- who_is_affected: be specific (e.g. "AI startups", "NBFCs", "semiconductor manufacturers"), avoid vague terms like "everyone"
- what_to_watch: must be forward-looking and actionable, not restatements of what happened
- If any field is genuinely unclear from the article, return null for that field instead of inventing content
- Return ONLY the JSON object, nothing else"""


COMPANY_STRUCTURED_SUMMARY = """\
Article: "{title}"
Source: {source} | Published: {published_date}
Company: {symbol}

Exa AI analysis:
{raw_summary}

From the analysis above, extract and consolidate into this exact JSON (no markdown, no code fences):
{{
  "impact_score": <single integer -10 to +10 representing net impact on {symbol}>,
  "signal_direction": "<positive | negative | mixed>",
  "signal_reason": "<one sentence explaining why this score and direction for {symbol}>",
  "impact_summary": "<one plain sentence: what happened and what it means for {symbol}>",
  "impact_chain": "<one sentence causal path using → arrows showing how this event impacts {symbol}>",
  "affected_sectors": ["<up to 4 business areas of {symbol} most affected, e.g. Revenue, Market Share, Operations, Partnerships>"],
  "what_happened": "<2-3 sentence factual description of the core development>",
  "so_what": "<2-3 sentences explaining the strategic significance for {symbol}>",
  "who_is_affected": ["<up to 5 specific stakeholder groups affected — investors, employees, competitors, partners, regulators>"],
  "what_to_watch": ["<up to 4 forward-looking items for {symbol}: upcoming earnings, regulatory decisions, market moves>"]
}}

Rules:
- impact_score: -10 = severely harmful to {symbol}, 0 = neutral, +10 = strongly beneficial to {symbol}
- Focus entirely on impact to the company {symbol}, NOT on India or any country
- If the raw analysis lists multiple scores, average them and round to the nearest integer
- signal_direction: use "mixed" only when there are both meaningful upside and downside effects
- impact_summary: exactly one sentence, plain prose, no bullet points
- impact_chain: must use → arrows, end with consequence for {symbol}
- what_happened: factual, concise
- so_what: explain strategic significance for {symbol}
- who_is_affected: be specific to {symbol}'s ecosystem
- what_to_watch: must be forward-looking and actionable
- Return ONLY the JSON object, nothing else"""


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1 — Daily Brief synthesis
# ─────────────────────────────────────────────────────────────────────────────

DAILY_BRIEF_SYNTHESIS = """\
You are generating a daily strategic intelligence brief for {region}.
Date: {date}

Below are today's top articles with structured insights:

{articles_json}

Using these articles, produce a JSON object (no markdown, no code fences):
{{
  "bottom_line": "<3-4 sentence executive summary tying together the biggest themes of the day — this should read as one coherent paragraph, not a list>",
  "top_developments": [
    {{
      "headline": "<short headline>",
      "summary": "<1-2 sentence summary>",
      "signal_score": <integer>,
      "signal_direction": "<positive | negative | mixed>"
    }}
  ],
  "signals_today": ["<up to 5 dominant signals or themes observed across articles>"],
  "what_to_watch_next": ["<up to 5 forward-looking items across all articles>"]
}}

Rules:
- bottom_line: must feel like one coherent story, not disconnected bullet points
- top_developments: pick the 4-6 most significant articles, ordered by importance
- signals_today: identify patterns and themes ACROSS articles, not per-article summaries
- what_to_watch_next: forward-looking, actionable, specific
- Keep it concise, analytical, and useful for a strategy-oriented professional
- Do NOT just list headlines; synthesize and find the narrative thread
- Return ONLY the JSON object, nothing else"""


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1 — Weekly Brief synthesis
# ─────────────────────────────────────────────────────────────────────────────

WEEKLY_BRIEF_SYNTHESIS = """\
You are generating a weekly strategic intelligence brief for {region}.
Week: {week_start} to {week_end}

Below are the week's articles with structured insights:

{articles_json}

Using these articles, produce a JSON object (no markdown, no code fences):
{{
  "bottom_line": "<4-5 sentence executive summary of the week — what actually changed, what patterns emerged, what the trajectory looks like>",
  "biggest_shifts": [
    {{
      "theme": "<theme name>",
      "description": "<2-3 sentences on what changed this week in this theme>",
      "direction": "<positive | negative | mixed>"
    }}
  ],
  "recurring_themes": ["<themes or signals that appeared repeatedly across the week>"],
  "what_to_watch_next_week": ["<up to 5 specific items to monitor in the coming week>"]
}}

Rules:
- bottom_line: must read as a coherent narrative, not a list
- biggest_shifts: 3-5 major thematic shifts, each with a clear direction
- recurring_themes: patterns that kept appearing across multiple days/articles
- what_to_watch_next_week: specific, actionable, tied to real upcoming events or decisions
- Focus on what CHANGED this week, not just what happened
- Identify which themes are strengthening, weakening, or new
- Return ONLY the JSON object, nothing else"""


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 — Multi-article theme synthesis
# ─────────────────────────────────────────────────────────────────────────────

THEME_SYNTHESIS = """\
You are synthesizing multiple articles about the theme: "{theme}"
Period: {period}
Region: {region}

Articles:
{articles_json}

Produce a JSON object (no markdown, no code fences):
{{
  "theme": "{theme}",
  "summary": "<3-4 sentence synthesis of what happened in this theme — tell the story, not a list>",
  "key_changes": ["<up to 5 specific changes or developments>"],
  "risks": ["<up to 4 risks or headwinds identified>"],
  "opportunities": ["<up to 4 opportunities or tailwinds identified>"],
  "what_to_watch": ["<up to 4 forward-looking items>"],
  "overall_direction": "<positive | negative | mixed>",
  "confidence": "<high | medium | low>"
}}

Rules:
- summary: coherent narrative, not bullet points disguised as a paragraph
- key_changes: specific and factual
- risks and opportunities: grounded in the articles, not generic
- what_to_watch: actionable and specific
- overall_direction: net direction of developments in this theme
- confidence: how confident the signal is based on volume and consistency of evidence
- Return ONLY the JSON object, nothing else"""


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 — Topic classification for clustering
# ─────────────────────────────────────────────────────────────────────────────

TOPIC_CLASSIFICATION = """\
Classify this article into exactly ONE primary theme from the list below.

Article title: "{title}"
Summary: {summary}

Themes:
- energy
- macro
- AI_and_technology
- semiconductors
- banking_and_finance
- healthcare
- geopolitics
- trade_and_commerce
- real_estate
- policy_and_regulation
- consumer_and_retail
- infrastructure
- agriculture
- telecom_and_media
- sustainability
- other

Return a JSON object (no markdown, no code fences):
{{
  "theme": "<one theme from the list above>"
}}

Rules:
- Pick the single most relevant theme
- Use "other" only if none of the themes fit at all
- Return ONLY the JSON object, nothing else"""


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 — Personalized "Why this matters to YOU"
# ─────────────────────────────────────────────────────────────────────────────

PERSONALIZED_INSIGHT = """\
Explain why this article matters to a specific user.

Article:
- Headline: {title}
- What happened: {what_happened}
- So what: {so_what}
- Impact score: {impact_score}
- Signal direction: {signal_direction}

User profile:
- Role: {user_role}
- Interests: {user_interests}
- Region focus: {user_geography}
- Experience level: {user_experience}

Return a JSON object (no markdown, no code fences):
{{
  "why_it_matters_to_you": "<2-3 sentences explaining why this matters to THIS specific user, given their role, interests, and focus. Be direct and professional. Do not be generic or cheesy. Connect the article's significance to their specific perspective.>"
}}

Rules:
- Use the user's actual profile to personalize — do not be generic
- Reference their role or interests naturally in the explanation
- Focus on actionable relevance: what should they pay attention to, why does this connect to their work
- If the article is not particularly relevant to this user's profile, say so honestly
- Return ONLY the JSON object, nothing else"""


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 — Stock / Sector sentiment mapping
# ─────────────────────────────────────────────────────────────────────────────

SECTOR_SENTIMENT = """\
Based on this article, assess the sentiment impact on relevant sectors and market themes.

Article:
- Headline: {title}
- What happened: {what_happened}
- So what: {so_what}
- Impact score: {impact_score}
- Signal direction: {signal_direction}

Return a JSON object (no markdown, no code fences):
{{
  "sector_sentiments": [
    {{
      "sector": "<specific sector or industry, e.g. 'semiconductor manufacturing', 'renewable energy'>",
      "direction": "<positive | negative | mixed>",
      "confidence": "<high | medium | low>",
      "horizon": "<immediate | short_term | medium_term | long_term>",
      "reason": "<one sentence explaining the connection>"
    }}
  ]
}}

Rules:
- List 1-4 most relevant sectors
- Be specific about sectors (not just "technology" — say "cloud infrastructure" or "AI chipmakers")
- confidence: based on how directly the article impacts the sector
- horizon: immediate = days, short_term = weeks, medium_term = months, long_term = years
- Do NOT make investment recommendations — keep to sector-level sentiment
- reason: must clearly connect the article to the sector impact
- Return ONLY the JSON object, nothing else"""


# ─────────────────────────────────────────────────────────────────────────────
# Exa search queries (used by news_fetcher.py)
# ─────────────────────────────────────────────────────────────────────────────

EXA_INDIA_SUMMARY_QUERY = """\
What is this news about, and how does it impact India?
- Summarise the core development in one sentence.
- Explain the direct or indirect impact on India (economy, markets, sectors, policy, geopolitics).
- Rate the impact on India: single score from -10 (very harmful to India) to +10 (very beneficial to India).
- Show the causal chain in one sentence using arrows: cause → effect → India impact."""

EXA_COMPANY_SUMMARY_QUERY = """\
What is this news about, and how does it impact the company?
- Summarise the core development in one sentence.
- Explain the direct impact on the company (revenue, stock price, market position, operations, partnerships, regulation).
- Rate the impact on the company: single score from -10 (very harmful) to +10 (very beneficial).
- Show the causal chain in one sentence using arrows: cause → effect → company impact."""

import os
from pathlib import Path

from dotenv import load_dotenv, find_dotenv
from exa_py import Exa
from openai import OpenAI

# Search for .env starting from the working directory upward
load_dotenv(find_dotenv(usecwd=True))


def _get_secret(key, default=""):
    """Read from Streamlit secrets (cloud) first, then fall back to env vars."""
    try:
        import streamlit as st
        return st.secrets.get(key, os.environ.get(key, default))
    except Exception:
        return os.environ.get(key, default)


EXA_API_KEY = _get_secret("EXA_API_KEY")
OPENAI_API_KEY = _get_secret("OPENAI_API_KEY")
OPENAI_API_BASE = _get_secret("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_MODEL = _get_secret("OPENAI_MODEL", "gpt-4o")

# Initialize clients with error checking
exa_client = None
openai_client = None

if EXA_API_KEY:
    try:
        exa_client = Exa(api_key=EXA_API_KEY)
    except Exception as e:
        print(f"Warning: Failed to initialize Exa client: {e}")

if OPENAI_API_KEY:
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE)
    except Exception as e:
        print(f"Warning: Failed to initialize OpenAI client: {e}")
else:
    print("Warning: OPENAI_API_KEY not configured")

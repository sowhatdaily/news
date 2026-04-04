# Streamlit Community Cloud Deployment Guide

## Prerequisites

Your app requires two external API keys to function:

### 1. **OpenAI API Key** (required)
- **Purpose**: Powers content summarization, analysis, and AI features
- **Get Key**: https://platform.openai.com/api-keys
- **Cost**: Pay-as-you-go (costs apply)

### 2. **Exa API Key** (required)
- **Purpose**: News fetching and search functionality
- **Get Key**: https://dashboard.exa.ai
- **Cost**: Free tier available at https://exa.ai

---

## Configuration Steps

### Step 1: Deploy to Streamlit Cloud

```bash
git push origin main
```

Then go to [share.streamlit.io](https://share.streamlit.io) and connect your repository.

### Step 2: Add Secrets (Critical!)

1. **Go to your app dashboard** on share.streamlit.io
2. **Click your deployed app**
3. **Click the three dots (⋮)** → **Settings**
4. **Click "Secrets"** in the sidebar
5. **Paste the following and add your actual keys:**

```
OPENAI_API_KEY = "sk-proj-xxxxxxxxxxxxx"
EXA_API_KEY = "xxxxxxxxxxxxx"
```

### Step 3: Reboot the App

- Click the **three dots (⋮)** → **Reboot app**
- Wait 30 seconds for it to restart
- Check that it loads properly

---

## Troubleshooting

### Still seeing blank screen?
- ✅ Check Streamlit logs (share.streamlit.io → App Settings → Logs)
- ✅ Verify secrets are exact (no extra spaces)
- ✅ Ensure API keys are still valid (not expired)
- ✅ Check that API keys have appropriate permissions

### "Configuration Error" message?
This means one or more secrets weren't found. Follow **Step 2** above.

### App runs but features don't work?
API keys might be valid but lack necessary permissions:
- **OpenAI**: Ensure account has API access + sufficient credits
- **Exa**: Check that API key is active on dashboard.exa.ai

---

## Local Development

To test locally with the same setup:

1. **Create `.env` file:**
```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
EXA_API_KEY=xxxxxxxxxxxxx
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run app:**
```bash
streamlit run streamlit_app.py
```

---

## Important Notes

- **Never commit `.env` files or API keys to Git**
- **Secrets are stored securely** on Streamlit Cloud and not visible in logs
- **API costs**: Monitor your API usage to avoid unexpected charges
- **Database**: SQLite database is stored in the app container (`anonimous_ai.db`)

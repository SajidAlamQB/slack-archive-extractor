# Slack Archive Extractor

Simple web app to extract messages from slackdump sqlite archives for LLM analysis.

## Quick Deploy to Streamlit Cloud (Free)

1. **Create a GitHub repo** with these files:
   - `app.py`
   - `requirements.txt`

2. **Go to** https://share.streamlit.io

3. **Sign in** with GitHub

4. **Click "New app"** and select:
   - Your repo
   - Branch: `main`
   - Main file: `app.py`

5. **Click Deploy** - takes ~2 minutes

6. **Share the URL** with Alice!

## Local Testing

```bash
pip install streamlit
streamlit run app.py
```

## Usage

1. Upload a `.sqlite` file from slackdump
2. View the summary of channels/messages
3. Download JSON or TXT for LLM use

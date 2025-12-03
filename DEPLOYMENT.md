# 🚀 Deploying AAG to Streamlit Cloud

## Prerequisites

1. ✅ GitHub account
2. ✅ Code pushed to GitHub (Done!)
3. ✅ Gemini API key
4. ✅ Google Service Account JSON
5. ✅ Google Sheet ID

## Step-by-Step Deployment

### 1. Go to Streamlit Cloud

Visit: https://share.streamlit.io/

### 2. Sign in with GitHub

Click "Sign in with GitHub" and authorize Streamlit

### 3. Create New App

1. Click **"New app"** button
2. Fill in the form:
   - **Repository**: `AnkurSinghYadav09/DBMS-projects-auto-grader`
   - **Branch**: `main`
   - **Main file path**: `dashboard.py`
   - **App URL** (optional): Choose a custom name like `aag-dbms-grader`

### 4. Add Secrets

Before deploying, click **"Advanced settings"** and add secrets:

```toml
# Paste this into the Secrets section:

AI_PROVIDER = "gemini"
GEMINI_API_KEY = "AIzaSyAdfYwVP8M7EXQzwsTdu3pmEvSwKFSbisc"
GEMINI_MODEL = "models/gemini-2.5-flash"

SPREADSHEET_ID = "1e-YGe4J3zJp-5TtRdFlB_vGfWiweELKnvTzNk9Uv4GE"
SHEET_NAME = "Sheet1"

DOC_LINK_COLUMN = "A"
STUDENT_NAME_COLUMN = "B"
SCORE_COLUMN = "C"
FEEDBACK_COLUMN = "D"

MAX_WORKERS = "5"
RETRY_ATTEMPTS = "3"
BATCH_SIZE = "10"
INCLUDE_PLAGIARISM_CHECK = "True"

# Add your full service_account.json content here:
[gcp_service_account]
type = "service_account"
project_id = "YOUR_PROJECT_ID"
private_key_id = "YOUR_PRIVATE_KEY_ID"
private_key = "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n"
client_email = "YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com"
client_id = "YOUR_CLIENT_ID"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "YOUR_CERT_URL"
```

**Important**: Replace the GCP service account values with your actual `credentials/service_account.json` content.

### 5. Update Code to Read Secrets

You'll need to update `src/config.py` to read from Streamlit secrets. I'll do this next.

### 6. Deploy

Click **"Deploy!"** button

⏱️ Deployment takes 2-3 minutes

### 7. Your App is Live! 🎉

Access at: `https://your-app-name.streamlit.app`

## Post-Deployment

### Update the App

Any push to the `main` branch will automatically redeploy!

```bash
git add .
git commit -m "Update prompt"
git push origin main
```

Streamlit will auto-detect and redeploy in ~1 minute.

### View Logs

In Streamlit Cloud dashboard:
- Click your app
- Click "Manage app"
- View logs in real-time

### Share with Team

Send them the URL: `https://your-app-name.streamlit.app`

No login required (unless you set it to private)!

## Troubleshooting

### "Module not found" error
- Check `requirements.txt` includes all dependencies
- Make sure branch is `main` not `master`

### Secrets not loading
- Verify secrets format (TOML syntax)
- No quotes around section headers like `[gcp_service_account]`
- Private key must include `\n` for newlines

### App crashes on startup
- Check logs in Streamlit dashboard
- Test locally first: `streamlit run dashboard.py`

### Google API errors
- Ensure service account has Sheet & Docs API access
- Sheet must be shared with service account email

## Free Tier Limits

- ✅ 1 GB RAM
- ✅ 1 CPU
- ✅ Unlimited requests
- ⚠️ App sleeps after 5 min inactivity (wakes in 30s)

Perfect for your use case! 🎯

## Next Steps

1. I'll update the code to read Streamlit secrets
2. Push the changes
3. You deploy on Streamlit Cloud
4. Share the URL with your team!

Ready? Say **"update code for streamlit deployment"**

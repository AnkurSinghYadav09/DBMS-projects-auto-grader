# Auto Evaluator System

Automatically evaluate student Google Docs using AI and update results in Google Sheets.

## Features

- ✅ Reads Google Doc links from Google Sheets
- ✅ Extracts full document text (including tables)
- ✅ AI-powered evaluation using GPT-4
- ✅ Customizable rubric system
- ✅ Automatic score and feedback writing to sheet
- ✅ Parallel processing for speed
- ✅ Comprehensive error handling and logging
- ✅ Retry logic for API failures
- ✅ Optional plagiarism detection

## Prerequisites

1. **Google Cloud Project** with enabled APIs:
   - Google Sheets API
   - Google Drive API
   - Google Docs API

2. **Service Account** with JSON credentials

3. **OpenAI API Key**

4. **Python 3.8+**

## Setup Instructions

### 1. Clone & Install

```bash
git clone <your-repo>
cd auto-evaluator
pip install -r requirements.txt
```

### 2. Configure Google Cloud

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable APIs: Sheets, Drive, Docs
4. Create Service Account:
   - IAM & Admin → Service Accounts → Create
   - Download JSON key
   - Save as `credentials/service_account.json`
5. Share your Google Sheet and Docs folder with:
   ```
   your-service-account@project-id.iam.gserviceaccount.com
   ```

### 3. Configure Environment

Copy `.env` template and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:
```
OPENAI_API_KEY=sk-...
SPREADSHEET_ID=1abc...
SHEET_NAME=Sheet1
```

To get your Spreadsheet ID:
- Open your Google Sheet
- Look at the URL: `https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit`

### 4. Prepare Your Google Sheet

Required columns:
| A | B | C | D |
|---|---|---|---|
| Doc Link | Student Name | Score | Feedback |
| https://docs.google.com/... | John Doe | (auto) | (auto) |

### 5. Customize Rubric (Optional)

Edit `rubrics/default_rubric.json`:

```json
{
  "total_points": 100,
  "criteria": [
    {
      "name": "Problem Statement",
      "points": 10,
      "description": "Clear problem identification"
    }
  ]
}
```

### 6. Run Evaluator

```bash
python main.py
```

## Configuration Options

In `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `MAX_WORKERS` | Parallel processing threads | 5 |
| `BATCH_SIZE` | Documents per batch | 10 |
| `RETRY_ATTEMPTS` | API retry attempts | 3 |
| `INCLUDE_PLAGIARISM_CHECK` | Enable plagiarism detection | True |
| `OPENAI_MODEL` | GPT model to use | gpt-4-turbo-preview |

## Output Format

The system writes to your sheet:

**Score Column**: Numeric score (0-100) or "ERROR"

**Feedback Column**: Formatted as:
```
Strengths: ... | Areas for Improvement: ... | Recommendations: ... | Plagiarism Check: ...
```

## Logs

All processing logs are saved to `logs/evaluation_YYYYMMDD_HHMMSS.log`

## Troubleshooting

### "Configuration errors"
- Check `.env` file has all required values
- Verify `service_account.json` exists in `credentials/`

### "Permission denied" errors
- Share sheet/docs with service account email
- Check service account has "Editor" role

### "Invalid document URL"
- Ensure column A contains full Google Docs URLs
- Format: `https://docs.google.com/document/d/{DOC_ID}/edit`

### "API quota exceeded"
- Reduce `MAX_WORKERS` in `.env`
- Add delays between batches

## Cost Estimation

Using GPT-4 Turbo:
- ~$0.01 per document (typical)
- 100 documents ≈ $1.00
- Adjust model in `.env` to reduce costs

## Security Notes

⚠️ **Never commit** these files to Git:
- `credentials/service_account.json`
- `.env`
- `logs/*.log`

Already configured in `.gitignore`

## Support

For issues, check logs in `logs/` directory first.

## License

MIT License

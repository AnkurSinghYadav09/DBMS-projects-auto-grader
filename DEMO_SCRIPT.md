# 🎯 Demo Script - Auto Evaluator Dashboard

## Pre-Demo Setup (5 minutes)

1. **Terminal Setup:**
   ```bash
   cd /Users/ankursingh/Documents/dbms-auto-evaluator
   source .venv/bin/activate
   pip install streamlit plotly
   ```

2. **Open Google Sheet in Browser:**
   - Have your evaluation sheet ready
   - Show empty Score/Feedback columns

3. **Start Dashboard:**
   ```bash
   streamlit run dashboard.py
   ```

---

## Live Demo Script (5 minutes)

### 1. Introduction (30 seconds)
> "Today I'm showing you our DBMS Auto Evaluator - a system that automatically grades student database projects using AI. It evaluates SQL code, ER diagrams, queries, and documentation in seconds instead of hours."

### 2. Show the Dashboard (30 seconds)
**Point out key features:**
- Configuration panel (shows which sheet and AI model)
- Big evaluation button
- Real-time progress tracking

> "The dashboard connects to our Google Sheet where students submit their project links, processes each document with Google's Gemini AI, and writes back scores with detailed feedback."

### 3. Show Before State (30 seconds)
**Switch to Google Sheet tab:**
- Point to Column A: "Here are links to student Google Docs"
- Point to Column B: "Student names"
- Point to Columns C & D: "These are currently empty - this is what gets auto-filled"

### 4. Run Evaluation (2 minutes)
**Switch back to dashboard:**
1. Click "🚀 Start Evaluation" button
2. **As it runs, narrate:**
   - "Validating configuration..."
   - "Found X documents..."
   - "Now evaluating each one using AI..."
   - "Each document takes 2-5 seconds"

3. **Point out the progress bar**
4. **When complete, show statistics:**
   - Total documents processed
   - Time taken
   - Average time per document

### 5. Show Results (1 minute)
**Switch to Google Sheet:**
- Refresh the page
- Show Column C now has scores
- Click into Column D to show detailed feedback
- Pick one example: "Look at this feedback - it identifies strengths like 'proper normalization' and gives specific recommendations like 'add composite indexes'"

### 6. Key Benefits (30 seconds)
> "The key advantages:
> - **Speed:** 300 projects in under 30 minutes vs. days manually
> - **Consistency:** Same rubric applied to everyone, deterministic scoring
> - **Quality:** Detailed, actionable feedback for each student
> - **Cost:** Completely free using Google Gemini's API
> - **Transparency:** All rubric criteria shown in the evaluation"

### 7. Q&A (remaining time)

---

## Common Questions & Answers

**Q: How accurate is the AI grading?**
> A: We've tested it with deterministic scoring - same document gets same score within 5 points across multiple runs. It follows our detailed rubric exactly.

**Q: What if a student's document is private?**
> A: They just need to share it with our service account email - takes 5 seconds.

**Q: Can we customize the rubric?**
> A: Yes! Edit `rubrics/default_rubric.json` or create new rubrics. The dashboard will use whatever rubric you define.

**Q: What happens if the API fails?**
> A: Built-in retry logic (3 attempts) and error handling. Failed documents are marked as "ERROR" and logged for manual review.

**Q: Is this only for DBMS projects?**
> A: No! Just change the rubric. Works for any document-based evaluation.

**Q: What's the cost?**
> A: Zero. We use Google Gemini's free tier (1,500 requests/day). Even with paid tier, 300 documents would cost ~$0.20.

---

## Backup: CLI Demo (if dashboard fails)

If Streamlit has issues, fall back to CLI:

```bash
python main.py
```

**Narrate while logs scroll:**
- "You can see it reading each document..."
- "Extracting text from Google Docs..."
- "Sending to AI for evaluation..."
- "Writing results back to sheet..."

Then show the Google Sheet results.

---

## Post-Demo: Show Them This

**GitHub Repo Structure:**
```
dbms-auto-evaluator/
├── dashboard.py          ← What you just saw
├── main.py              ← CLI version
├── .env                 ← Configuration
├── src/
│   ├── evaluator.py     ← AI evaluation logic
│   ├── google_api.py    ← Google APIs integration
│   └── sheet_processor.py ← Main orchestration
├── rubrics/
│   └── default_rubric.json ← Scoring criteria
└── logs/                ← Detailed processing logs
```

---

## Tips for a Smooth Demo

1. **Test beforehand:** Run it once 30 minutes before demo
2. **Have 2-3 test documents:** Don't demo with 300 on first run
3. **Screen arrangement:** Dashboard on left, Google Sheet on right
4. **Internet connection:** Ensure stable WiFi
5. **Backup plan:** Have screenshots ready if live demo fails
6. **Time buffer:** Leave 5 extra minutes for questions

---

## Next Steps After Demo

1. **Share dashboard URL** (if deployed to Cloud Run)
2. **Send instructions PDF** for team to try themselves
3. **Schedule feedback session** in 1 week
4. **Discuss rollout plan** for next semester

Good luck! 🚀

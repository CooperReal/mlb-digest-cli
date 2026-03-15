# MLB Digest CLI - User Guide

This guide walks you through everything step by step. No assumptions about what you already know.

---

## Step 1: Install Python

You need Python 3.11 or newer.

**Check if you have it:**

Open a terminal (Command Prompt on Windows, Terminal on Mac) and type:

```bash
python --version
```

You should see something like `Python 3.11.1` or higher. If you get an error or a version below 3.11, download Python from [python.org/downloads](https://www.python.org/downloads/).

**Windows users:** During installation, check the box that says "Add Python to PATH". This is important.

---

## Step 2: Download the Project

Open your terminal and run:

```bash
git clone https://github.com/CooperReal/mlb-digest-cli.git
cd mlb-digest-cli
```

If you don't have `git`, you can download the ZIP from GitHub and unzip it instead.

---

## Step 3: Set Up a Virtual Environment

A virtual environment keeps this project's packages separate from everything else on your computer. You only need to do this once.

**Mac/Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
```

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

You should see `(.venv)` at the beginning of your terminal prompt. That means it's working.

**Every time you open a new terminal** to work with this project, you need to activate the virtual environment again with the `source` or `.venv\Scripts\activate` command above.

---

## Step 4: Install Dependencies

With your virtual environment activated, run:

```bash
pip install -e ".[dev]"
```

This installs everything the project needs. It might take a minute.

---

## Step 5: Get an Anthropic API Key

This tool uses Claude (by Anthropic) to write the digest. You need an API key.

1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Create an account (or sign in)
3. Go to **API Keys** in the left sidebar
4. Click **Create Key**
5. Copy the key - it starts with `sk-ant-`

**Cost:** This will cost roughly $0.50 - $1.50 per month for daily use. Each digest costs about 1-3 cents.

---

## Step 6: Set Up Gmail App Password

The tool sends emails through your Gmail account. Google requires an "App Password" for this (your regular password won't work).

1. Go to [myaccount.google.com](https://myaccount.google.com/)
2. Click **Security** in the left sidebar
3. Make sure **2-Step Verification** is turned ON (you need this first)
4. Go back to Security, scroll down to **App passwords** (or search for it)
5. Click **App passwords**
6. Select **Mail** as the app and **Windows Computer** (or whatever) as the device
7. Click **Generate**
8. Google will show you a 16-character password like `abcd efgh ijkl mnop`
9. Copy it (remove the spaces when you paste it later)

**If you don't see "App passwords":** You need to enable 2-Step Verification first. Go to Security > 2-Step Verification and follow the prompts.

---

## Step 7: Create Your .env File

This file holds your secret keys. It is NOT uploaded to GitHub.

1. In the project folder, copy the example file:

   **Mac/Linux:**
   ```bash
   cp .env.example .env
   ```

   **Windows:**
   ```bash
   copy .env.example .env
   ```

2. Open `.env` in any text editor (Notepad, VS Code, whatever) and fill in your real values:

   ```
   ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
   GMAIL_ADDRESS=yourname@gmail.com
   GMAIL_APP_PASSWORD=abcdefghijklmnop
   ```

   Replace the placeholder values with your actual API key, Gmail address, and app password.

3. Save the file.

---

## Step 8: Update config.toml (Optional)

The `config.toml` file controls which team you follow and where the email goes. Open it in a text editor.

**Change the email recipient** to your actual email:

```toml
[email]
recipients = ["yourname@gmail.com"]
```

**To follow a different team**, change the team section. Here are some common team IDs:

| Team | ID | League ID |
|------|----|-----------|
| Atlanta Braves | 144 | 104 (NL) |
| New York Yankees | 147 | 103 (AL) |
| Los Angeles Dodgers | 119 | 104 (NL) |
| Boston Red Sox | 111 | 103 (AL) |
| Chicago Cubs | 112 | 104 (NL) |
| Houston Astros | 117 | 103 (AL) |
| New York Mets | 121 | 104 (NL) |
| Philadelphia Phillies | 143 | 104 (NL) |
| San Diego Padres | 135 | 104 (NL) |
| San Francisco Giants | 137 | 104 (NL) |

For example, to follow the Yankees:

```toml
[team]
id = 147
name = "Yankees"
league_id = 103
colors = { primary = "#003087", accent = "#E4002B" }
```

You'd also want to change the team RSS feed. Find your team's MLB Trade Rumors feed at:
`https://www.mlbtraderumors.com/your-team-name/feed`

```toml
[feeds.team]
urls = ["https://www.mlbtraderumors.com/new-york-yankees/feed"]
```

---

## Step 9: Test Your Email Setup

Before doing anything else, make sure the email works:

```bash
mlb-digest test-email
```

You should see: `Test email sent successfully!`

Check your inbox for an email with the subject "MLB Digest - Test Email".

**If it fails:**
- Double-check your Gmail address and app password in `.env`
- Make sure there are no extra spaces in the `.env` values
- Make sure 2-Step Verification is enabled on your Google account
- Try generating a new app password

---

## Step 10: Try It Out

Now let's see what the digest looks like. Start with `--no-email` so it prints to your terminal instead of sending an email:

```bash
mlb-digest --no-email
```

This will:
1. Fetch game data from the MLB API
2. Fetch articles from RSS feeds
3. Send everything to Claude to write up
4. Print the digest to your terminal

**First time might take 15-30 seconds** because it's fetching stats for every player on the roster.

**Want to see the full catchup report?**

```bash
mlb-digest --catchup --no-email
```

This adds a full roster breakdown, season overview, and division rivals.

**Just want to see what data it's pulling?**

```bash
mlb-digest --dry-run
```

This skips Claude and email entirely and just shows you the raw data in JSON format. Useful for debugging.

---

## Step 11: Send Your First Real Email

Once you're happy with the output, send it for real:

```bash
mlb-digest
```

Or with the catchup content:

```bash
mlb-digest --catchup
```

Check your email. You should have a nicely formatted digest with team-colored headers.

---

## Running It Daily (Optional)

The whole point is to get this automatically every morning. Here are a few ways to do that:

### Option A: Windows Task Scheduler

1. Open **Task Scheduler** (search for it in Start)
2. Click **Create Basic Task**
3. Name it "MLB Digest"
4. Set the trigger to **Daily** at your preferred time (e.g., 7:00 AM)
5. Set the action to **Start a Program**
6. Program: `C:\path\to\mlb-digest-cli\.venv\Scripts\python.exe`
7. Arguments: `-m mlb_digest.cli`
8. Start in: `C:\path\to\mlb-digest-cli`

**Note:** Your computer needs to be on at the scheduled time.

### Option B: Mac/Linux Cron

```bash
crontab -e
```

Add this line (runs at 7 AM every day):

```
0 7 * * * cd /path/to/mlb-digest-cli && .venv/bin/python -m mlb_digest.cli
```

### Option C: Cloud (Later)

You can also run this on AWS Lambda, Google Cloud Functions, or any server with a cron job. The tool has no state and no database, so it works anywhere that has Python.

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'mlb_digest'"

You forgot to activate the virtual environment. Run:

```bash
source .venv/bin/activate  # Mac/Linux
.venv\Scripts\activate     # Windows
```

### "Missing required environment variables: ANTHROPIC_API_KEY"

Your `.env` file is missing or has empty values. Make sure you created it (Step 7) and filled in real values.

### "SMTP Authentication Error"

Your Gmail app password is wrong. Go back to Step 6 and generate a new one. Make sure you're using the app password, not your regular Gmail password.

### "No game data" or empty digest

If it's the off-season (November - March) or an off-day, there won't be game data. The digest will still include articles and standings if available.

### Digest is too slow

The first run fetches stats for every player on the roster (~26 API calls). This takes 10-20 seconds. Subsequent runs are the same speed because there's no caching (each run is fresh data).

### Email lands in spam

If the email goes to spam, mark it as "Not Spam" once. Gmail learns from this. You can also add the sender address to your contacts.

---

## Quick Reference

| Command | What it does |
|---------|-------------|
| `mlb-digest` | Send the daily digest email |
| `mlb-digest --catchup` | Send digest + roster/season/rivals |
| `mlb-digest --no-email` | Print to terminal (don't send email) |
| `mlb-digest --dry-run` | Show raw data (no Claude, no email) |
| `mlb-digest --catchup --no-email` | Full report printed to terminal |
| `mlb-digest test-email` | Send a test email to verify setup |

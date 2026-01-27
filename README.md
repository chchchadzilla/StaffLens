# StaffLens 🎙️🤖

**Version 0.1.0** | [License: MIT with Attribution](#-license)

**Fully autonomous AI interviewer Discord bot that conducts natural voice conversations with applicants, then delivers comprehensive psychological assessments to your team.**

StaffLens uses cutting-edge AI to have real, dynamic voice conversations with your applicants—no scripted questions, no awkward silences, just a natural interview powered by an AI "workplace psychologist." When the conversation ends, you get a detailed report covering communication skills, problem-solving ability, emotional intelligence, red flags, and a clear hire/no-hire recommendation.

---

## ⚠️ IMPORTANT: Two Files You MUST Edit

Before running StaffLens, you **MUST** configure these two files:

| File | What It Does | Required? |
|------|--------------|-----------|
| **`.env`** | Your API keys, Discord token, channel IDs | ✅ **YES** |
| **`interview-config.md`** | Customizes the AI interviewer for YOUR community | ✅ **YES** |

> 🚨 **The bot will NOT work correctly without editing BOTH files!** See [Step 6](#-step-6-configure-the-bot) and [Step 8](#-step-8-customize-the-interview-important) for detailed instructions.

---

## ✨ What Makes StaffLens Different

| Feature | Old-School Bots | **StaffLens** |
|---------|-----------------|---------------|
| **Interview Style** | Pre-written questions read in order | Dynamic AI conversation that responds to what they actually say |
| **Voice Interaction** | None or basic | Full TTS voice output—the bot literally speaks to them |
| **Analysis** | Basic sentiment or none | Deep psychological profiling by AI "workplace psychologist" |
| **Accessibility** | Voice only | Voice + real-time text transcription for deaf/HoH users |
| **Intelligence** | Rules-based | Powered by Claude 3 Haiku via OpenRouter |

### The Magic

1. **Applicant joins voice channel** → Bot joins and greets them naturally
2. **AI conducts a real conversation** → Responds to their answers, asks follow-ups, probes deeper
3. **Bot speaks AND displays text** → Accessibility-first design
4. **3 seconds of silence** → Bot moves to next topic (not awkward long waits)
5. **Conversation naturally ends** → AI wraps up when it has enough info
6. **Instant analysis** → Comprehensive report posted to your staff channel

---

## 📋 Table of Contents

1. [What You'll Need](#-what-youll-need)
2. [Step 1: Create a Discord Bot](#-step-1-create-a-discord-bot)
3. [Step 2: Install Python](#-step-2-install-python)
4. [Step 3: Install FFmpeg](#-step-3-install-ffmpeg-required-for-voice)
5. [Step 4: Download & Setup StaffLens](#-step-4-download--setup-stafflens)
6. [Step 5: Get Your API Keys](#-step-5-get-your-api-keys)
7. [Step 6: Configure the Bot](#-step-6-configure-the-bot)
8. [Step 7: Setup Your Discord Server](#-step-7-setup-your-discord-server)
9. [Step 8: Customize the Interview](#-step-8-customize-the-interview-important)
10. [Step 9: Run the Bot](#-step-9-run-the-bot)
11. [Step 10: Test Everything](#-step-10-test-everything)
12. [Commands Reference](#-commands-reference)
13. [How the AI Interview Works](#-how-the-ai-interview-works)
14. [Understanding the Report](#-understanding-the-report)
15. [Troubleshooting](#-troubleshooting)
16. [Project Structure](#-project-structure)
17. [License](#-license)

---

## 🛠️ What You'll Need

Before starting, make sure you have these things ready:

| Thing | What It Is | Where To Get It | Cost |
|-------|-----------|-----------------|------|
| **Discord Account** | Your account to manage the bot | [discord.com](https://discord.com) | Free |
| **A Discord Server** | Where the bot will operate (you need admin) | Create one or use existing | Free |
| **Python 3.10+** | Programming language the bot runs on | [python.org](https://python.org) | Free |
| **FFmpeg** | Audio processing tool (required for voice) | See Step 3 below | Free |
| **Deepgram Account** | Turns voice audio into text | [deepgram.com](https://console.deepgram.com) | Free tier: $200 credit |
| **OpenRouter Account** | AI that runs the interview & analysis | [openrouter.ai](https://openrouter.ai) | Pay-per-use (~$0.01/interview) |

### Time Estimate
- **First-time setup:** 30-45 minutes
- **If you've done this before:** 10-15 minutes

---

## 🤖 Step 1: Create a Discord Bot

### 1.1 Go to the Discord Developer Portal

1. Open your web browser and go to: **[discord.com/developers/applications](https://discord.com/developers/applications)**
2. Log in with your Discord account (the same one that owns the server)
3. You'll see a list of your applications (probably empty)

### 1.2 Create a New Application

1. Click the big blue **"New Application"** button in the top-right corner
2. A popup will ask for a name—type `StaffLens` (or whatever you want to call your bot)
3. Check the box agreeing to Terms of Service
4. Click **"Create"**

You'll now see your application's settings page.

### 1.3 Create the Bot User

1. In the **left sidebar**, find and click **"Bot"**
2. You'll see a page about your bot (it might say "Build-A-Bot")
3. Click the **"Reset Token"** button
4. Discord will ask "Are you sure?" — Click **"Yes, do it!"**
5. A long string of random characters will appear — this is your **bot token**
6. Click **"Copy"** immediately
7. **⚠️ PASTE THIS SOMEWHERE SAFE RIGHT NOW** — You can only see this once! If you lose it, you'll have to reset it again.

> **Security Warning:** Never share your bot token with anyone! It's like a password—anyone with it can control your bot.

### 1.4 Enable Required Permissions

Still on the Bot page, scroll down to the section called **"Privileged Gateway Intents"**

You need to enable these three toggles:

- ✅ **PRESENCE INTENT** — Lets the bot see who's online (optional but nice)
- ✅ **SERVER MEMBERS INTENT** — **Required!** Lets the bot see member roles (needed to detect applicants)
- ✅ **MESSAGE CONTENT INTENT** — **Required!** Lets the bot read commands

Click the toggle switches to turn them ON (they turn blue/purple when enabled).

Click **"Save Changes"** at the bottom.

### 1.5 Generate the Invite Link

Now we need to create a special link to invite the bot to your server:

1. In the left sidebar, click **"OAuth2"**
2. Then click **"URL Generator"** (it's under OAuth2)

**Under SCOPES**, check these boxes:
- ✅ `bot`
- ✅ `applications.commands`

**Under BOT PERMISSIONS**, check these boxes:
- ✅ Send Messages
- ✅ Send Messages in Threads
- ✅ Embed Links
- ✅ Attach Files
- ✅ Read Message History
- ✅ Connect
- ✅ Speak
- ✅ Use Voice Activity

3. Scroll to the bottom—you'll see a **Generated URL**
4. Click **"Copy"** to copy this URL
5. Open a new browser tab and paste the URL
6. Select your server from the dropdown
7. Click **"Authorize"**
8. Complete the captcha

**🎉 Your bot is now in your server!** It will appear offline until we run it later.

---

## 🐍 Step 2: Install Python

### Windows

1. Go to [python.org/downloads](https://python.org/downloads)
2. Click the big yellow "Download Python 3.x.x" button
3. Open the downloaded file
4. **⚠️ CRITICAL:** On the first installer screen, check the box that says **"Add Python to PATH"** at the bottom
5. Click **"Install Now"**
6. Wait for it to finish, then click **"Close"**

### Mac

**Option A: From Python.org**
1. Go to [python.org/downloads/macos](https://python.org/downloads/macos)
2. Download the latest Python 3.x installer
3. Open the .pkg file and follow the prompts

**Option B: Using Homebrew (if you have it)**
```bash
brew install python
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### Verify Python Installation

Open a terminal/command prompt and type:

```bash
python --version
```

You should see something like `Python 3.10.x` or `Python 3.11.x` or higher.

If Windows says "python not found," try:
```bash
python3 --version
```

If that works, use `python3` instead of `python` for all future commands.

---

## 🔊 Step 3: Install FFmpeg (REQUIRED for Voice)

FFmpeg is what lets the bot actually play audio in voice channels. **The bot will not work without it.**

### Windows

**Option A: Using winget (Windows 11 or Windows 10 with App Installer)**
```powershell
winget install ffmpeg
```

**Option B: Using Chocolatey (if you have it)**
```powershell
choco install ffmpeg
```

**Option C: Manual Installation**
1. Go to [ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Under "Windows," click the Windows logo
3. Click "Windows builds from gyan.dev"
4. Download the "ffmpeg-release-essentials.zip"
5. Extract the zip file
6. Find the `bin` folder inside (contains `ffmpeg.exe`)
7. Copy the full path to the `bin` folder (e.g., `C:\ffmpeg\bin`)
8. Add this path to your system's PATH environment variable:
   - Search "environment variables" in Windows search
   - Click "Edit the system environment variables"
   - Click "Environment Variables" button
   - Under "System variables," find "Path" and click "Edit"
   - Click "New" and paste the path to the bin folder
   - Click OK on all windows

### Mac

```bash
brew install ffmpeg
```

### Linux (Ubuntu/Debian)

```bash
sudo apt install ffmpeg
```

### Verify FFmpeg Installation

**IMPORTANT: Close your terminal/command prompt and open a new one first!** Then run:

```bash
ffmpeg -version
```

You should see version information. If it says "command not found," restart your computer and try again.

---

## 📥 Step 4: Download & Setup StaffLens

### 4.1 Download the Code

**Option A: Using Git (Recommended)**

If you have Git installed:
```bash
git clone https://github.com/YourUsername/stafflens.git
cd stafflens
```

**Option B: Download as ZIP**

1. Click the green "Code" button on this GitHub page
2. Click "Download ZIP"
3. Extract the ZIP to a folder you'll remember (e.g., `C:\StaffLens` or `~/StaffLens`)
4. Open a terminal/command prompt
5. Navigate to that folder:
   - Windows: `cd C:\StaffLens`
   - Mac/Linux: `cd ~/StaffLens`

### 4.2 Create a Virtual Environment

A virtual environment keeps StaffLens's packages separate from other Python projects. It's not strictly required but highly recommended.

**Create it:**
```bash
python -m venv venv
```

**Activate it:**

Windows (Command Prompt):
```cmd
venv\Scripts\activate
```

Windows (PowerShell):
```powershell
.\venv\Scripts\Activate.ps1
```

Mac/Linux:
```bash
source venv/bin/activate
```

You'll know it's activated when you see `(venv)` at the start of your command line.

> **Note:** Every time you open a new terminal to run the bot, you'll need to activate the virtual environment again with the activate command above.

### 4.3 Install Dependencies

```bash
pip install -r requirements.txt
```

This downloads all the packages StaffLens needs. It might take a minute or two.

You should see a lot of text scrolling by. When it's done, you'll see "Successfully installed..." at the end.

---

## 🔑 Step 5: Get Your API Keys

### 5.1 Deepgram API Key (for Speech-to-Text)

Deepgram is what turns audio into text. They have a generous free tier.

1. Go to [console.deepgram.com](https://console.deepgram.com)
2. Click "Sign Up" and create an account (Google sign-in works)
3. Once logged in, you'll see a dashboard
4. In the left sidebar, click **"API Keys"**
5. Click **"Create a New API Key"**
6. For the name, type `StaffLens`
7. For permissions, leave it as default (all permissions)
8. Click **"Create Key"**
9. A popup will show your API key — **COPY IT NOW**
10. Save it somewhere safe (a text file, password manager, etc.)

> **Free Tier:** $200 in credits, which is roughly 100+ hours of transcription. More than enough to get started.

### 5.2 OpenRouter API Key (for AI Brain)

OpenRouter gives us access to powerful AI models like Gemini 3 Flash.

1. Go to [openrouter.ai](https://openrouter.ai)
2. Click **"Sign In"** in the top right
3. Choose your sign-in method (Google is easiest)
4. Once logged in, click your profile icon (top right)
5. Click **"Keys"**
6. Click **"Create Key"**
7. Name it `StaffLens`
8. Click **"Create"**
9. **COPY THE KEY** immediately (starts with `sk-or-`)
10. Save it somewhere safe

**Add Credits:**
1. Click **"Credits"** in the OpenRouter dashboard
2. Add $5-10 to start (you can add more later)
3. Each interview costs roughly $0.01 or less

---

## ⚙️ Step 6: Configure the Bot

### 6.1 Create Your .env File

The `.env` file holds all your secret keys and settings.

1. In the StaffLens folder, find the file called `.env.example`
2. Make a copy of it:
   - Windows: Right-click → Copy, then Right-click → Paste
   - Or in terminal: `copy .env.example .env` (Windows) or `cp .env.example .env` (Mac/Linux)
3. Rename the copy to `.env` (just `.env`, no other extension)
4. Open `.env` in a text editor (Notepad, VS Code, etc.)

### 6.2 Fill In Your Values

Edit the `.env` file to look like this (replace the placeholder values with YOUR actual values):

```env
# ===========================================
# REQUIRED - Discord Bot Configuration
# ===========================================

# Paste your Discord bot token from Step 1.3 (the long random string)
DISCORD_TOKEN=MTIzNDU2Nzg5MDEyMzQ1Njc4OQ.XXXXXX.XXXXXXXXXXXXXXXXXXXXXXXX

# We'll get this in Step 7 - leave blank for now
REPORT_CHANNEL_ID=

# ===========================================
# REQUIRED - API Keys
# ===========================================

# Paste your Deepgram API key from Step 5.1
DEEPGRAM_API_KEY=your_deepgram_key_here

# Paste your OpenRouter API key from Step 5.2 (starts with sk-or-)
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# AI model to use (Claude 3 Haiku recommended - fast and reliable)
OPENROUTER_MODEL=anthropic/claude-3-haiku

# ===========================================
# OPTIONAL - Customization
# ===========================================

# The role name that triggers the interview (must match EXACTLY!)
APPLICANT_ROLE_NAME=Applicant

# Minimum score (1-100) to be marked as "Recommended" 
FIT_THRESHOLD=70

# Command prefix for bot commands
COMMAND_PREFIX=!
```

**Save the file.**

---

## 🏠 Step 7: Setup Your Discord Server

### 7.1 Enable Developer Mode

Developer Mode lets you copy IDs (unique numbers) for channels and users.

1. Open Discord
2. Click the **gear icon** (User Settings) at the bottom left, next to your username
3. In the left sidebar, scroll down and click **"Advanced"**
4. Toggle ON **"Developer Mode"**
5. Close settings

### 7.2 Create the Applicant Role

This is the role that will trigger interviews. Anyone with this role who joins a voice channel will be interviewed.

1. Go to your Discord server
2. Click the **server name** at the top → **"Server Settings"**
3. In the left sidebar, click **"Roles"**
4. Click **"Create Role"**
5. Set the name to exactly: `Applicant` (must match your .env file!)
6. Give it a noticeable color so applicants stand out
7. Click **"Save Changes"**

### 7.3 Create the Reports Channel

This is where the bot will post interview reports for your staff.

1. Create a new **text channel** (click the + next to "Text Channels")
2. Name it `staff-reports` (or whatever you prefer)
3. Make it **private** so only staff can see it:
   - Click the gear icon next to the channel name
   - Go to "Permissions"
   - Turn OFF "View Channel" for @everyone
   - Turn ON "View Channel" for your staff/admin roles
4. **Get the Channel ID:**
   - Right-click the channel name
   - Click **"Copy Channel ID"** (this only appears if Developer Mode is on)
5. Paste this number into your `.env` file as `REPORT_CHANNEL_ID`:

```env
REPORT_CHANNEL_ID=1234567890123456789
```

(Your number will be different—it's usually 18-19 digits)

### 7.4 Make Sure the Bot Can Post

1. Go to your `#staff-reports` channel settings (gear icon)
2. Click "Permissions"
3. Click "Add members or roles"
4. Add your bot (StaffLens)
5. Enable these permissions for the bot:
   - ✅ View Channel
   - ✅ Send Messages
   - ✅ Embed Links

---

## 🎨 Step 8: Customize the Interview (IMPORTANT!)

This is the fun part! You can customize what the AI asks about to match YOUR community.

### 8.1 Open the Config File

In the StaffLens folder, find **`interview-config.md`** and open it in any text editor.

This file tells the AI:
- What your server is called
- What your community is about
- What topics to ask about
- What personality traits you care about
- What red flags to watch for
- The tone/style of the interview

### 8.2 Fill In Your Community Info

Here's an example for a **Gaming Community:**

```markdown
## Community Info

**Server Name:** Epic Gamers United

**Community Type:** Competitive gaming community focused on teamwork and improvement

**What We Value:**
- Good sportsmanship and not being toxic
- Showing up for scheduled events
- Helping newer players improve
- Active participation in voice chat
- Having fun while taking competition seriously
```

Here's an example for an **Art Community:**

```markdown
## Community Info

**Server Name:** Creative Corner

**Community Type:** Digital art and illustration community

**What We Value:**
- Constructive criticism and growth mindset
- Supporting fellow artists
- Participating in art challenges
- Sharing resources and tutorials
- Respecting all skill levels
```

### 8.3 Define What to Ask About

Tell the AI what topics matter for YOUR community:

```markdown
## Interview Focus Areas

**Primary Topics to Explore:**
- Their experience with [your community's focus]
- How they handle [common situations in your community]
- What they're looking for in a community
- How active they plan to be
- Their past community experiences

**Personality Traits We Care About:**
- [Trait 1 that matters to you]
- [Trait 2 that matters to you]
- [Trait 3 that matters to you]

**Red Flags to Watch For:**
- [Behavior you want to avoid]
- [Another bad sign]
- [Deal-breaker behavior]
```

### 8.4 Set the Interview Tone

```markdown
## Interview Style

**Tone:** Casual and friendly, like talking to a potential new friend

**Special Instructions:**
- Use [your community's] terminology if they seem familiar
- Ask about [specific interests related to your community]
- Keep it relaxed, not like a job interview
```

### 8.5 Save the File

That's it! The bot reads this file every time it starts an interview, so your changes take effect immediately (no restart needed).

**Tips:**
- Be specific! "Friendly" is vague, but "Good sport who doesn't rage quit" is clear
- Include 4-6 things in each section—don't overwhelm the AI
- The AI won't read these as a checklist; it weaves them into natural conversation

---

## 🚀 Step 9: Run the Bot

### 9.1 Start the Bot

Open a terminal/command prompt in the StaffLens folder:

```bash
# Navigate to the folder (adjust path as needed)
cd C:\StaffLens

# Activate the virtual environment (if you made one)
venv\Scripts\activate          # Windows
# OR
source venv/bin/activate       # Mac/Linux

# Run the bot
python bot.py
```

### 8.2 What Success Looks Like

You should see output similar to this:

```
2026-01-25 12:00:00 | INFO     | stafflens | Loading cogs...
2026-01-25 12:00:00 | INFO     | stafflens.voice | Voice cog loaded - Conversational AI interviewer ready
2026-01-25 12:00:00 | INFO     | stafflens | Loaded cog: src.cogs.voice
2026-01-25 12:00:00 | INFO     | stafflens | Loaded cog: src.cogs.admin
2026-01-25 12:00:00 | INFO     | stafflens | Database initialized
2026-01-25 12:00:01 | INFO     | stafflens | Logged in as StaffLens#1234 (ID: 123456789012345678)
2026-01-25 12:00:01 | INFO     | stafflens | Connected to 1 guild(s)
2026-01-25 12:00:01 | INFO     | stafflens | Report channel ID: 1234567890123456789
2026-01-25 12:00:01 | INFO     | stafflens | Applicant role: Applicant
2026-01-25 12:00:01 | INFO     | stafflens | ------
```

**Check Discord:** Your bot should now show as **Online** with a green dot!

### 8.3 Keeping the Bot Running

- The bot runs as long as the terminal window stays open
- To stop the bot: Press `Ctrl+C` in the terminal
- Closing the terminal window will also stop the bot
- For 24/7 operation, you'd need to host it on a VPS or cloud server

---

## 🧪 Step 10: Test Everything

### Quick Test: Check Bot Status

In any Discord channel where the bot can see messages, type:

```
!status
```

The bot should reply with its current configuration, including:
- Applicant role name
- Fit threshold
- Active sessions
- Report channel

### Full Interview Test

1. **Create a test applicant:**
   - Right-click yourself (or a friend) in the server member list
   - Click **"Roles"**
   - Add the **"Applicant"** role

2. **Join any voice channel**
   - The bot should automatically join within 2-3 seconds
   - You'll see a message in the terminal: "Starting conversational interview..."

3. **The bot will greet you!**
   - You'll hear the bot speak (TTS) a friendly greeting
   - You'll also see text messages in the report channel (accessibility)

4. **Have a conversation**
   - Talk naturally—the bot is AI-powered and responds to what you actually say
   - After you stop talking for 5 seconds, the bot will respond
   - The conversation continues until the AI decides it has enough info

5. **End the interview**
   - Either leave the voice channel OR
   - The AI will naturally wrap up after 6-8 exchanges

6. **Check your #staff-reports channel**
   - A detailed report embed should appear!
   - It includes scores, strengths, concerns, recommendation, and more

---

## 📝 Commands Reference

All commands use the `!` prefix by default (customizable in .env)

### General Commands

| Command | Description | Who Can Use |
|---------|-------------|-------------|
| `!status` | Shows bot config, active sessions, and stats | Everyone |
| `!testvoice` | Verifies voice cog is loaded and ready | Everyone |

### Staff Commands (Require Manage Channels)

| Command | Description |
|---------|-------------|
| `!sessions` | Lists all active interview sessions |
| `!endinterview` | Manually ends the interview in your current voice channel |

### Manager Commands (Require Manage Server)

| Command | Description |
|---------|-------------|
| `!history` | Shows last 10 interviews |
| `!history 25` | Shows last 25 interviews |
| `!interview 5` | Shows full details of interview #5 |
| `!transcript 5` | Downloads full transcript of interview #5 |

### Admin Commands (Require Administrator)

| Command | Description |
|---------|-------------|
| `!reanalyze 5` | Re-runs AI analysis on interview #5 |
| `!setrole Candidate` | Changes trigger role to "Candidate" |
| `!setthreshold 75` | Changes recommendation threshold to 75 |

---

## 🤖 How the AI Interview Works

### The Conversation Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS AI INTERVIEW FLOW                     │
└─────────────────────────────────────────────────────────────────────┘

    ┌───────────────┐
    │   Applicant   │
    │  joins voice  │
    │    channel    │
    └───────┬───────┘
            │
            ▼
    ┌───────────────┐
    │   Bot joins   │
    │  & generates  │
    │ AI greeting   │
    └───────┬───────┘
            │
            ▼
    ┌───────────────┐
    │  Bot speaks   │──────► Text displayed in
    │  via TTS +    │        report channel
    │  shows text   │        (accessibility)
    └───────┬───────┘
            │
            ▼
    ┌───────────────┐
    │   Applicant   │
    │    speaks     │◄──────┐
    └───────┬───────┘       │
            │               │
            ▼               │
    ┌───────────────┐       │
    │  5 seconds    │       │      CONVERSATION
    │  of silence   │       │         LOOP
    │   detected    │       │
    └───────┬───────┘       │
            │               │
            ▼               │
    ┌───────────────┐       │
    │  Transcribe   │       │
    │  via Deepgram │       │
    └───────┬───────┘       │
            │               │
            ▼               │
    ┌───────────────┐       │
    │ AI generates  │───────┘
    │ next response │
    │ (OpenRouter)  │
    └───────┬───────┘
            │
            │ After 6-8 exchanges, AI ends interview
            ▼
    ┌───────────────┐
    │   Compile     │
    │  transcript   │
    │  for analysis │
    └───────┬───────┘
            │
            ▼
    ┌───────────────┐
    │  AI Analyzes  │──────────────────────────┐
    │   (Gemini 3   │                          │
    │    Flash)     │    PSYCHOLOGICAL         │
    └───────┬───────┘    ASSESSMENT:           │
            │            • Communication       │
            │            • Problem-solving     │
            │            • Confidence          │
            │            • Emotional IQ        │
            │            • Cultural fit        │
            │            • Red flags           │
            ▼                                  │
    ┌───────────────┐◄─────────────────────────┘
    │   Generate    │
    │    report     │
    │    embed      │
    └───────┬───────┘
            │
            ▼
    ┌───────────────┐
    │    Post to    │
    │ #staff-reports│
    │   channel     │
    └───────────────┘
```

### What the AI Evaluates

| Trait | What It Measures | Score Range |
|-------|------------------|-------------|
| **Communication Clarity** | Can they articulate thoughts clearly? Good sentence structure? Coherent ideas? | 1-10 |
| **Problem-Solving** | Evidence of analytical thinking, learning from failures, systematic approaches | 1-10 |
| **Confidence** | Do they speak with conviction? Decisive but not arrogant? | 1-10 |
| **Emotional Regulation** | How do they handle tough questions? Stay composed under pressure? | 1-10 |
| **Cultural Fit** | Team player? Aligns with collaborative, growth-oriented mindset? | 1-10 |

### Red Flags It Watches For

The AI is specifically trained to watch for:

- 🚩 **Evasion or deflection** — Avoiding questions, changing the subject
- 🚩 **Aggression or defensiveness** — Getting hostile when challenged
- 🚩 **Disengagement or disinterest** — One-word answers, seeming bored
- 🚩 **Inconsistencies** — Story doesn't add up, contradicting themselves
- 🚩 **Entitlement or arrogance** — Acting like they're above the process
- 🚩 **Blame-shifting** — Never taking responsibility for anything

---

## 📊 Understanding the Report

### Recommendation Levels

| Level | Emoji | Meaning |
|-------|-------|---------|
| **STRONG HIRE** | 🟢 | Exceptional candidate—move fast before someone else gets them |
| **HIRE** | ✅ | Solid candidate, recommend bringing them on |
| **LEAN HIRE** | 🟡 | Promising but some concerns—discuss as a team |
| **LEAN NO** | 🟠 | More concerns than strengths—probably pass |
| **NO HIRE** | ❌ | Clear issues identified—recommend passing |
| **STRONG NO** | 🔴 | Major red flags—definite pass |

### Report Sections

The report embed includes:

1. **Fit Score** — Overall score out of 100 with visual bar
2. **Trait Scores** — Individual scores for each trait
3. **Key Strengths** — What they did well
4. **Concerns** — Areas of concern
5. **Red Flags** — Serious issues (only if detected)
6. **Psychological Profile** — AI's personality assessment
7. **Culture Alignment** — How they'd fit your specific culture
8. **Evidence Quotes** — Direct quotes supporting the assessment
9. **Summary** — Executive summary for busy managers
10. **Recommendation Reasoning** — Why the AI made this call

---

## ❗ Troubleshooting

### Bot Won't Start

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'discord'` | Dependencies not installed | Run `pip install -r requirements.txt` |
| `Improper token has been passed` | Wrong bot token | Check `.env` — make sure there are no extra spaces or quotes around the token |
| `FileNotFoundError: .env` | .env file not created | Copy `.env.example` to `.env` and fill it in |
| `Invalid token` | Token is wrong or expired | Generate a new token in Discord Developer Portal |

### Bot Is Online But Doesn't Do Anything

| Issue | Cause | Solution |
|-------|-------|----------|
| Ignores commands | Missing MESSAGE CONTENT INTENT | Go to Discord Developer Portal → Bot → Enable MESSAGE CONTENT INTENT |
| No permissions | Bot role is too low | In Server Settings → Roles, drag the bot's role higher |
| Wrong prefix | Using wrong command prefix | Check `COMMAND_PREFIX` in `.env` (default is `!`) |

### Bot Doesn't Join Voice Channels

| Issue | Cause | Solution |
|-------|-------|----------|
| Nothing happens when applicant joins | Role name doesn't match | Check `APPLICANT_ROLE_NAME` in `.env` — must match EXACTLY (case-sensitive) |
| "Missing permissions" error | Voice permissions not set | Re-invite bot with Connect + Speak permissions |
| Joins but immediately leaves | FFmpeg not installed | See Step 3: Install FFmpeg |
| `ffmpeg was not found` | FFmpeg not in PATH | Restart terminal/computer after installing FFmpeg |

### No Report Appears

| Issue | Cause | Solution |
|-------|-------|----------|
| "Report channel not found" | Wrong channel ID | Get the correct ID: Right-click channel → Copy Channel ID |
| "Analysis failed" | API issue | Check OpenRouter has credits and API key is correct |
| Empty transcript | No audio captured | Make sure you actually spoke for more than a few seconds |

### Bot Speaks But You Can't Hear It

| Issue | Cause | Solution |
|-------|-------|----------|
| No audio at all | FFmpeg issue | Reinstall FFmpeg and restart your computer |
| Audio is robotic/corrupted | Edge-TTS issue | Try `pip install --upgrade edge-tts` |
| Audio cuts out | Network issue | Check your internet connection |

### Check the Logs

The terminal shows everything happening. Look for these log levels:
- `INFO` — Normal operation, good news
- `WARNING` — Something might be wrong but bot continues
- `ERROR` — Something broke, investigate this

---

## 📁 Project Structure

```
stafflens/
│
├── 📄 bot.py                 # Main entry point - run this to start
├── 📄 interview-config.md    # ⭐ CUSTOMIZE THIS - your community's interview focus
├── 📄 .env                   # YOUR config (DON'T SHARE THIS!)
├── 📄 .env.example           # Template showing what goes in .env
├── 📄 requirements.txt       # Python packages needed
├── 📄 README.md              # This file you're reading
├── 📄 LICENSE                # License terms
├── 📄 .gitignore             # Files Git should ignore
│
├── 📁 src/                   # Source code
│   │
│   ├── 📁 cogs/              # Bot features (modular)
│   │   ├── 📄 voice.py       # AI interviewer - TTS, recording, conversation
│   │   └── 📄 admin.py       # Admin commands
│   │
│   ├── 📁 services/          # External integrations
│   │   ├── 📄 transcription.py  # Deepgram speech-to-text
│   │   ├── 📄 analysis.py       # OpenRouter AI analysis
│   │   ├── 📄 tts.py            # Text-to-speech (Edge-TTS)
│   │   ├── 📄 database.py       # SQLite storage
│   │   └── 📄 questions.py      # Question bank (for reference)
│   │
│   └── 📁 utils/
│       └── 📄 embeds.py      # Discord embed builders
│
└── 📁 data/                  # Created automatically
    └── 📄 stafflens.db       # SQLite database
```

### What Each Key File Does

| File | Purpose |
|------|---------|
| `bot.py` | The main brain—initializes everything and starts the bot |
| `interview-config.md` | **Your customization file!** Edit this to change what the AI asks about |
| `voice.py` | The AI interviewer—handles conversations, TTS, recording |
| `admin.py` | All the staff commands like `!history` and `!status` |
| `transcription.py` | Sends audio to Deepgram, gets text back |
| `analysis.py` | Sends conversation to AI, gets psychological analysis |
| `tts.py` | Converts text to spoken audio |
| `database.py` | Saves and loads interview data from SQLite |
| `embeds.py` | Creates the beautiful report cards in Discord |

---

## 📜 License

MIT License with Attribution Clause

**For personal/non-commercial use:** Completely free, no strings attached!

**For commercial use:** You must credit **Chad Keith** as the original creator. This includes:
- Including "StaffLens by Chad Keith" in your about page, documentation, or marketing
- A link to this repository if publicly available

See [LICENSE](LICENSE) for full terms.

---

## 🙏 Credits & Support

**Created by [Chad Keith](https://github.com/chadkeith)**

If StaffLens helps your community, consider:
- ⭐ Starring this repo
- 🐛 Reporting bugs via Issues
- 💡 Suggesting features
- 🔀 Contributing via Pull Requests

---

**Built with ❤️ for communities that care about who they bring on board.**

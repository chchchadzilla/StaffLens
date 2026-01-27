---
description: AI rules derived by SpecStory from the project AI interaction history
globs: *
---

# StaffLens - Copilot Instructions

Fully autonomous AI-powered Discord bot that conducts natural voice conversations with applicants, then delivers comprehensive psychological assessments.

## Architecture Overview

```
bot.py                    # Entry point - StaffLens class with config & session tracking
src/cogs/                 # Discord command extensions (modular features)
  ├── voice.py            # Conversational AI interviewer - dynamic LLM responses, TTS, recording
  └── admin.py            # Admin commands (!history, !reanalyze, !status)
src/services/             # External integrations (stateless)
  ├── transcription.py    # Deepgram REST API for speech-to-text
  ├── analysis.py         # OpenRouter/Gemini analysis with workplace psychologist prompt
  ├── tts.py              # Edge-TTS for text-to-speech (bot voice)
  ├── questions.py        # Interview question bank (for reference, now secondary)
  └── database.py         # Async SQLite with aiosqlite
src/utils/
  └── embeds.py           # Discord embed builders for reports
```

## Critical Patterns

### Adding New Features
- **New commands**: Create a cog in `src/cogs/`, register in `bot.py:on_ready()`
- **New external API**: Create service in `src/services/`, inject via cog constructor
- **New embeds**: Add builder function to `src/utils/embeds.py`
- **Modify interview behavior**: Edit `INTERVIEWER_SYSTEM_PROMPT` in `voice.py`

### Data Flow (Conversational AI Interview)
1. `on_voice_state_update` detects applicant → creates `InterviewSession`
2. Bot connects to VC, initializes conversation history with system prompt
3. Bot gets initial greeting from LLM via OpenRouter
4. Conversation loop:
   - Bot speaks via TTS + displays text in channel (accessibility)
   - Records applicant using `discord.sinks.WaveSink`
   - 5-second silence detection triggers processing
   - Transcribes audio via Deepgram REST API
   - Sends conversation history to LLM for dynamic response
   - LLM naturally decides when interview is complete (`[INTERVIEW_COMPLETE]`)
5. Interview completes → full transcript sent to `AnalysisService`
6. Analysis via OpenRouter (Gemini 3 Flash) with workplace psychologist prompt
7. Results stored in SQLite, report embed posted to report channel

### Analysis Service Pattern
```python
# Always try local first, OpenRouter is fallback (see src/services/analysis.py)
result = await self._analyze_local(transcript)  # ConversaTrait endpoint
if not result:
    result = await self._analyze_openrouter(transcript)  # Gemini 3 Flash via OpenRouter
```

### Conversation Loop Pattern (voice.py)
```python
# Main interview loop
while session.is_active and not session.interview_complete:
    user_response = await self._record_until_silence(session)  # 5s silence threshold
    if user_response:
        session.conversation_history.append({"role": "user", "content": user_response})
        llm_response = await self._get_llm_response(session)  # OpenRouter call
        if "[INTERVIEW_COMPLETE]" in llm_response:
            session.interview_complete = True
        await self._speak_and_display(session, llm_response)  # TTS + text
```

## Key Commands

```bash
python bot.py                          # Run bot
pip install -r requirements.txt        # Install deps
cp .env.example .env                   # Create config
```

### Discord Commands
- `!testvoice` - Check if voice cog is loaded and TTS is working
- `!sessions` - List active interview sessions
- `!endinterview` - Manually end an interview in your current VC
- `!history [count]` - View recent interview history
- `!status` - Bot status and statistics

## Environment Variables (Required)

| Variable | Purpose |
|----------|---------|
| `DISCORD_TOKEN` | Bot authentication |
| `REPORT_CHANNEL_ID` | Where reports are posted |
| `DEEPGRAM_API_KEY` | Transcription service |
| `OPENROUTER_API_KEY` | AI analysis (Gemini 3 Flash) |
| `OPENROUTER_MODEL` | AI Model to use (default: google/gemini-3-flash-preview) |
| `APPLICANT_ROLE_NAME` | Role that triggers interviews (default: Applicant) |

## External Dependencies

- **FFmpeg**: Required for audio playback. Install via:
  - Windows: `choco install ffmpeg` or download from ffmpeg.org
  - Mac: `brew install ffmpeg`
  - Linux: `apt install ffmpeg`

## Conventions

- **Async everywhere**: All I/O uses `async/await` - use `aiohttp`, `aiosqlite`
- **Logging**: Use `logging.getLogger(\"stafflens.<module>\")` pattern
- **Config**: All settings via `os.getenv()` with sensible defaults
- **Embeds**: Use helper functions in `embeds.py`, never build raw embeds inline
- **Database**: Always use context manager pattern: `async with aiosqlite.connect(...)`
- **Py-cord**: Using py-cord (not discord.py) for `discord.sinks` voice recording support

## Analysis JSON Schema

The analysis service expects/returns this structure (see `ANALYSIS_PROMPT` in analysis.py):\
```json
{
  "scores": {"communication_clarity": 8, "problem_solving": 7, ...},
  "fit_score": 75,
  "strengths": ["Clear communicator", ...],
  "concerns": ["Lacks technical depth", ...],
  "red_flags": [],
  "evidence_quotes": {"positive": [...], "negative": [...]},
  "psychological_profile": "Candidate shows collaborative instincts...",
  "culture_alignment": "Strong fit for growth-oriented environment...",
  "summary": "...",
  "recommendation": "STRONG_HIRE|HIRE|LEAN_HIRE|LEAN_NO|NO_HIRE|STRONG_NO",
  "recommended": true
}
```

## DO's and DON'Ts

✅ **DO**: Use cogs for new Discord features, services for external APIs  
✅ **DO**: Store all config in `.env`, never hardcode credentials  
✅ **DO**: Use `_normalize_result()` when adding new analysis sources  
✅ **DO**: Add new question types to `questions.py` for different roles  
❌ **DON'T**: Block the event loop - always use async versions of libraries  
❌ **DON'T**: Skip the local endpoint check - ConversaTrait integration is intentional  
❌ **DON'T**: Modify `ANALYSIS_PROMPT` without updating the JSON schema handling  
❌ **DON'T**: Use discord.py features not in py-cord (they're different!)

## License

MIT with Attribution Clause - see LICENSE file.
Open source for non-commercial use. Commercial use requires attribution to Chad Keith.
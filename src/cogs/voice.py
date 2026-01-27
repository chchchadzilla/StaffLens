"""
Voice Cog - Conversational AI interviewer.

This cog handles:
- Joining voice channels when applicants enter
- Dynamic LLM-driven conversations (not preset questions)
- Silence detection (5 seconds) before sending to LLM
- TTS responses + text display for accessibility
- Custom interview focus loaded from interview-config.md
"""

import asyncio
import logging
import io
import tempfile
import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import discord
from discord.ext import commands
import aiohttp

from src.services.transcription import TranscriptionService
from src.services.analysis import AnalysisService
from src.services.tts import get_tts_service
from src.utils.embeds import create_report_embed

logger = logging.getLogger("stafflens.voice")

# Base system prompt template - community config gets inserted
INTERVIEWER_SYSTEM_PROMPT_TEMPLATE = """CRITICAL RULES - READ FIRST:
1. **KEEP IT SHORT** - Maximum 2 sentences per response. One brief reaction + one question. That's it.
2. **NO URLS OR LINKS** - Never include ANY URLs, websites, or web references.
3. **NO ROLEPLAY ACTIONS** - Never use *asterisk actions* like *clears throat*. Just speak.
4. **NO GREETINGS** - The applicant has already been greeted. Jump straight into your question.
5. **NO SYSTEM NOTES** - Never include [SYSTEM:], [NOTE:], [THINKING:], or any bracketed commentary. Your entire response is read aloud.

You are an AI interviewer for a Discord community conducting a voice interview.

{community_context}

YOUR GOALS:
1. Make the applicant comfortable while gathering useful information
2. Assess their personality, communication skills, and culture fit
3. Understand their background and what they can contribute

RESPONSE FORMAT (STRICT):
- Sentence 1: Brief reaction to what they said (optional)
- Sentence 2: Your next question
- THAT'S IT. No more. No paragraphs. No lists. No elaboration.
- DO NOT say "Hello", "Hi", "Welcome", or any greeting - the applicant was already greeted.

EXAMPLE GOOD RESPONSES:
- "What got you interested in joining this community?"
- "Nice, sounds like you've got solid experience. How do you usually handle disagreements with teammates?"
- "Got it. What are you hoping to get out of joining this community?"

EXAMPLE BAD RESPONSES (TOO LONG):
- "That's really interesting! It sounds like you have a lot of experience in that area. I can see how that would be valuable. Let me ask you about..." (TOO MANY SENTENCES)
- "Hello! Welcome to the interview! So glad to have you here today. Let me start by asking..." (NO GREETINGS - already done)

GUIDELINES:
- Ask ONE question at a time
- React naturally but BRIEFLY
- If they give short answers, gently probe deeper
- You MUST ask at least 5-6 questions before wrapping up
- Only wrap up after substantial conversation (minimum 6 exchanges)

When ready to end (ONLY after 6+ questions), include "[INTERVIEW_COMPLETE]" at the end.

Remember: This is VOICE. Keep it conversational and SHORT. NO GREETINGS. DO NOT END EARLY."""


def load_interview_config() -> str:
    """
    Load custom interview configuration from interview-config.md.
    
    Returns community context string to inject into system prompt.
    """
    config_path = Path("interview-config.md")
    
    if not config_path.exists():
        logger.warning("interview-config.md not found, using default config")
        return """CONTEXT:
- This is a general Discord community
- You're having a voice conversation (keep responses concise and natural for speech)
- The applicant can hear you speak, so be warm and conversational"""
    
    try:
        content = config_path.read_text(encoding="utf-8")
        
        # Parse the markdown to extract key sections
        context_parts = []
        
        # Extract server name
        if "**Server Name:**" in content:
            for line in content.split("\n"):
                if "**Server Name:**" in line:
                    server_name = line.replace("**Server Name:**", "").strip()
                    if server_name:
                        context_parts.append(f"- This is the {server_name} Discord server")
                    break
        
        # Extract community type
        if "**Community Type:**" in content:
            for line in content.split("\n"):
                if "**Community Type:**" in line:
                    comm_type = line.replace("**Community Type:**", "").strip()
                    if comm_type:
                        context_parts.append(f"- Community focus: {comm_type}")
                    break
        
        # Extract what we value
        if "**What We Value:**" in content:
            start = content.find("**What We Value:**")
            end = content.find("---", start + 1)
            if end == -1:
                end = content.find("## Interview Focus", start)
            if start != -1:
                values_section = content[start:end] if end != -1 else content[start:start+500]
                values = []
                for line in values_section.split("\n"):
                    line = line.strip()
                    if line.startswith("- ") and len(line) > 3:
                        values.append(line[2:])
                if values:
                    context_parts.append(f"- Community values: {', '.join(values[:5])}")
        
        # Extract primary topics
        if "**Primary Topics to Explore:**" in content:
            start = content.find("**Primary Topics to Explore:**")
            end = content.find("**Personality Traits", start)
            if end == -1:
                end = start + 600
            topics_section = content[start:end]
            topics = []
            for line in topics_section.split("\n"):
                line = line.strip()
                if line.startswith("- ") and len(line) > 3:
                    topics.append(line[2:])
            if topics:
                context_parts.append(f"\nTOPICS TO EXPLORE:\n" + "\n".join(f"- {t}" for t in topics[:6]))
        
        # Extract personality traits
        if "**Personality Traits We Care About:**" in content:
            start = content.find("**Personality Traits We Care About:**")
            end = content.find("**Red Flags", start)
            if end == -1:
                end = start + 500
            traits_section = content[start:end]
            traits = []
            for line in traits_section.split("\n"):
                line = line.strip()
                if line.startswith("- ") and len(line) > 3:
                    traits.append(line[2:])
            if traits:
                context_parts.append(f"\nTRAITS WE'RE LOOKING FOR:\n" + "\n".join(f"- {t}" for t in traits[:5]))
        
        # Extract red flags
        if "**Red Flags to Watch For:**" in content:
            start = content.find("**Red Flags to Watch For:**")
            end = content.find("---", start + 1)
            if end == -1:
                end = content.find("## Interview Style", start)
            if end == -1:
                end = start + 500
            flags_section = content[start:end]
            flags = []
            for line in flags_section.split("\n"):
                line = line.strip()
                if line.startswith("- ") and len(line) > 3:
                    flags.append(line[2:])
            if flags:
                context_parts.append(f"\nRED FLAGS TO WATCH FOR:\n" + "\n".join(f"- {t}" for t in flags[:5]))
        
        # Extract tone/style
        if "**Tone:**" in content:
            for line in content.split("\n"):
                if "**Tone:**" in line:
                    tone = line.replace("**Tone:**", "").strip()
                    if tone:
                        context_parts.append(f"\nINTERVIEW TONE: {tone}")
                    break
        
        # Extract special instructions
        if "**Special Instructions:**" in content:
            start = content.find("**Special Instructions:**")
            end = content.find("---", start + 1)
            if end == -1:
                end = content.find("## About", start)
            if end == -1:
                end = start + 400
            instr_section = content[start:end]
            instructions = []
            for line in instr_section.split("\n"):
                line = line.strip()
                if line.startswith("- ") and len(line) > 3:
                    instructions.append(line[2:])
            if instructions:
                context_parts.append(f"\nSPECIAL INSTRUCTIONS:\n" + "\n".join(f"- {i}" for i in instructions[:4]))
        
        if context_parts:
            result = "CONTEXT:\n" + "\n".join(context_parts)
            result += "\n- You're having a voice conversation (keep responses concise and natural for speech)"
            result += "\n- The applicant can hear you speak, so be warm and conversational"
            logger.info("Loaded custom interview config from interview-config.md")
            return result
        else:
            logger.warning("Could not parse interview-config.md, using defaults")
            return """CONTEXT:
- This is a general Discord community
- You're having a voice conversation (keep responses concise and natural for speech)
- The applicant can hear you speak, so be warm and conversational"""
            
    except Exception as e:
        logger.error(f"Error loading interview-config.md: {e}")
        return """CONTEXT:
- This is a general Discord community  
- You're having a voice conversation (keep responses concise and natural for speech)
- The applicant can hear you speak, so be warm and conversational"""


def get_system_prompt() -> str:
    """Build the full system prompt with custom community config."""
    community_context = load_interview_config()
    return INTERVIEWER_SYSTEM_PROMPT_TEMPLATE.format(community_context=community_context)


# Responses that indicate "yes, I'm done talking"
AFFIRMATIVE_RESPONSES = {
    "yeah", "yes", "yup", "yep", "yap", "yuh-huh", "uh-huh", "sure", "mmhmm", "mhm",
    "bet", "for sure", "cool", "tight", "you got it", "yuppers", "yip", "oh yeah",
    "hell yeah", "hella", "lets go", "let's go", "lets do it", "let's do it", 
    "send it", "next", "do it", "hit me", "do it up", "go on then", "bring it on",
    "bring it", "waiting on you", "affirmative", "absolutely", "of course",
    "i'm waiting on you", "i've been ready", "i was born ready", "i done been ready",
    "well go on then", "whatever", "i don't care", "do whatever you want",
    "whatever's clever", "leggo", "lessgo", "try and stop me", "cha-ching",
    "ka-ching", "i thought you'd never ask", "do it then", "that's it", "that's all",
    "i'm done", "i'm finished", "that's everything", "nothing else", "nope that's it",
    "all good", "good to go", "ready", "go ahead", "proceed", "continue", "move on",
    "next question", "fire away", "shoot", "go for it", "yessir", "yes sir", "yes ma'am",
    "yessum", "aye", "aye aye", "roger", "roger that", "copy", "copy that", "10-4",
    "affirmative", "indeed", "correct", "right", "exactly", "precisely", "certainly",
    "definitely", "surely", "okay", "ok", "k", "kk", "alright", "aight", "ight",
}

# Responses that indicate "no, I'm still talking / let me continue"
NEGATIVE_RESPONSES = {
    "wait", "hold up", "hold on", "stop", "lemme think", "let me think",
    "i need to think", "i'm still talking", "let me redo", "let me re-do",
    "can you start over", "start over", "what the fuck", "wtf", "ah man", "aw man",
    "mannnn", "let me finish", "i didn't finish", "i didnt finish", "you cut me off",
    "you stepped on me", "you're stepping on my toes", "you're cutting me off",
    "you just cut me off", "again", "stop doing that", "don't talk til i'm finished",
    "i'm not done", "not done yet", "not yet", "hang on", "one sec", "one second",
    "gimme a sec", "give me a second", "no", "nope", "nah", "naw", "negative",
    "not quite", "actually", "well actually", "um", "uh", "uhh", "umm", "hmm",
    "let me", "i want to", "i wanna", "there's more", "also", "and another thing",
    "one more thing", "but wait", "oh and", "plus", "additionally", "furthermore",
    "more to say", "not finished", "still got more", "keep going", "i'll keep going",
    "continuing", "as i was saying", "anyway", "anywho", "so anyway", "back to",
}

# Trigger phrases that signal "move to next question" (must be followed by silence)
NEXT_QUESTION_TRIGGERS = {
    "next question", "next question please", "next", "go to the next question",
    "ready for the next question", "ready for next question", "next one",
    "next one please", "that's my answer", "i'm ready", "im ready",
}

# Reminder message if they go silent for too long without saying "next question"
SILENCE_REMINDER = "Take your time! When you're finished with your answer, just say 'next question' and I'll move on."


def contains_next_question_trigger(text: str) -> bool:
    """Check if the text ends with a 'next question' trigger phrase."""
    if not text:
        return False
    text_lower = text.lower().strip()
    # Check if text ends with any trigger phrase
    for trigger in NEXT_QUESTION_TRIGGERS:
        if text_lower.endswith(trigger):
            return True
        # Also check if trigger is in the last ~50 chars (in case of trailing filler)
        if len(text_lower) > len(trigger) and trigger in text_lower[-50:]:
            return True
    return False


def strip_trigger_phrase(text: str) -> str:
    """Remove the 'next question' trigger phrase from the end of text."""
    if not text:
        return text
    text_clean = text.strip()
    text_lower = text_clean.lower()
    for trigger in sorted(NEXT_QUESTION_TRIGGERS, key=len, reverse=True):  # Longest first
        if text_lower.endswith(trigger):
            return text_clean[:-len(trigger)].strip()
    return text_clean


def is_affirmative(text: str) -> bool:
    """Check if the response indicates they're done talking."""
    if not text:
        return False
    text_lower = text.lower().strip()
    # Check for exact matches
    if text_lower in AFFIRMATIVE_RESPONSES:
        return True
    # Check if any affirmative phrase is in the response
    for phrase in AFFIRMATIVE_RESPONSES:
        if phrase in text_lower:
            return True
    return False


def is_negative(text: str) -> bool:
    """Check if the response indicates they want to keep talking."""
    if not text:
        return False
    text_lower = text.lower().strip()
    # Check for exact matches
    if text_lower in NEGATIVE_RESPONSES:
        return True
    # Check if any negative phrase is in the response
    for phrase in NEGATIVE_RESPONSES:
        if phrase in text_lower:
            return True
    return False


class InterviewSession:
    """Represents an active conversational interview session."""

    def __init__(self, channel: discord.VoiceChannel, applicant: discord.Member, text_channel: discord.TextChannel):
        self.channel = channel
        self.applicant = applicant
        self.guild = channel.guild
        self.text_channel = text_channel  # For accessibility text display
        self.started_at = datetime.utcnow()
        
        # Voice connection
        self.connection: Optional[discord.VoiceClient] = None
        
        # Recording state
        self.sink: Optional[discord.sinks.WaveSink] = None
        self.is_recording = False
        self.last_audio_size = 0
        self.silence_start: Optional[float] = None
        
        # Conversation state
        self.conversation_history: list[dict] = []
        self.is_active = True
        self.is_speaking = False  # Bot is currently speaking
        self.interview_complete = False
        
        # Transcript for final analysis
        self.transcript_lines: list[str] = []
        
        # Report tracking
        self.report_sent = False  # Prevent duplicate reports


class VoiceCog(commands.Cog):
    """
    Conversational AI interviewer cog.
    """

    def __init__(self, bot):
        self.bot = bot
        self.transcription = TranscriptionService()
        self.analysis = AnalysisService()
        self.tts = get_tts_service()
        
        # Silence detection settings
        self.silence_threshold = 2.0  # 2 seconds of silence before sending to LLM
        self.check_interval = 0.3  # Check audio every 300ms
        
        # OpenRouter settings - use :nitro suffix for maximum throughput
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        # Claude Haiku 4.5:nitro for fastest real-time conversation
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-haiku-4.5:nitro")

    async def handle_voice_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        """Handle voice state changes - called from bot.py."""
        logger.info(f"Voice update: {member.display_name} | {before.channel} -> {after.channel}")
        
        if member.bot:
            return

        # Check for applicant role
        applicant_role = discord.utils.get(
            member.guild.roles,
            name=self.bot.applicant_role_name,
        )
        
        if not applicant_role or applicant_role not in member.roles:
            return

        logger.info(f"Applicant detected: {member.display_name}")

        # Applicant joined a voice channel
        if after.channel and (not before.channel or before.channel != after.channel):
            # Check if there's already an active interview in this channel
            if after.channel.id in self.bot.active_sessions:
                logger.info(f"Interview already in progress in {after.channel.name}, ignoring {member.display_name}")
                return
            await self._start_interview(member, after.channel)

        # Applicant left
        elif before.channel and (not after.channel or before.channel != after.channel):
            await self._handle_applicant_leave(member, before.channel)

    async def _start_interview(self, applicant: discord.Member, channel: discord.VoiceChannel):
        """Start a conversational interview session."""
        if channel.id in self.bot.active_sessions:
            logger.info(f"Already interviewing in {channel.name}")
            return

        logger.info(f"Starting conversational interview with {applicant.display_name}")

        # Find a text channel for accessibility (use report channel or first available)
        text_channel = self.bot.get_report_channel()
        if not text_channel:
            text_channel = channel.guild.text_channels[0] if channel.guild.text_channels else None

        session = InterviewSession(channel, applicant, text_channel)

        try:
            session.connection = await channel.connect()
            logger.info(f"Connected to {channel.name}")
            
            self.bot.active_sessions[channel.id] = session
            
            # Start the conversational interview
            asyncio.create_task(self._run_conversation(session))

        except Exception as e:
            logger.error(f"Failed to start interview: {e}", exc_info=True)
            if session.connection:
                await session.connection.disconnect()
            self.bot.active_sessions.pop(channel.id, None)

    async def _run_conversation(self, session: InterviewSession):
        """Run the conversational interview loop."""
        import random
        
        try:
            await asyncio.sleep(2)  # Brief pause before starting
            
            # Initialize conversation with system prompt (loads custom config)
            system_prompt = get_system_prompt()
            session.conversation_history = [
                {"role": "system", "content": system_prompt}
            ]
            
            # === FORMAL INTRODUCTION ===
            intro_message = (
                f"Hello {session.applicant.display_name}! Welcome. "
                f"This is the first stage of your application interview. "
                f"I'll be asking you a few questions to get to know you better. "
                f"Keep in mind, I'm an AI bot, so to make this easier on both of us, "
                f"at the end of every answer, please say 'next question', and I'll know to move on. "
                f"Take as long as you need with your answers! "
                f"If you have any questions after we're done, please direct them to the person who set up this interview."
            )
            await self._speak_and_display(session, intro_message)
            await asyncio.sleep(1.5)
            
            # First question - directly ask, no second greeting
            await self._speak_and_display(session, "Alright, let's begin. First question:", add_to_transcript=False)
            await asyncio.sleep(0.3)
            
            first_question = await self._get_llm_response(session, is_initial=True)
            if first_question:
                await self._speak_and_display(session, first_question)
            
            # Main conversation loop
            accumulated_response = ""  # For accumulating response until "next question"
            question_number = 1  # Track question count
            reminder_given = False  # Track if we've reminded them about "next question"
            
            while session.is_active and not session.interview_complete:
                # Record until silence is detected (short chunks)
                user_response = await self._record_until_silence(session)
                
                if not session.is_active:
                    break
                
                if user_response:
                    # Accumulate the response
                    if accumulated_response:
                        accumulated_response += " " + user_response
                    else:
                        accumulated_response = user_response
                    
                    logger.info(f"Applicant said: {user_response[:100]}...")
                    reminder_given = False  # Reset reminder flag since they spoke
                    
                    # Check if they said "next question" (trigger to move on)
                    if contains_next_question_trigger(user_response):
                        logger.info("Detected 'next question' trigger, getting LLM response...")
                        
                        # Strip the trigger phrase from the response
                        accumulated_response = strip_trigger_phrase(accumulated_response)
                        
                        if accumulated_response:
                            session.conversation_history.append({
                                "role": "user",
                                "content": accumulated_response
                            })
                            session.transcript_lines.append(f"[{session.applicant.display_name}]: {accumulated_response}")
                            
                            # Get LLM response (with timing)
                            import time as _time
                            _start = _time.time()
                            llm_response = await self._get_llm_response(session)
                            logger.info(f"LLM response took {_time.time() - _start:.1f}s")
                            
                            if llm_response:
                                # Check if interview is complete
                                # BUT enforce minimum 5 questions before allowing end
                                if "[INTERVIEW_COMPLETE]" in llm_response:
                                    llm_response = llm_response.replace("[INTERVIEW_COMPLETE]", "").strip()
                                    if question_number >= 5:
                                        session.interview_complete = True
                                        logger.info(f"Interview ending after {question_number} questions")
                                    else:
                                        # LLM tried to end early - ignore and continue
                                        logger.warning(f"LLM tried to end at question {question_number}, forcing continue")
                                
                                if not session.interview_complete:
                                    # Announce next question (avoid saying 'next question' which could trigger detection)
                                    question_number += 1
                                    await self._speak_and_display(session, "Great, thanks for that. Here's another one:", add_to_transcript=False)
                                    await asyncio.sleep(0.3)
                                
                                await self._speak_and_display(session, llm_response)
                            
                            # Reset accumulator for next question
                            accumulated_response = ""
                    # Otherwise, they didn't say "next question" yet - keep listening
                    # (the loop will continue and record more)
                    
                else:
                    # No response detected (silence timeout)
                    if accumulated_response and not reminder_given:
                        # They said something but went quiet without saying "next question"
                        await self._speak_and_display(session, SILENCE_REMINDER, add_to_transcript=False)
                        reminder_given = True
                    elif not accumulated_response and len(session.conversation_history) < 4:
                        # They haven't said anything yet - gentle prompt
                        await self._speak_and_display(session, "Take your time! I'm here whenever you're ready.", add_to_transcript=False)
            
            # Interview complete
            if session.is_active:
                logger.info(f"Interview complete, processing... (transcript lines: {len(session.transcript_lines)})")
                
                # Formal closing
                closing_message = (
                    f"That concludes our interview, {session.applicant.display_name}. "
                    f"Thank you so much for taking the time to speak with me today. "
                    f"I'll put together a summary for the team to review. "
                    f"If you have any questions, please reach out to the person who set up this interview. "
                    f"Take care!"
                )
                await self._speak_and_display(session, closing_message)
                await asyncio.sleep(1)
                
                # Generate and post the report
                await self._complete_interview(session)
                
        except asyncio.CancelledError:
            logger.info("Interview cancelled")
        except Exception as e:
            logger.error(f"Conversation error: {e}", exc_info=True)
        finally:
            await self._cleanup_session(session)

    async def _record_until_silence(self, session: InterviewSession, short_timeout: bool = False) -> Optional[str]:
        """Record audio until silence is detected, then transcribe.
        
        Args:
            session: The interview session
            short_timeout: If True, use shorter timeouts (for confirmation responses)
        """
        if not session.connection or session.is_speaking:
            return None
        
        # Use shorter thresholds for confirmation responses
        silence_threshold = 2.0 if short_timeout else self.silence_threshold
        no_response_timeout = 8.0 if short_timeout else 30.0
        
        try:
            # Start recording
            session.sink = discord.sinks.WaveSink()
            session.connection.start_recording(
                session.sink,
                self._on_recording_done,
                session.channel.id,
            )
            session.is_recording = True
            session.last_audio_size = 0
            session.silence_start = None
            
            logger.debug("Started recording, waiting for speech...")
            
            # Monitor for silence
            has_received_audio = False
            
            while session.is_active and session.is_recording:
                await asyncio.sleep(self.check_interval)
                
                # Get current audio size
                current_size = self._get_audio_size(session)
                
                if current_size > session.last_audio_size:
                    # Audio is being received
                    has_received_audio = True
                    session.silence_start = None
                    session.last_audio_size = current_size
                else:
                    # No new audio
                    if has_received_audio:
                        # They were talking but stopped
                        if session.silence_start is None:
                            session.silence_start = time.time()
                        elif time.time() - session.silence_start >= silence_threshold:
                            # Silence threshold reached after speaking
                            if not short_timeout:
                                logger.info(f"{silence_threshold}s silence detected, processing...")
                            break
                    else:
                        # Haven't started talking yet - give them time
                        if session.silence_start is None:
                            session.silence_start = time.time()
                        elif time.time() - session.silence_start >= no_response_timeout:
                            # Timeout with no response at all
                            if not short_timeout:
                                logger.info(f"No response for {no_response_timeout} seconds")
                            break
            
            # Stop recording
            if session.is_recording and session.connection:
                session.connection.stop_recording()
                session.is_recording = False
            
            await asyncio.sleep(0.3)  # Brief pause for data
            
            # Transcribe if we got audio
            if has_received_audio and session.sink:
                audio_bytes = self._extract_user_audio(session)
                if audio_bytes:
                    result = await self.transcription.transcribe_audio(audio_bytes)
                    if result and result.get("transcript"):
                        return result["transcript"].strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Recording error: {e}")
            if session.is_recording and session.connection:
                try:
                    session.connection.stop_recording()
                except:
                    pass
                session.is_recording = False
            return None

    def _get_audio_size(self, session: InterviewSession) -> int:
        """Get total audio data size from sink."""
        if not session.sink or not session.sink.audio_data:
            return 0
        
        total = 0
        for user_id, audio in session.sink.audio_data.items():
            member = session.guild.get_member(user_id)
            if member and member.bot:
                continue
            if audio.file:
                audio.file.seek(0, 2)  # Seek to end
                total += audio.file.tell()
        return total

    def _extract_user_audio(self, session: InterviewSession) -> Optional[bytes]:
        """Extract audio data from non-bot users."""
        if not session.sink or not session.sink.audio_data:
            return None
        
        combined = io.BytesIO()
        for user_id, audio in session.sink.audio_data.items():
            member = session.guild.get_member(user_id)
            if member and member.bot:
                continue
            if audio.file:
                audio.file.seek(0)
                combined.write(audio.file.read())
        
        return combined.getvalue() if combined.tell() > 0 else None

    async def _on_recording_done(self, sink, channel_id: int, *args):
        """Callback when recording stops. Must be async for py-cord."""
        # This callback is called from py-cord's thread via run_coroutine_threadsafe
        # The actual processing happens in _record_until_silence after we stop recording
        pass

    async def _get_llm_response(self, session: InterviewSession, is_initial: bool = False) -> Optional[str]:
        """Get a response from the LLM via OpenRouter with retry logic."""
        if not self.openrouter_key:
            logger.error("OpenRouter API key not configured")
            return None
        
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                messages = session.conversation_history.copy()
                
                if is_initial:
                    # Prompt for initial greeting
                    messages.append({
                        "role": "user",
                        "content": f"[SYSTEM: A new applicant named {session.applicant.display_name} has just joined the voice channel. Greet them warmly and begin the interview. Remember to keep it short since this will be spoken aloud.]"
                    })
                
                async with aiohttp.ClientSession() as http:
                    async with http.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.openrouter_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.openrouter_model,
                            "messages": messages,
                            "max_tokens": 200,  # Keep responses short for speech
                            "temperature": 0.7,
                            # SPEED OPTIMIZATION: Route to lowest latency provider
                            "provider": {
                                "sort": "latency",  # Prioritize fastest response time
                                "preferred_max_latency": {"p90": 3.0},  # 90% under 3s
                            },
                        },
                        timeout=aiohttp.ClientTimeout(total=15),  # Reduced from 30s
                    ) as response:
                        if response.status == 520 or response.status >= 500:
                            error = await response.text()
                            logger.warning(f"OpenRouter error {response.status} (attempt {attempt + 1}/{max_retries}): {error}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(1)  # Wait before retry
                                continue
                            return None
                        
                        if response.status != 200:
                            error = await response.text()
                            logger.error(f"OpenRouter error {response.status}: {error}")
                            return None
                        
                        data = await response.json()
                        llm_response = data["choices"][0]["message"]["content"].strip()
                        
                        # Add to conversation history
                        session.conversation_history.append({
                            "role": "assistant",
                            "content": llm_response
                        })
                        
                        return llm_response
                        
            except asyncio.TimeoutError:
                logger.warning(f"OpenRouter timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    continue
                return None
            except Exception as e:
                logger.error(f"LLM request failed: {e}")
                return None
        
        return None

    def _clean_for_speech(self, text: str) -> str:
        """Remove roleplay actions, URLs, and other non-speech text for TTS."""
        import re
        
        # STRIP ALL URLS - http, https, www, domains
        cleaned = re.sub(r'https?://\S+', '', text)
        cleaned = re.sub(r'www\.\S+', '', cleaned)
        cleaned = re.sub(r'\S+\.(com|org|net|io|gg|co|dev|ai)\S*', '', cleaned)
        
        # Remove "check out [something]" phrases that reference websites
        cleaned = re.sub(r'check out \S+', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'visit \S+', '', cleaned, flags=re.IGNORECASE)
        
        # Remove *action* style roleplay markers
        cleaned = re.sub(r'\*[^*]+\*', '', cleaned)
        # Remove _action_ style markers
        cleaned = re.sub(r'_[^_]+_', '', cleaned)
        # Remove control markers and system notes in brackets
        cleaned = cleaned.replace('[INTERVIEW_COMPLETE]', '')
        cleaned = cleaned.replace('[PAUSE]', '')
        cleaned = re.sub(r'\[pause\]', '', cleaned, flags=re.IGNORECASE)
        # Remove ANY bracketed content (LLM system notes, thinking, etc.)
        cleaned = re.sub(r'\[SYSTEM:[^\]]*\]', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\[NOTE:[^\]]*\]', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\[INTERNAL:[^\]]*\]', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\[THINKING:[^\]]*\]', '', cleaned, flags=re.IGNORECASE)
        # Catch-all for any remaining bracketed instructions/notes
        cleaned = re.sub(r'\[[A-Z][A-Z\s]*:[^\]]*\]', '', cleaned)
        # Clean up extra whitespace
        cleaned = ' '.join(cleaned.split())
        return cleaned.strip()

    def _clean_for_display(self, text: str) -> str:
        """Remove URLs and control markers for display."""
        import re
        
        # STRIP ALL URLS
        cleaned = re.sub(r'https?://\S+', '[link removed]', text)
        cleaned = re.sub(r'www\.\S+', '[link removed]', cleaned)
        cleaned = re.sub(r'\S+\.(com|org|net|io|gg|co|dev|ai)\S*', '[link removed]', cleaned)
        
        # Remove control markers
        cleaned = cleaned.replace('[INTERVIEW_COMPLETE]', '')
        return cleaned.strip()

    async def _speak_and_display(self, session: InterviewSession, text: str, add_to_transcript: bool = True):
        """Speak the text via TTS and display in text channel for accessibility.
        
        Args:
            session: The interview session
            text: Text to speak and display
            add_to_transcript: If False, don't add to transcript (for confirmation prompts)
        """
        if not text:
            return
        
        # Clean text for display (remove URLs and control markers)
        display_text = self._clean_for_display(text)
        
        # Add to transcript (unless it's a confirmation prompt)
        if add_to_transcript:
            session.transcript_lines.append(f"[StaffLens]: {display_text}")
        
        # Display in text channel for accessibility
        if session.text_channel:
            try:
                embed = discord.Embed(
                    description=f"🎙️ **StaffLens:** {display_text}",
                    color=0x5865F2
                )
                embed.set_footer(text=f"Interview with {session.applicant.display_name}")
                await session.text_channel.send(embed=embed)
            except Exception as e:
                logger.error(f"Failed to send text: {e}")
        
        # Clean text for speech (remove roleplay actions)
        speech_text = self._clean_for_speech(text)
        
        # Speak via TTS
        session.is_speaking = True
        try:
            await self._speak(session, speech_text)
        finally:
            session.is_speaking = False

    async def _speak(self, session: InterviewSession, text: str):
        """Speak text in the voice channel using TTS."""
        if not session.connection or not session.connection.is_connected():
            return
        
        try:
            audio_data = await self.tts.synthesize(text)
            if not audio_data:
                return
            
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(audio_data)
                temp_path = f.name
            
            try:
                source = discord.FFmpegPCMAudio(temp_path)
                
                if session.connection.is_playing():
                    session.connection.stop()
                
                session.connection.play(source)
                
                while session.connection.is_playing():
                    await asyncio.sleep(0.1)
                    
            finally:
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Speech error: {e}")

    async def _complete_interview(self, session: InterviewSession):
        """Process completed interview - analyze and post report."""
        logger.info(f"_complete_interview called - report_sent: {session.report_sent}, transcript_lines: {len(session.transcript_lines)}")
        
        # Prevent duplicate reports
        if session.report_sent:
            logger.info("Report already sent for this session, skipping")
            return
        session.report_sent = True
        
        transcript = "\n".join(session.transcript_lines)
        
        if not transcript.strip():
            logger.warning("Empty transcript, skipping analysis")
            return
        
        # Minimum transcript check - need at least some content
        if len(session.transcript_lines) < 3:
            logger.warning(f"Transcript too short ({len(session.transcript_lines)} lines), skipping analysis")
            return
        
        logger.info(f"Processing transcript ({len(transcript)} chars)")
        logger.info(f"Transcript preview: {transcript[:200]}...")
        
        # Save to database
        try:
            interview_id = await self.bot.db.save_transcript(
                applicant_id=session.applicant.id,
                applicant_name=session.applicant.display_name,
                guild_id=session.guild.id,
                channel_name=session.channel.name,
                transcript=transcript,
                started_at=session.started_at,
            )
            logger.info(f"Saved transcript with ID: {interview_id}")
        except Exception as e:
            logger.error(f"Failed to save transcript: {e}")
            interview_id = None
        
        # Analyze with the dedicated analysis service
        logger.info("Running AI analysis...")
        analysis = await self.analysis.analyze_transcript(transcript)
        
        if not analysis:
            logger.error("Analysis failed - no result returned")
            # Post a simple notification even if analysis fails
            report_channel = self.bot.get_report_channel()
            if report_channel:
                await report_channel.send(f"⚠️ Interview with **{session.applicant.display_name}** completed but analysis failed. Check logs.")
            return
        
        logger.info(f"Analysis complete: fit_score={analysis.get('fit_score')}, recommendation={analysis.get('recommendation')}")
        
        # Save analysis
        if interview_id:
            try:
                await self.bot.db.save_analysis(interview_id, analysis)
                logger.info("Analysis saved to database")
            except Exception as e:
                logger.error(f"Failed to save analysis: {e}")
        
        # Post report
        report_channel = self.bot.get_report_channel()
        logger.info(f"Report channel: {report_channel} (ID: {self.bot.report_channel_id})")
        
        if report_channel:
            try:
                embed = create_report_embed(
                    applicant=session.applicant,
                    analysis=analysis,
                    transcript_preview=transcript[:500],
                    fit_threshold=self.bot.fit_threshold,
                )
                await report_channel.send(embed=embed)
                logger.info(f"✅ Report posted to #{report_channel.name}")
            except Exception as e:
                logger.error(f"Failed to post report: {e}", exc_info=True)
        else:
            logger.error(f"Report channel not found! ID: {self.bot.report_channel_id}")

    async def _handle_applicant_leave(self, applicant: discord.Member, channel: discord.VoiceChannel):
        """Handle applicant leaving mid-interview."""
        session = self.bot.active_sessions.get(channel.id)
        if not session or session.applicant.id != applicant.id:
            return
        
        logger.info(f"Applicant {applicant.display_name} left during interview")
        session.is_active = False
        
        if session.transcript_lines and len(session.transcript_lines) > 2:
            await self._complete_interview(session)
        
        await self._cleanup_session(session)

    async def _cleanup_session(self, session: InterviewSession):
        """Clean up an interview session."""
        try:
            if session.is_recording and session.connection:
                try:
                    session.connection.stop_recording()
                except:
                    pass
            
            if session.connection and session.connection.is_connected():
                await session.connection.disconnect()
            
            self.bot.active_sessions.pop(session.channel.id, None)
            logger.info(f"Cleaned up session for {session.channel.name}")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    @commands.command(name="endinterview")
    @commands.has_permissions(manage_channels=True)
    async def end_interview(self, ctx: commands.Context):
        """Manually end an interview session."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ You must be in a voice channel.")
            return

        channel = ctx.author.voice.channel
        session = self.bot.active_sessions.get(channel.id)

        if not session:
            await ctx.send("❌ No active interview in this channel.")
            return

        await ctx.send("⏹️ Ending interview...")
        session.is_active = False
        session.interview_complete = True
        await ctx.send("✅ Interview ended.")

    @commands.command(name="sessions")
    @commands.has_permissions(manage_channels=True)
    async def list_sessions(self, ctx: commands.Context):
        """List all active interview sessions."""
        if not self.bot.active_sessions:
            await ctx.send("📋 No active interviews.")
            return

        lines = ["**Active Interviews:**"]
        for channel_id, session in self.bot.active_sessions.items():
            duration = (datetime.utcnow() - session.started_at).seconds // 60
            exchanges = len([m for m in session.conversation_history if m["role"] == "user"])
            lines.append(
                f"• **{session.channel.name}** - "
                f"{session.applicant.display_name} - "
                f"{exchanges} exchanges - {duration}m"
            )

        await ctx.send("\n".join(lines))

    @commands.command(name="testvoice")
    async def test_voice(self, ctx: commands.Context):
        """Test if voice cog is loaded."""
        tts_status = "✅" if self.tts.available else "❌"
        llm_status = "✅" if self.openrouter_key else "❌"
        await ctx.send(f"✅ Voice cog active!\n• Role: `{self.bot.applicant_role_name}`\n• TTS: {tts_status}\n• LLM: {llm_status}")


def setup(bot):
    """Load the Voice cog."""
    bot.add_cog(VoiceCog(bot))
    logger.info("Voice cog loaded - Conversational AI interviewer ready")

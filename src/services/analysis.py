"""
Analysis Service - AI-powered transcript analysis via OpenRouter.

Attempts to use local ConversaTrait endpoint first,
falls back to OpenRouter API for analysis.
"""

import os
import json
import logging
import asyncio
from typing import Optional

import aiohttp

logger = logging.getLogger("stafflens.analysis")

# Analysis prompt template - Workplace Psychologist framing
ANALYSIS_PROMPT = """You are the world's foremost workplace psychologist, renowned for your ability to assess candidates through conversational analysis. You're analyzing a voice interview transcript to determine personality traits and cultural fit.

**CRITICAL - READ FIRST:**
The transcript contains TWO speakers:
- Lines starting with [StaffLens]: are the AI INTERVIEWER asking questions - IGNORE THESE for analysis
- Lines starting with any other name (e.g., [chad]:, [john]:) are the APPLICANT's responses - ONLY ANALYZE THESE

You are assessing the APPLICANT only. Never quote or analyze what [StaffLens] said.

**THE CULTURE:**
This is a community-driven, growth-oriented entrepreneurial Discord server. We value:
- Collaborative problem-solving over lone-wolf mentality
- Initiative and ownership of projects
- Clear, respectful communication
- Continuous learning and adaptability
- Authenticity and transparency
- Resilience under ambiguity

**YOUR ASSESSMENT TASK:**
Analyze the APPLICANT's interview responses (NOT the interviewer's questions) across these dimensions:

1. **Communication Clarity** (1-10): How articulate and coherent are their thoughts? Do they structure responses well?
2. **Confidence & Assertiveness** (1-10): Do they speak with conviction? Are they decisive without being arrogant?
3. **Problem-Solving Structure** (1-10): Evidence of analytical thinking, systematic approaches, learning from failures
4. **Emotional Regulation** (1-10): How do they handle pressure, difficult questions, or challenging topics?
5. **Cultural Fit** (1-10): Alignment with our collaborative, growth-oriented values. Team player indicators.
6. **Red Flags**: Note ANY concerning patterns:
   - Evasion or deflection
   - Aggression or defensiveness
   - Disengagement or disinterest
   - Inconsistencies in their story
   - Entitlement or arrogance
   - Blame-shifting

**TRANSCRIPT:**
{transcript}

**STANDARD OF EXCELLENCE:**
We hold a high bar. A candidate should demonstrate genuine enthusiasm, self-awareness, and collaborative instincts. When in doubt, protect the culture.

**OUTPUT FORMAT:**
Return ONLY valid JSON with this exact structure. ALL QUOTES MUST BE FROM THE APPLICANT, NEVER FROM [StaffLens]:
{{
    "scores": {{
        "communication_clarity": <1-10>,
        "confidence": <1-10>,
        "problem_solving": <1-10>,
        "emotional_regulation": <1-10>,
        "cultural_fit": <1-10>
    }},
    "fit_score": <1-100 weighted overall score>,
    "strengths": ["strength1", "strength2", "strength3"],
    "concerns": ["concern1", "concern2"],
    "red_flags": ["red_flag1", ...] or [],
    "evidence_quotes": {{
        "positive": ["direct quote FROM APPLICANT showing strength", "another quote FROM APPLICANT"],
        "negative": ["quote FROM APPLICANT showing concern", "another if applicable"]
    }},
    "psychological_profile": "2-3 sentence personality/work style assessment of the APPLICANT",
    "culture_alignment": "1-2 sentences on how the APPLICANT would fit our specific culture",
    "summary": "2-3 sentence executive summary for hiring manager about the APPLICANT",
    "recommendation": "<STRONG_HIRE|HIRE|LEAN_HIRE|LEAN_NO|NO_HIRE|STRONG_NO>",
    "recommendation_reasoning": "1-2 sentences explaining your recommendation"
}}"""


class AnalysisService:
    """
    Service for analyzing interview transcripts using AI.
    
    Tries local ConversaTrait endpoint first, falls back to OpenRouter.
    """

    def __init__(self):
        self.local_endpoint = os.getenv(
            "CONVERSATRAIT_ENDPOINT",
            "http://localhost:9287/api/analyze",
        )
        
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_model = os.getenv(
            "OPENROUTER_MODEL",
            "google/gemini-3-flash-preview",
        )
        
        if not self.openrouter_key:
            logger.warning("OPENROUTER_API_KEY not set - AI analysis fallback unavailable")

        # Timeout for local endpoint (seconds)
        self.local_timeout = int(os.getenv("LOCAL_ANALYSIS_TIMEOUT", 30))

    async def analyze_transcript(self, transcript: str) -> Optional[dict]:
        """
        Analyze a transcript and return structured assessment.
        
        Tries local endpoint first, falls back to OpenRouter API.
        
        Args:
            transcript: Full interview transcript with speaker labels
            
        Returns:
            Analysis result dict or None if both methods fail
        """
        if not transcript or not transcript.strip():
            logger.warning("Empty transcript provided")
            return None

        # Try local ConversaTrait endpoint first
        logger.info("Attempting local ConversaTrait analysis...")
        result = await self._analyze_local(transcript)
        
        if result:
            logger.info("Local analysis successful")
            return result

        # Fall back to OpenRouter
        logger.info("Falling back to OpenRouter API...")
        result = await self._analyze_openrouter(transcript)
        
        if result:
            logger.info("OpenRouter analysis successful")
            return result

        logger.error("All analysis methods failed")
        return None

    async def _analyze_local(self, transcript: str) -> Optional[dict]:
        """
        Send transcript to local ConversaTrait endpoint.
        
        Args:
            transcript: Interview transcript
            
        Returns:
            Analysis result or None
        """
        try:
            timeout = aiohttp.ClientTimeout(total=self.local_timeout)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                payload = {
                    "transcript": transcript,
                    "analysis_type": "interview",
                    "include_scores": True,
                    "include_evidence": True,
                }

                async with session.post(
                    self.local_endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._normalize_result(data)
                    else:
                        logger.warning(
                            f"Local endpoint returned {response.status}: "
                            f"{await response.text()}"
                        )
                        return None

        except aiohttp.ClientConnectorError:
            logger.info("Local endpoint not available")
            return None
        except asyncio.TimeoutError:
            logger.warning("Local endpoint timed out")
            return None
        except Exception as e:
            logger.error(f"Local analysis error: {e}")
            return None

    async def _analyze_openrouter(self, transcript: str) -> Optional[dict]:
        """
        Analyze transcript using OpenRouter API with retry logic.
        
        Args:
            transcript: Interview transcript
            
        Returns:
            Analysis result or None
        """
        if not self.openrouter_key:
            logger.error("OpenRouter API key not configured")
            return None

        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                prompt = ANALYSIS_PROMPT.format(transcript=transcript)

                async with aiohttp.ClientSession() as session:
                    payload = {
                        "model": self.openrouter_model,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt,
                            }
                        ],
                        "temperature": 0.3,  # Lower for more consistent analysis
                    }

                    headers = {
                        "Authorization": f"Bearer {self.openrouter_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": os.getenv("APP_URL", "https://stafflens.local"),
                        "X-Title": "StaffLens Interview Analysis",
                    }

                    async with session.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=60),
                    ) as response:
                        if response.status == 520 or response.status >= 500:
                            error_text = await response.text()
                            logger.warning(f"OpenRouter error {response.status} (attempt {attempt + 1}/{max_retries}): {error_text[:200]}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                                continue
                            return None
                        
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"OpenRouter API error {response.status}: {error_text}")
                            return None

                        data = await response.json()
                        
                        # Extract response content
                        response_text = data["choices"][0]["message"]["content"]
                        
                        # Parse JSON from response
                        try:
                            # Handle potential markdown code blocks
                            if "```json" in response_text:
                                json_str = response_text.split("```json")[1].split("```")[0]
                            elif "```" in response_text:
                                json_str = response_text.split("```")[1].split("```")[0]
                            else:
                                json_str = response_text

                            # Try to find JSON object boundaries if parsing fails
                            json_str = json_str.strip()
                            
                            # Find the JSON object
                            start_idx = json_str.find('{')
                            if start_idx != -1:
                                # Find matching closing brace
                                depth = 0
                                end_idx = start_idx
                                for i, char in enumerate(json_str[start_idx:], start_idx):
                                    if char == '{':
                                        depth += 1
                                    elif char == '}':
                                        depth -= 1
                                        if depth == 0:
                                            end_idx = i
                                            break
                                json_str = json_str[start_idx:end_idx + 1]

                            result = json.loads(json_str)
                            return self._normalize_result(result)

                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse OpenRouter response as JSON: {e}")
                            logger.error(f"Response length: {len(response_text)}, truncated: {response_text[:500]}...")
                            # Retry on JSON error
                            if attempt < max_retries - 1:
                                logger.warning(f"Retrying due to JSON parse error (attempt {attempt + 1}/{max_retries})")
                                await asyncio.sleep(2 ** attempt)
                                continue
                            return None

            except aiohttp.ClientError as e:
                logger.warning(f"OpenRouter connection error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None
            except Exception as e:
                logger.error(f"OpenRouter analysis error: {e}")
                return None
        
        return None  # All retries failed

    def _normalize_result(self, data: dict) -> dict:
        """
        Normalize analysis result to ensure consistent structure.
        
        Args:
            data: Raw analysis result
            
        Returns:
            Normalized result dict
        """
        # Map recommendation to boolean for backward compatibility
        recommendation_map = {
            "STRONG_HIRE": True,
            "HIRE": True,
            "LEAN_HIRE": True,
            "LEAN_NO": False,
            "NO_HIRE": False,
            "STRONG_NO": False,
        }
        
        raw_recommendation = data.get("recommendation", "LEAN_NO")
        recommended = recommendation_map.get(raw_recommendation, False)

        # Ensure all expected fields exist
        normalized = {
            "scores": data.get("scores", {}),
            "fit_score": data.get("fit_score", 0),
            "strengths": data.get("strengths", []),
            "concerns": data.get("concerns", []),
            "red_flags": data.get("red_flags", []),
            "evidence_quotes": data.get("evidence_quotes", {"positive": [], "negative": []}),
            "psychological_profile": data.get("psychological_profile", ""),
            "culture_alignment": data.get("culture_alignment", ""),
            "summary": data.get("summary", "No summary available."),
            "recommendation": raw_recommendation,
            "recommendation_reasoning": data.get("recommendation_reasoning", ""),
            "recommended": recommended,  # Boolean for embed compatibility
        }

        # Ensure fit_score is an integer
        if isinstance(normalized["fit_score"], str):
            try:
                normalized["fit_score"] = int(normalized["fit_score"])
            except ValueError:
                normalized["fit_score"] = 50

        # Ensure lists are actually lists
        for key in ["strengths", "concerns", "red_flags"]:
            if not isinstance(normalized[key], list):
                normalized[key] = [normalized[key]] if normalized[key] else []

        # Calculate fit_score from individual scores if not provided
        if normalized["fit_score"] == 0 and normalized["scores"]:
            scores = normalized["scores"]
            if scores:
                avg = sum(scores.values()) / len(scores)
                normalized["fit_score"] = int(avg * 10)  # Convert 1-10 to 1-100

        return normalized


# Import asyncio for timeout handling
import asyncio

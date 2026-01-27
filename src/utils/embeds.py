"""
Embed Utilities - Discord embed generation for reports.

Creates beautifully formatted Discord embeds for interview
reports and other bot messages.
"""

from datetime import datetime
from typing import Optional, Any

import discord


def create_report_embed(
    applicant: Any,
    analysis: dict,
    transcript_preview: str,
    fit_threshold: int = 70,
) -> discord.Embed:
    """
    Create a comprehensive interview report embed.
    
    Args:
        applicant: Discord member object (or mock with display_name, id, avatar)
        analysis: Analysis result dict
        transcript_preview: First ~500 chars of transcript
        fit_threshold: Score threshold for recommendation
        
    Returns:
        Discord Embed object
    """
    fit_score = analysis.get("fit_score", 0)
    recommendation = analysis.get("recommendation", "LEAN_NO")
    recommended = analysis.get("recommended", fit_score >= fit_threshold)

    # Determine embed color and status based on recommendation tier
    recommendation_display = {
        "STRONG_HIRE": ("🟢 STRONG HIRE", discord.Color.green()),
        "HIRE": ("✅ HIRE", discord.Color.green()),
        "LEAN_HIRE": ("🟡 LEAN HIRE", discord.Color.gold()),
        "LEAN_NO": ("🟠 LEAN NO", discord.Color.orange()),
        "NO_HIRE": ("❌ NO HIRE", discord.Color.red()),
        "STRONG_NO": ("🔴 STRONG NO", discord.Color.dark_red()),
    }
    
    status_text, color = recommendation_display.get(
        recommendation, 
        ("⚠️ NEEDS REVIEW", discord.Color.greyple())
    )

    # Create embed
    embed = discord.Embed(
        title=f"📋 Interview Report: {applicant.display_name}",
        description=f"**{status_text}**",
        color=color,
        timestamp=datetime.utcnow(),
    )

    # Set applicant info
    embed.set_author(
        name=f"Applicant ID: {applicant.id}",
        icon_url=applicant.avatar.url if hasattr(applicant, 'avatar') and applicant.avatar else None,
    )

    # Fit Score with visual bar
    score_bar = _create_score_bar(fit_score)
    embed.add_field(
        name="🎯 Fit Score",
        value=f"**{fit_score}**/100\n{score_bar}",
        inline=False,
    )

    # Individual trait scores
    scores = analysis.get("scores", {})
    if scores:
        score_lines = []
        score_emoji = {
            "communication_clarity": "💬",
            "problem_solving": "🧩",
            "confidence": "💪",
            "emotional_regulation": "🧘",
            "cultural_fit": "🤝",
        }
        for trait, score in scores.items():
            emoji = score_emoji.get(trait, "📊")
            trait_name = trait.replace("_", " ").title()
            score_lines.append(f"{emoji} **{trait_name}:** {score}/10")
        
        embed.add_field(
            name="📊 Trait Scores",
            value="\n".join(score_lines),
            inline=True,
        )

    # Key Strengths
    strengths = analysis.get("strengths", [])
    if strengths:
        embed.add_field(
            name="💪 Key Strengths",
            value="\n".join(f"• {s}" for s in strengths[:5]),
            inline=True,
        )

    # Concerns
    concerns = analysis.get("concerns", [])
    if concerns:
        embed.add_field(
            name="⚠️ Concerns",
            value="\n".join(f"• {c}" for c in concerns[:5]),
            inline=True,
        )

    # Red Flags (prominent if present)
    red_flags = analysis.get("red_flags", [])
    if red_flags:
        embed.add_field(
            name="🚩 Red Flags",
            value="\n".join(f"• {rf}" for rf in red_flags),
            inline=False,
        )

    # Psychological Profile (new)
    psych_profile = analysis.get("psychological_profile", "")
    if psych_profile:
        embed.add_field(
            name="🧠 Psychological Profile",
            value=psych_profile[:1024],
            inline=False,
        )

    # Culture Alignment (new)
    culture_align = analysis.get("culture_alignment", "")
    if culture_align:
        embed.add_field(
            name="🏠 Culture Alignment",
            value=culture_align[:1024],
            inline=False,
        )

    # Evidence Quotes
    evidence = analysis.get("evidence_quotes", {})
    if evidence.get("positive"):
        quotes = evidence["positive"][:2]
        embed.add_field(
            name="💬 Positive Quotes",
            value="\n".join(f'> "{q}"' for q in quotes),
            inline=False,
        )
    if evidence.get("negative"):
        quotes = evidence["negative"][:2]
        embed.add_field(
            name="💬 Concerning Quotes",
            value="\n".join(f'> "{q}"' for q in quotes),
            inline=False,
        )

    # Summary & Recommendation Reasoning
    summary = analysis.get("summary", "")
    reasoning = analysis.get("recommendation_reasoning", "")
    if summary or reasoning:
        summary_text = summary
        if reasoning:
            summary_text += f"\n\n**Reasoning:** {reasoning}"
        embed.add_field(
            name="📝 Summary",
            value=summary_text[:1024],
            inline=False,
        )

    # Transcript Preview
    if transcript_preview:
        preview = transcript_preview[:400]
        if len(transcript_preview) > 400:
            preview += "..."
        embed.add_field(
            name="📜 Transcript Preview",
            value=f"```{preview}```",
            inline=False,
        )

    # Footer
    embed.set_footer(
        text=f"StaffLens Analysis • Threshold: {fit_threshold} • Model: Gemini 3 Flash",
    )

    return embed


def _create_score_bar(score: int, total: int = 100, length: int = 20) -> str:
    """
    Create a visual progress bar for scores.
    
    Args:
        score: Current score
        total: Maximum score
        length: Bar length in characters
        
    Returns:
        Unicode progress bar string
    """
    filled = int((score / total) * length)
    empty = length - filled
    
    # Color-coded segments
    if score >= 80:
        fill_char = "🟩"
    elif score >= 60:
        fill_char = "🟨"
    elif score >= 40:
        fill_char = "🟧"
    else:
        fill_char = "🟥"
    
    return fill_char * filled + "⬜" * empty


def create_session_start_embed(
    applicant: discord.Member,
    channel: discord.VoiceChannel,
) -> discord.Embed:
    """
    Create an embed for when an interview session starts.
    
    Args:
        applicant: The applicant member
        channel: Voice channel being recorded
        
    Returns:
        Discord Embed
    """
    embed = discord.Embed(
        title="🎙️ Interview Session Started",
        description=f"Recording interview with **{applicant.display_name}**",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow(),
    )
    
    embed.add_field(name="Channel", value=channel.name, inline=True)
    embed.add_field(name="Applicant ID", value=str(applicant.id), inline=True)
    
    embed.set_thumbnail(url=applicant.avatar.url if applicant.avatar else None)
    embed.set_footer(text="StaffLens • Recording in progress")
    
    return embed


def create_error_embed(
    title: str,
    description: str,
    details: Optional[str] = None,
) -> discord.Embed:
    """
    Create an error embed.
    
    Args:
        title: Error title
        description: Error description
        details: Optional technical details
        
    Returns:
        Discord Embed
    """
    embed = discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=discord.Color.red(),
        timestamp=datetime.utcnow(),
    )
    
    if details:
        embed.add_field(
            name="Details",
            value=f"```{details[:1000]}```",
            inline=False,
        )
    
    return embed


def create_success_embed(
    title: str,
    description: str,
) -> discord.Embed:
    """
    Create a success embed.
    
    Args:
        title: Success title
        description: Success description
        
    Returns:
        Discord Embed
    """
    return discord.Embed(
        title=f"✅ {title}",
        description=description,
        color=discord.Color.green(),
        timestamp=datetime.utcnow(),
    )

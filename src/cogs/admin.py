"""
Admin Cog - Administrative commands for managing StaffLens.

Provides commands for viewing past interviews, managing settings,
and other administrative functions.
"""

import logging
from datetime import datetime

import discord
from discord.ext import commands

from src.utils.embeds import create_report_embed

logger = logging.getLogger("stafflens.admin")


class AdminCog(commands.Cog):
    """Administrative commands for StaffLens."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="history")
    @commands.has_permissions(manage_guild=True)
    async def view_history(self, ctx: commands.Context, limit: int = 10):
        """
        View recent interview history.
        
        Usage: !history [limit]
        Default: Shows last 10 interviews
        Requires: Manage Server permission
        """
        interviews = await self.bot.db.get_recent_interviews(
            guild_id=ctx.guild.id,
            limit=limit,
        )

        if not interviews:
            await ctx.send("📋 No interview history found.")
            return

        embed = discord.Embed(
            title="📋 Recent Interviews",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow(),
        )

        for interview in interviews:
            score = interview.get("fit_score", "N/A")
            recommended = "✅" if interview.get("recommended") else "❌"
            date = interview.get("created_at", "Unknown")

            embed.add_field(
                name=f"{interview['applicant_name']}",
                value=(
                    f"Score: **{score}**/100 {recommended}\n"
                    f"Date: {date}\n"
                    f"Channel: #{interview.get('channel_name', 'Unknown')}"
                ),
                inline=True,
            )

        await ctx.send(embed=embed)

    @commands.command(name="interview")
    @commands.has_permissions(manage_guild=True)
    async def view_interview(self, ctx: commands.Context, interview_id: int):
        """
        View details of a specific interview.
        
        Usage: !interview <id>
        Requires: Manage Server permission
        """
        interview = await self.bot.db.get_interview(interview_id)

        if not interview:
            await ctx.send(f"❌ Interview #{interview_id} not found.")
            return

        # Create a detailed embed
        embed = discord.Embed(
            title=f"Interview #{interview_id}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow(),
        )

        embed.add_field(
            name="Applicant",
            value=interview["applicant_name"],
            inline=True,
        )
        embed.add_field(
            name="Fit Score",
            value=f"{interview.get('fit_score', 'N/A')}/100",
            inline=True,
        )
        embed.add_field(
            name="Recommended",
            value="✅ Yes" if interview.get("recommended") else "❌ No",
            inline=True,
        )

        # Add analysis details if available
        if interview.get("analysis"):
            analysis = interview["analysis"]
            
            if analysis.get("strengths"):
                embed.add_field(
                    name="Key Strengths",
                    value="\n".join(f"• {s}" for s in analysis["strengths"][:3]),
                    inline=False,
                )
            
            if analysis.get("concerns"):
                embed.add_field(
                    name="Concerns",
                    value="\n".join(f"• {c}" for c in analysis["concerns"][:3]),
                    inline=False,
                )

        # Add transcript preview
        if interview.get("transcript"):
            preview = interview["transcript"][:500]
            if len(interview["transcript"]) > 500:
                preview += "..."
            embed.add_field(
                name="Transcript Preview",
                value=f"```{preview}```",
                inline=False,
            )

        await ctx.send(embed=embed)

    @commands.command(name="transcript")
    @commands.has_permissions(manage_guild=True)
    async def get_transcript(self, ctx: commands.Context, interview_id: int):
        """
        Get full transcript of an interview.
        
        Usage: !transcript <id>
        Requires: Manage Server permission
        """
        interview = await self.bot.db.get_interview(interview_id)

        if not interview:
            await ctx.send(f"❌ Interview #{interview_id} not found.")
            return

        transcript = interview.get("transcript", "No transcript available.")

        # If transcript is too long, send as file
        if len(transcript) > 1900:
            file = discord.File(
                fp=transcript.encode(),
                filename=f"transcript_{interview_id}.txt",
            )
            await ctx.send(f"📄 Transcript for Interview #{interview_id}:", file=file)
        else:
            await ctx.send(
                f"📄 **Transcript for Interview #{interview_id}:**\n```{transcript}```"
            )

    @commands.command(name="reanalyze")
    @commands.has_permissions(administrator=True)
    async def reanalyze(self, ctx: commands.Context, interview_id: int):
        """
        Re-run AI analysis on a past interview.
        
        Usage: !reanalyze <id>
        Requires: Administrator permission
        """
        interview = await self.bot.db.get_interview(interview_id)

        if not interview:
            await ctx.send(f"❌ Interview #{interview_id} not found.")
            return

        transcript = interview.get("transcript")
        if not transcript:
            await ctx.send("❌ No transcript available for this interview.")
            return

        await ctx.send("🔄 Re-analyzing interview...")

        # Get the analysis service from voice cog
        voice_cog = self.bot.get_cog("VoiceCog")
        if not voice_cog:
            await ctx.send("❌ Voice cog not loaded.")
            return

        analysis = await voice_cog.analysis.analyze_transcript(transcript)

        if not analysis:
            await ctx.send("❌ Analysis failed.")
            return

        # Update database
        await self.bot.db.save_analysis(interview_id, analysis)

        # Create a mock applicant object for the embed
        class MockApplicant:
            def __init__(self, name, id):
                self.display_name = name
                self.id = id
                self.avatar = None

        applicant = MockApplicant(
            interview["applicant_name"],
            interview["applicant_id"],
        )

        embed = create_report_embed(
            applicant=applicant,
            analysis=analysis,
            transcript_preview=transcript[:500],
            fit_threshold=self.bot.fit_threshold,
        )

        await ctx.send("✅ Analysis complete!", embed=embed)

    @commands.command(name="setrole")
    @commands.has_permissions(administrator=True)
    async def set_applicant_role(self, ctx: commands.Context, *, role_name: str):
        """
        Set the role name that triggers recording.
        
        Usage: !setrole <role name>
        Requires: Administrator permission
        
        Note: This only changes the runtime value.
        Update APPLICANT_ROLE_NAME in .env for persistence.
        """
        # Verify role exists
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            await ctx.send(f"⚠️ Role '{role_name}' not found, but setting anyway.")

        self.bot.applicant_role_name = role_name
        await ctx.send(f"✅ Applicant role set to: **{role_name}**")

    @commands.command(name="setthreshold")
    @commands.has_permissions(administrator=True)
    async def set_threshold(self, ctx: commands.Context, threshold: int):
        """
        Set the fit score threshold for recommendations.
        
        Usage: !setthreshold <1-100>
        Requires: Administrator permission
        """
        if not 1 <= threshold <= 100:
            await ctx.send("❌ Threshold must be between 1 and 100.")
            return

        self.bot.fit_threshold = threshold
        await ctx.send(f"✅ Fit threshold set to: **{threshold}**")

    @commands.command(name="status")
    async def show_status(self, ctx: commands.Context):
        """
        Show current bot configuration and status.
        
        Usage: !status
        """
        embed = discord.Embed(
            title="🤖 StaffLens Status",
            color=discord.Color.green(),
            timestamp=datetime.utcnow(),
        )

        embed.add_field(
            name="Applicant Role",
            value=self.bot.applicant_role_name,
            inline=True,
        )
        embed.add_field(
            name="Fit Threshold",
            value=f"{self.bot.fit_threshold}/100",
            inline=True,
        )
        embed.add_field(
            name="Active Sessions",
            value=str(len(self.bot.active_sessions)),
            inline=True,
        )

        report_channel = self.bot.get_report_channel()
        embed.add_field(
            name="Report Channel",
            value=f"#{report_channel.name}" if report_channel else "Not configured",
            inline=True,
        )

        # Database stats
        stats = await self.bot.db.get_stats(ctx.guild.id)
        embed.add_field(
            name="Total Interviews",
            value=str(stats.get("total_interviews", 0)),
            inline=True,
        )
        embed.add_field(
            name="Avg Fit Score",
            value=f"{stats.get('avg_fit_score', 0):.1f}",
            inline=True,
        )

        await ctx.send(embed=embed)


def setup(bot):
    """Load the Admin cog."""
    bot.add_cog(AdminCog(bot))

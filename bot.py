"""
StaffLens - AI-Powered Applicant Vetting Discord Bot

Main entry point for the Discord bot. Handles initialization,
cog loading, and core event management.
"""

import os
import asyncio
import logging
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

from src.services.database import Database

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("stafflens")


class StaffLens(commands.Bot):
    """
    Main bot class for StaffLens.
    
    Handles voice recording, transcription, and AI analysis
    of applicant interviews in Discord voice channels.
    """

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        intents.members = True  # Required to check roles

        super().__init__(
            command_prefix=os.getenv("COMMAND_PREFIX", "!"),
            intents=intents,
            description="AI-powered applicant vetting through voice analysis",
        )

        # Database instance
        self.db = Database()

        # Channel ID for posting reports
        self.report_channel_id = int(os.getenv("REPORT_CHANNEL_ID", 0))

        # Role name that triggers recording
        self.applicant_role_name = os.getenv("APPLICANT_ROLE_NAME", "Applicant")

        # Fit score threshold for recommendation
        self.fit_threshold = int(os.getenv("FIT_THRESHOLD", 70))

        # Active recording sessions: {voice_channel_id: session_data}
        self.active_sessions = {}

    async def on_ready(self):
        """Called when the bot is fully connected and ready."""
        # Load cogs here where we have an event loop
        if not self.cogs:
            logger.info("Loading cogs...")
            for cog in ["src.cogs.voice", "src.cogs.admin"]:
                try:
                    self.load_extension(cog)
                    logger.info(f"Loaded cog: {cog}")
                except Exception as e:
                    logger.error(f"Failed to load cog {cog}: {e}")
            logger.info(f"Loaded cogs: {list(self.cogs.keys())}")
        
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guild(s)")
        logger.info(f"Report channel ID: {self.report_channel_id}")
        logger.info(f"Applicant role: {self.applicant_role_name}")
        logger.info("------")

        # Set presence
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="for applicants",
        )
        await self.change_presence(activity=activity)

    async def on_voice_state_update(self, member, before, after):
        """Handle voice state changes - delegate to voice cog."""
        logger.info(f"[BOT] Voice event: {member.display_name} | {before.channel} -> {after.channel}")
        
        # Get voice cog and call its handler
        voice_cog = self.get_cog("VoiceCog")
        if voice_cog:
            await voice_cog.handle_voice_update(member, before, after)
        else:
            logger.warning("VoiceCog not found!")

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Global error handler for commands."""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands

        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
            return

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing argument: `{error.param.name}`")
            return

        # Log unexpected errors
        logger.error(f"Command error in {ctx.command}: {error}", exc_info=error)
        await ctx.send("❌ An unexpected error occurred.")

    def get_report_channel(self) -> discord.TextChannel | None:
        """Get the channel for posting interview reports."""
        return self.get_channel(self.report_channel_id)


async def main():
    """Main entry point."""
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables!")
        logger.error("Please create a .env file with your bot token.")
        return

    bot = StaffLens()
    
    # Initialize database first
    await bot.db.initialize()
    logger.info("Database initialized")

    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())

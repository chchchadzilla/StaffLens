"""
Database Service - SQLite storage for transcripts and analysis results.

Provides async database operations for storing and retrieving
interview data.
"""

import os
import json
import logging
import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("stafflens.database")

# Default database path
DEFAULT_DB_PATH = "data/stafflens.db"


class Database:
    """
    Async SQLite database service for StaffLens.
    
    Stores interview transcripts, analysis results, and metadata.
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.getenv("DATABASE_PATH", DEFAULT_DB_PATH)
        self._connection: Optional[aiosqlite.Connection] = None

    async def initialize(self):
        """Initialize database and create tables if needed."""
        # Ensure data directory exists
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        # Create tables
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript("""
                -- Interviews table
                CREATE TABLE IF NOT EXISTS interviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    applicant_id INTEGER NOT NULL,
                    applicant_name TEXT NOT NULL,
                    guild_id INTEGER NOT NULL,
                    channel_name TEXT,
                    transcript TEXT,
                    started_at TIMESTAMP,
                    ended_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Analysis results table
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    interview_id INTEGER NOT NULL,
                    fit_score INTEGER,
                    recommended BOOLEAN,
                    scores JSON,
                    strengths JSON,
                    concerns JSON,
                    red_flags JSON,
                    evidence_quotes JSON,
                    summary TEXT,
                    raw_response JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (interview_id) REFERENCES interviews(id)
                );

                -- Create indexes for common queries
                CREATE INDEX IF NOT EXISTS idx_interviews_guild 
                    ON interviews(guild_id);
                CREATE INDEX IF NOT EXISTS idx_interviews_applicant 
                    ON interviews(applicant_id);
                CREATE INDEX IF NOT EXISTS idx_analysis_interview 
                    ON analysis_results(interview_id);
            """)
            await db.commit()
            logger.info(f"Database initialized at {self.db_path}")

    async def save_transcript(
        self,
        applicant_id: int,
        applicant_name: str,
        guild_id: int,
        channel_name: str,
        transcript: str,
        started_at: datetime,
    ) -> int:
        """
        Save an interview transcript.
        
        Args:
            applicant_id: Discord user ID
            applicant_name: Display name
            guild_id: Discord server ID
            channel_name: Voice channel name
            transcript: Full transcript text
            started_at: Interview start time
            
        Returns:
            Interview ID
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO interviews 
                (applicant_id, applicant_name, guild_id, channel_name, transcript, started_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    applicant_id,
                    applicant_name,
                    guild_id,
                    channel_name,
                    transcript,
                    started_at.isoformat(),
                ),
            )
            await db.commit()
            
            interview_id = cursor.lastrowid
            logger.info(f"Saved transcript for interview #{interview_id}")
            return interview_id

    async def save_analysis(self, interview_id: int, analysis: dict) -> int:
        """
        Save analysis results for an interview.
        
        Args:
            interview_id: Associated interview ID
            analysis: Analysis result dict
            
        Returns:
            Analysis record ID
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO analysis_results
                (interview_id, fit_score, recommended, scores, strengths, 
                 concerns, red_flags, evidence_quotes, summary, raw_response)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    interview_id,
                    analysis.get("fit_score"),
                    analysis.get("recommended", False),
                    json.dumps(analysis.get("scores", {})),
                    json.dumps(analysis.get("strengths", [])),
                    json.dumps(analysis.get("concerns", [])),
                    json.dumps(analysis.get("red_flags", [])),
                    json.dumps(analysis.get("evidence_quotes", {})),
                    analysis.get("summary"),
                    json.dumps(analysis),
                ),
            )
            await db.commit()
            
            analysis_id = cursor.lastrowid
            logger.info(f"Saved analysis #{analysis_id} for interview #{interview_id}")
            return analysis_id

    async def get_interview(self, interview_id: int) -> Optional[dict]:
        """
        Get interview details with analysis.
        
        Args:
            interview_id: Interview ID
            
        Returns:
            Interview dict with analysis or None
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Get interview
            cursor = await db.execute(
                "SELECT * FROM interviews WHERE id = ?",
                (interview_id,),
            )
            row = await cursor.fetchone()
            
            if not row:
                return None

            interview = dict(row)
            
            # Get analysis
            cursor = await db.execute(
                "SELECT * FROM analysis_results WHERE interview_id = ?",
                (interview_id,),
            )
            analysis_row = await cursor.fetchone()
            
            if analysis_row:
                analysis = dict(analysis_row)
                # Parse JSON fields
                for field in ["scores", "strengths", "concerns", "red_flags", "evidence_quotes"]:
                    if analysis.get(field):
                        try:
                            analysis[field] = json.loads(analysis[field])
                        except json.JSONDecodeError:
                            pass
                interview["analysis"] = analysis
                interview["fit_score"] = analysis.get("fit_score")
                interview["recommended"] = analysis.get("recommended")

            return interview

    async def get_recent_interviews(
        self,
        guild_id: int,
        limit: int = 10,
    ) -> list[dict]:
        """
        Get recent interviews for a guild.
        
        Args:
            guild_id: Discord server ID
            limit: Max results to return
            
        Returns:
            List of interview dicts
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute(
                """
                SELECT i.*, ar.fit_score, ar.recommended
                FROM interviews i
                LEFT JOIN analysis_results ar ON i.id = ar.interview_id
                WHERE i.guild_id = ?
                ORDER BY i.created_at DESC
                LIMIT ?
                """,
                (guild_id, limit),
            )
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_interviews_by_applicant(
        self,
        applicant_id: int,
        guild_id: Optional[int] = None,
    ) -> list[dict]:
        """
        Get all interviews for a specific applicant.
        
        Args:
            applicant_id: Discord user ID
            guild_id: Optional guild filter
            
        Returns:
            List of interview dicts
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            if guild_id:
                cursor = await db.execute(
                    """
                    SELECT i.*, ar.fit_score, ar.recommended
                    FROM interviews i
                    LEFT JOIN analysis_results ar ON i.id = ar.interview_id
                    WHERE i.applicant_id = ? AND i.guild_id = ?
                    ORDER BY i.created_at DESC
                    """,
                    (applicant_id, guild_id),
                )
            else:
                cursor = await db.execute(
                    """
                    SELECT i.*, ar.fit_score, ar.recommended
                    FROM interviews i
                    LEFT JOIN analysis_results ar ON i.id = ar.interview_id
                    WHERE i.applicant_id = ?
                    ORDER BY i.created_at DESC
                    """,
                    (applicant_id,),
                )
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_stats(self, guild_id: int) -> dict:
        """
        Get interview statistics for a guild.
        
        Args:
            guild_id: Discord server ID
            
        Returns:
            Stats dict
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Total interviews
            cursor = await db.execute(
                "SELECT COUNT(*) FROM interviews WHERE guild_id = ?",
                (guild_id,),
            )
            total = (await cursor.fetchone())[0]

            # Average fit score
            cursor = await db.execute(
                """
                SELECT AVG(ar.fit_score)
                FROM interviews i
                JOIN analysis_results ar ON i.id = ar.interview_id
                WHERE i.guild_id = ?
                """,
                (guild_id,),
            )
            avg_score = (await cursor.fetchone())[0] or 0

            # Recommended count
            cursor = await db.execute(
                """
                SELECT COUNT(*)
                FROM interviews i
                JOIN analysis_results ar ON i.id = ar.interview_id
                WHERE i.guild_id = ? AND ar.recommended = 1
                """,
                (guild_id,),
            )
            recommended = (await cursor.fetchone())[0]

            return {
                "total_interviews": total,
                "avg_fit_score": avg_score,
                "recommended_count": recommended,
                "recommendation_rate": (recommended / total * 100) if total > 0 else 0,
            }

    async def delete_interview(self, interview_id: int) -> bool:
        """
        Delete an interview and its analysis.
        
        Args:
            interview_id: Interview ID
            
        Returns:
            True if deleted
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Delete analysis first (foreign key)
            await db.execute(
                "DELETE FROM analysis_results WHERE interview_id = ?",
                (interview_id,),
            )
            
            # Delete interview
            cursor = await db.execute(
                "DELETE FROM interviews WHERE id = ?",
                (interview_id,),
            )
            await db.commit()
            
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Deleted interview #{interview_id}")
            return deleted

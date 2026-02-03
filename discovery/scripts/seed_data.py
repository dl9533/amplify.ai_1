#!/usr/bin/env python3
"""Seed the database with test data for development/demo purposes.

This script:
1. Creates test O*NET occupation records
2. Creates a test user and organization
3. Creates sample discovery sessions with data
"""
import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.base import Base
from app.models.onet import OnetOccupation, OnetGWA, OnetDWA
from app.models.session import DiscoverySession, SessionStatus
from app.models.role_mapping import RoleMapping
from app.models.activity_selection import ActivitySelection
from app.models.analysis import AnalysisResult, AnalysisDimension, PriorityTier
from app.models.candidate import Candidate, CandidatePhase


# Test O*NET occupations with AI exposure scores
ONET_OCCUPATIONS = [
    ("15-1252.00", "Software Developers", 0.72),
    ("15-1253.00", "Software Quality Assurance Analysts and Testers", 0.68),
    ("15-1254.00", "Web Developers", 0.65),
    ("15-2051.00", "Data Scientists", 0.78),
    ("15-2041.00", "Statisticians", 0.75),
    ("13-1111.00", "Management Analysts", 0.62),
    ("13-2011.00", "Accountants and Auditors", 0.58),
    ("11-1021.00", "General and Operations Managers", 0.45),
    ("11-2021.00", "Marketing Managers", 0.52),
    ("11-3021.00", "Computer and Information Systems Managers", 0.48),
    ("43-4051.00", "Customer Service Representatives", 0.70),
    ("27-3031.00", "Public Relations Specialists", 0.55),
    ("13-1161.00", "Market Research Analysts", 0.68),
    ("15-1211.00", "Computer Systems Analysts", 0.65),
    ("15-1299.08", "Computer and Information Research Scientists", 0.82),
]

# Test GWAs (Generalized Work Activities) with AI exposure scores
GWAS = [
    ("4.A.1.a.1", "Getting Information", 0.75),
    ("4.A.1.b.2", "Processing Information", 0.82),
    ("4.A.2.a.4", "Analyzing Data or Information", 0.85),
    ("4.A.2.b.2", "Making Decisions and Solving Problems", 0.60),
    ("4.A.3.a.1", "Scheduling Work and Activities", 0.55),
    ("4.A.3.b.4", "Organizing, Planning, and Prioritizing Work", 0.52),
    ("4.A.4.a.1", "Communicating with Supervisors", 0.40),
    ("4.A.4.a.5", "Communicating with People Outside Organization", 0.45),
    ("4.A.4.b.4", "Establishing and Maintaining Relationships", 0.35),
]

# Test DWAs (Detailed Work Activities) mapped to GWAs
DWAS = [
    ("2.B.1.a", "Analyze business data", "4.A.2.a.4", 0.88),
    ("2.B.1.b", "Compile data for reports", "4.A.1.b.2", 0.90),
    ("2.B.1.c", "Review documents for accuracy", "4.A.1.b.2", 0.75),
    ("2.B.2.a", "Calculate financial metrics", "4.A.2.a.4", 0.85),
    ("2.B.2.b", "Interpret statistical results", "4.A.2.a.4", 0.78),
    ("2.C.1.a", "Draft correspondence", "4.A.4.a.5", 0.72),
    ("2.C.1.b", "Prepare presentations", "4.A.4.a.1", 0.65),
    ("2.C.2.a", "Coordinate team meetings", "4.A.3.a.1", 0.45),
    ("2.C.2.b", "Negotiate contracts", "4.A.4.b.4", 0.38),
]


async def seed_database():
    """Seed the database with test data."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=True)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Check if already seeded
        result = await session.execute(
            text("SELECT COUNT(*) FROM onet_occupations")
        )
        count = result.scalar()
        if count and count > 0:
            print(f"Database already has {count} occupations. Skipping seed.")
            return

        print("Seeding O*NET occupations...")
        for code, title, exposure in ONET_OCCUPATIONS:
            occupation = OnetOccupation(
                code=code,
                title=title,
                description=f"Description for {title}",
                ai_exposure_score=exposure,
            )
            session.add(occupation)

        print("Seeding GWAs...")
        for code, title, exposure in GWAS:
            gwa = OnetGWA(
                code=code,
                title=title,
                ai_exposure_score=exposure,
            )
            session.add(gwa)

        print("Seeding DWAs...")
        for code, title, gwa_code, exposure in DWAS:
            dwa = OnetDWA(
                code=code,
                title=title,
                gwa_code=gwa_code,
                ai_exposure_score=exposure,
            )
            session.add(dwa)

        await session.commit()

        # Create test session with data
        print("Creating test discovery session...")
        test_user_id = uuid4()
        test_org_id = uuid4()

        test_session = DiscoverySession(
            id=uuid4(),
            user_id=test_user_id,
            organization_id=test_org_id,
            status=SessionStatus.IN_PROGRESS,
            current_step=3,
        )
        session.add(test_session)
        await session.flush()

        # Add role mappings
        print("Adding role mappings...")
        role_mappings_data = [
            ("Software Engineer", "15-1252.00", "Software Developers", 0.95),
            ("Data Analyst", "15-2051.00", "Data Scientists", 0.87),
            ("Product Manager", "11-1021.00", "General and Operations Managers", 0.78),
            ("UX Designer", "27-3031.00", "Public Relations Specialists", 0.72),
            ("Customer Support Specialist", "43-4051.00", "Customer Service Representatives", 0.92),
        ]

        role_mapping_ids = []
        for role_name, onet_code, onet_title, confidence in role_mappings_data:
            mapping = RoleMapping(
                id=uuid4(),
                session_id=test_session.id,
                source_role=role_name,
                onet_code=onet_code,
                onet_title=onet_title,
                confidence_score=confidence,
                is_confirmed=confidence > 0.85,
            )
            session.add(mapping)
            role_mapping_ids.append(mapping.id)

        await session.flush()

        # Add activity selections
        print("Adding activity selections...")
        for i, (dwa_code, dwa_title, gwa_code, exposure) in enumerate(DWAS[:5]):
            selection = ActivitySelection(
                id=uuid4(),
                session_id=test_session.id,
                role_mapping_id=role_mapping_ids[i % len(role_mapping_ids)],
                dwa_code=dwa_code,
                selected=exposure > 0.70,
            )
            session.add(selection)

        # Add analysis results
        print("Adding analysis results...")
        analysis_data = [
            ("Software Engineer", AnalysisDimension.ROLE, 0.72, 0.85, 0.28, 0.80, PriorityTier.HIGH),
            ("Data Analyst", AnalysisDimension.ROLE, 0.78, 0.70, 0.22, 0.75, PriorityTier.HIGH),
            ("Product Manager", AnalysisDimension.ROLE, 0.45, 0.60, 0.55, 0.52, PriorityTier.MEDIUM),
            ("Engineering", AnalysisDimension.DEPARTMENT, 0.70, 0.82, 0.30, 0.78, PriorityTier.HIGH),
            ("Operations", AnalysisDimension.DEPARTMENT, 0.52, 0.58, 0.48, 0.55, PriorityTier.MEDIUM),
            ("New York", AnalysisDimension.GEOGRAPHY, 0.68, 0.75, 0.32, 0.72, PriorityTier.MEDIUM),
        ]

        for name, dimension, exposure, impact, complexity, priority, tier in analysis_data:
            result = AnalysisResult(
                id=uuid4(),
                session_id=test_session.id,
                name=name,
                dimension=dimension,
                ai_exposure_score=exposure,
                impact_score=impact,
                complexity_score=complexity,
                priority_score=priority,
                priority_tier=tier,
            )
            session.add(result)

        # Add roadmap candidates
        print("Adding roadmap candidates...")
        candidates_data = [
            ("Software Engineer Agent", 0.80, PriorityTier.HIGH, CandidatePhase.NOW, "medium"),
            ("Data Analysis Agent", 0.75, PriorityTier.HIGH, CandidatePhase.NOW, "high"),
            ("Customer Support Agent", 0.68, PriorityTier.MEDIUM, CandidatePhase.NEXT, "low"),
            ("Report Generation Agent", 0.62, PriorityTier.MEDIUM, CandidatePhase.NEXT, "medium"),
            ("Scheduling Assistant", 0.55, PriorityTier.LOW, CandidatePhase.LATER, "low"),
        ]

        for name, priority, tier, phase, effort in candidates_data:
            candidate = Candidate(
                id=uuid4(),
                session_id=test_session.id,
                role_name=name,
                priority_score=priority,
                priority_tier=tier.value,
                phase=phase,
                estimated_effort=effort,
            )
            session.add(candidate)

        await session.commit()
        print(f"\n✅ Database seeded successfully!")
        print(f"   Test session ID: {test_session.id}")
        print(f"   Test user ID: {test_user_id}")
        print(f"   Test org ID: {test_org_id}")


if __name__ == "__main__":
    asyncio.run(seed_database())

"""Seed GWA data with Pew Research AI exposure scores.

This migration populates the onet_gwas table with the 41 Generalized Work
Activities from O*NET and their corresponding AI exposure scores based on
Pew Research analysis.

AI Exposure Scores (0.0-1.0):
- Higher scores indicate activities more susceptible to AI automation
- Scores derived from Pew Research analysis of AI impact on work activities

Revision ID: 073_discovery_gwa_seed
Revises: 072_discovery_memory_tables
Create Date: 2026-01-31
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "073_discovery_gwa_seed"
down_revision: str | None = "072_discovery_memory_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# GWA seed data: (id, name, description, ai_exposure_score)
# 41 Generalized Work Activities with Pew Research AI exposure scores
GWA_SEED_DATA = [
    # Information Input (4.A.1)
    (
        "4.A.1.a.1",
        "Getting Information",
        "Observing, receiving, and otherwise obtaining information from all relevant sources.",
        0.85,
    ),
    (
        "4.A.1.a.2",
        "Monitor Processes, Materials, or Surroundings",
        "Monitoring and reviewing information from materials, events, or the environment.",
        0.70,
    ),
    (
        "4.A.1.b.1",
        "Identify Objects, Actions, and Events",
        "Identifying information by categorizing, estimating, recognizing differences or similarities.",
        0.75,
    ),
    (
        "4.A.1.b.2",
        "Estimating Quantifiable Characteristics",
        "Estimating sizes, distances, and quantities; determining time, costs, resources, or materials.",
        0.75,
    ),
    (
        "4.A.1.b.3",
        "Judging Qualities",
        "Judging the qualities of things, services, or people.",
        0.55,
    ),
    # Mental Processes (4.A.2)
    (
        "4.A.2.a.1",
        "Analyzing Data or Information",
        "Identifying the underlying principles, reasons, or facts of information.",
        0.90,
    ),
    (
        "4.A.2.a.2",
        "Making Decisions and Solving Problems",
        "Analyzing information and evaluating results to choose the best solution.",
        0.65,
    ),
    (
        "4.A.2.a.3",
        "Thinking Creatively",
        "Developing, designing, or creating new applications, ideas, relationships, systems, or products.",
        0.40,
    ),
    (
        "4.A.2.a.4",
        "Updating and Using Relevant Knowledge",
        "Keeping up-to-date technically and applying new knowledge to your job.",
        0.80,
    ),
    (
        "4.A.2.b.1",
        "Developing Objectives and Strategies",
        "Establishing long-range objectives and specifying the strategies and actions to achieve them.",
        0.55,
    ),
    (
        "4.A.2.b.2",
        "Scheduling Work and Activities",
        "Scheduling events, programs, and activities, as well as the work of others.",
        0.75,
    ),
    (
        "4.A.2.b.3",
        "Organizing, Planning, and Prioritizing",
        "Developing specific goals and plans to prioritize, organize, and accomplish your work.",
        0.70,
    ),
    (
        "4.A.2.b.4",
        "Processing Information",
        "Compiling, coding, categorizing, calculating, tabulating, auditing, or verifying information.",
        0.85,
    ),
    (
        "4.A.2.b.5",
        "Evaluating Information",
        "Determining compliance with standards and evaluating information against criteria.",
        0.80,
    ),
    # Work Output (4.A.3)
    (
        "4.A.3.a.1",
        "Performing General Physical Activities",
        "Performing physical activities that require considerable use of arms and legs.",
        0.20,
    ),
    (
        "4.A.3.a.2",
        "Handling and Moving Objects",
        "Using hands and arms in handling, installing, positioning, and moving materials.",
        0.35,
    ),
    (
        "4.A.3.a.3",
        "Controlling Machines and Processes",
        "Using either control mechanisms or direct physical activity to operate machines or processes.",
        0.50,
    ),
    (
        "4.A.3.a.4",
        "Operating Vehicles or Equipment",
        "Running, maneuvering, navigating, or driving vehicles or mechanized equipment.",
        0.45,
    ),
    (
        "4.A.3.b.1",
        "Interacting With Computers",
        "Using computers and computer systems to program, write software, set up functions, enter data.",
        0.85,
    ),
    (
        "4.A.3.b.2",
        "Drafting, Laying Out, and Specifying",
        "Providing documentation, detailed instructions, drawings, or specifications.",
        0.70,
    ),
    (
        "4.A.3.b.3",
        "Inspecting Equipment",
        "Inspecting equipment, structures, or materials to identify problems or defects.",
        0.40,
    ),
    (
        "4.A.3.b.4",
        "Repairing and Maintaining Equipment",
        "Servicing, repairing, adjusting, and testing machines, devices, and equipment.",
        0.30,
    ),
    (
        "4.A.3.b.5",
        "Repairing and Maintaining Mechanical Equipment",
        "Servicing, repairing, adjusting, and testing machines, devices, moving parts, and equipment.",
        0.25,
    ),
    (
        "4.A.3.b.6",
        "Documenting/Recording Information",
        "Entering, transcribing, recording, storing, or maintaining information in written or electronic form.",
        0.90,
    ),
    # Interacting with Others (4.A.4)
    (
        "4.A.4.a.1",
        "Interpreting Meaning of Information",
        "Translating or explaining what information means and how it can be used.",
        0.80,
    ),
    (
        "4.A.4.a.2",
        "Communicating with Supervisors or Peers",
        "Providing information to supervisors, co-workers, and subordinates by telephone, written form, or in person.",
        0.55,
    ),
    (
        "4.A.4.a.3",
        "Communicating with Outside Organizations",
        "Communicating with people outside the organization representing the organization to customers and the public.",
        0.50,
    ),
    (
        "4.A.4.a.4",
        "Establishing and Maintaining Relationships",
        "Developing constructive and cooperative working relationships with others.",
        0.30,
    ),
    (
        "4.A.4.a.5",
        "Assisting and Caring for Others",
        "Providing personal assistance, medical attention, emotional support, or other personal care.",
        0.25,
    ),
    (
        "4.A.4.a.6",
        "Selling or Influencing Others",
        "Convincing others to buy merchandise or goods or to otherwise change their minds or actions.",
        0.45,
    ),
    (
        "4.A.4.a.7",
        "Resolving Conflicts and Negotiating",
        "Handling complaints, settling disputes, and resolving grievances and conflicts.",
        0.35,
    ),
    (
        "4.A.4.a.8",
        "Performing for or Working with Public",
        "Performing for people or dealing directly with the public.",
        0.30,
    ),
    (
        "4.A.4.b.1",
        "Coordinating Work of Others",
        "Getting members of a group to work together to accomplish tasks.",
        0.55,
    ),
    (
        "4.A.4.b.2",
        "Developing and Building Teams",
        "Encouraging and building mutual trust, respect, and cooperation among team members.",
        0.35,
    ),
    (
        "4.A.4.b.3",
        "Training and Teaching Others",
        "Identifying the educational needs of others, developing programs or classes, and teaching.",
        0.50,
    ),
    (
        "4.A.4.b.4",
        "Guiding, Directing, and Motivating",
        "Providing guidance and direction to subordinates, including setting performance standards.",
        0.35,
    ),
    (
        "4.A.4.b.5",
        "Coaching and Developing Others",
        "Identifying the developmental needs of others and coaching, mentoring, or helping them improve.",
        0.40,
    ),
    (
        "4.A.4.b.6",
        "Provide Consultation and Advice",
        "Providing guidance and expert advice to management or other groups on various subjects.",
        0.55,
    ),
    (
        "4.A.4.c.1",
        "Performing Administrative Activities",
        "Performing day-to-day administrative tasks such as maintaining files and processing paperwork.",
        0.80,
    ),
    (
        "4.A.4.c.2",
        "Staffing Organizational Units",
        "Recruiting, interviewing, selecting, hiring, and promoting employees in an organization.",
        0.60,
    ),
    (
        "4.A.4.c.3",
        "Monitoring and Controlling Resources",
        "Monitoring and controlling resources and overseeing the spending of money.",
        0.70,
    ),
]


def upgrade() -> None:
    """Insert 41 GWA records with Pew Research AI exposure scores."""
    # Build the insert statement with all GWA data
    gwa_table = "onet_gwas"

    # Insert each GWA record
    for gwa_id, name, description, ai_exposure_score in GWA_SEED_DATA:
        op.execute(
            f"""
            INSERT INTO {gwa_table} (id, name, description, ai_exposure_score)
            VALUES ('{gwa_id}', '{name.replace("'", "''")}', '{description.replace("'", "''")}', {ai_exposure_score})
            """
        )


def downgrade() -> None:
    """Remove all seeded GWA records."""
    # Delete all records that were seeded
    gwa_ids = [gwa[0] for gwa in GWA_SEED_DATA]
    ids_str = ", ".join(f"'{gwa_id}'" for gwa_id in gwa_ids)
    op.execute(f"DELETE FROM onet_gwas WHERE id IN ({ids_str})")

#!/usr/bin/env python3
"""
Seed demo data for VenturePulse v2.

Creates a demo user and loads sample project specs as public projects.
Can be run standalone or as part of Docker setup.

Usage:
    python scripts/seed-demo-data.py [--reset]

Options:
    --reset    Delete existing demo data before seeding
"""

import asyncio
import os
import re
import sys
from pathlib import Path
from datetime import datetime

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, User, Project
from app.config import get_settings


settings = get_settings()

# Demo user configuration
DEMO_USER = {
    "email": "demo@venturepulse.example.com",
    "name": "Demo User",
    "avatar_url": None,
    "provider": "demo",
    "provider_id": "demo-user-001",
    "role": "approved",  # Approved so projects can be created
}


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text


def extract_project_info(content: str, filename: str) -> dict:
    """Extract project name and description from markdown content."""
    lines = content.strip().split('\n')

    # Extract title from first # heading
    name = filename.replace('.md', '').replace('-', ' ').title()
    for line in lines[:5]:
        if line.startswith('# '):
            name = line[2:].strip()
            break

    # Extract description from first paragraph after title or "Product Vision" section
    description = ""
    in_vision = False
    for i, line in enumerate(lines):
        if '## Product Vision' in line or '## Overview' in line:
            in_vision = True
            continue
        if in_vision and line.strip() and not line.startswith('#'):
            description = line.strip()
            break
        if i > 0 and not description and lines[i-1].startswith('# ') and line.strip():
            description = line.strip()
            break

    if not description and len(lines) > 2:
        for line in lines[2:10]:
            if line.strip() and not line.startswith('#'):
                description = line.strip()[:200]
                break

    return {
        "name": name,
        "description": description or f"Sample project from {filename}",
    }


async def seed_demo_data(reset: bool = False):
    """Main seeding function."""
    print("VenturePulse v2 - Demo Data Seeding")
    print("=" * 50)

    # Create async engine
    db_path = settings.BASE_DIR / "data" / "venturepulse.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        # Create tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Check for existing demo user
        result = await session.execute(
            select(User).where(User.email == DEMO_USER["email"])
        )
        demo_user = result.scalar_one_or_none()

        if reset and demo_user:
            print(f"\n[RESET] Deleting existing demo user and projects...")
            # Delete user (cascades to projects and analyses)
            await session.delete(demo_user)
            await session.commit()
            demo_user = None
            print("[RESET] Demo data deleted.")

        # Create demo user if needed
        if not demo_user:
            print(f"\n[USER] Creating demo user: {DEMO_USER['email']}")
            demo_user = User(
                email=DEMO_USER["email"],
                name=DEMO_USER["name"],
                avatar_url=DEMO_USER["avatar_url"],
                provider=DEMO_USER["provider"],
                provider_id=DEMO_USER["provider_id"],
                role=DEMO_USER["role"],
            )
            session.add(demo_user)
            await session.commit()
            await session.refresh(demo_user)
            print(f"[USER] Demo user created with ID: {demo_user.id}")
        else:
            print(f"\n[USER] Demo user already exists with ID: {demo_user.id}")

        # Load sample specs
        sample_specs_dir = settings.BASE_DIR / "sample-specs"
        if not sample_specs_dir.exists():
            print(f"\n[WARN] Sample specs directory not found: {sample_specs_dir}")
            return

        print(f"\n[PROJECTS] Loading sample specs from: {sample_specs_dir}")

        # Get existing project slugs for this user
        result = await session.execute(
            select(Project.slug).where(Project.user_id == demo_user.id)
        )
        existing_slugs = {row[0] for row in result.fetchall()}

        projects_created = 0
        projects_skipped = 0

        # Iterate through category folders
        for category_dir in sorted(sample_specs_dir.iterdir()):
            if not category_dir.is_dir():
                continue

            category = category_dir.name
            print(f"\n  Category: {category}")

            for spec_file in sorted(category_dir.glob("*.md")):
                # Read spec content
                spec_content = spec_file.read_text(encoding="utf-8")

                # Extract project info
                info = extract_project_info(spec_content, spec_file.name)
                slug = slugify(info["name"])

                # Add category prefix to make slugs unique
                slug = f"{slugify(category)}-{slug}"

                if slug in existing_slugs:
                    print(f"    [SKIP] {info['name']} (already exists)")
                    projects_skipped += 1
                    continue

                # Create specs directory for user if needed
                specs_dir = settings.BASE_DIR / "data" / "specs" / str(demo_user.id)
                specs_dir.mkdir(parents=True, exist_ok=True)

                # Save spec file
                spec_path = specs_dir / f"{slug}.md"
                spec_path.write_text(spec_content, encoding="utf-8")

                # Create project
                project = Project(
                    user_id=demo_user.id,
                    name=info["name"],
                    slug=slug,
                    description=info["description"],
                    spec_content=spec_content,
                    spec_file_path=f"data/specs/{demo_user.id}/{slug}.md",
                    is_public=True,  # Sample projects are public
                )
                session.add(project)

                print(f"    [CREATE] {info['name']}")
                projects_created += 1

        await session.commit()

        # Summary
        print("\n" + "=" * 50)
        print(f"[DONE] Seeding complete!")
        print(f"       Projects created: {projects_created}")
        print(f"       Projects skipped: {projects_skipped}")
        print(f"       Demo user email: {DEMO_USER['email']}")
        print("\n[NOTE] The demo user cannot log in via OAuth.")
        print("       These projects are public and can be viewed by anyone.")


async def main():
    """Entry point."""
    reset = "--reset" in sys.argv

    if reset:
        print("\n[WARN] Reset mode enabled - existing demo data will be deleted!")
        response = input("Continue? [y/N] ")
        if response.lower() != 'y':
            print("Aborted.")
            return

    await seed_demo_data(reset=reset)


if __name__ == "__main__":
    asyncio.run(main())

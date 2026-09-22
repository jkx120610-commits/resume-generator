from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class EducationEntry:
    school: str = ""
    date_range: str = ""
    major: str = ""
    details: str = ""


@dataclass(slots=True)
class SkillEntry:
    name: str = ""
    level: str = "熟练"
    score: int = 80


@dataclass(slots=True)
class ResumeData:
    name: str = ""
    job_target: str = ""
    city: str = ""
    work_years: str = ""
    availability: str = ""
    birth_date: str = ""
    political_status: str = ""
    highest_education: str = ""
    current_address: str = ""
    educations: list[EducationEntry] = field(
        default_factory=lambda: [EducationEntry(), EducationEntry()]
    )
    skills: list[SkillEntry] = field(
        default_factory=lambda: [
            SkillEntry(name="", level="熟练", score=92),
            SkillEntry(name="", level="熟练", score=85),
            SkillEntry(name="", level="掌握", score=78),
            SkillEntry(name="", level="了解", score=68),
        ]
    )
    skill_tags: list[str] = field(default_factory=list)
    phone: str = ""
    email: str = ""
    portfolio: str = ""
    contact_address: str = ""
    evaluation: str = ""
    photo_path: str = ""
    copyright_year: str = ""


@dataclass(slots=True)
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


@dataclass(slots=True)
class GeneratedFiles:
    image_path: Path
    pdf_path: Path

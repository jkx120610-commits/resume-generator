"""Resume Generator desktop application."""

from .models import EducationEntry, ResumeData, SkillEntry, ValidationResult
from .validator import validate_resume

__all__ = [
    "EducationEntry",
    "ResumeData",
    "SkillEntry",
    "ValidationResult",
    "validate_resume",
]

__version__ = "1.0.0"

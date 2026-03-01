"""Data models for BharatSahayak."""

from .eligibility import EligibilityCriteria
from .impact import InteractionEvent, OutcomeEvent
from .location import Location
from .scheme import Scheme
from .skill import JobPosting, SkillProgram
from .user import UserPreferences, UserProfile

__all__ = [
    "EligibilityCriteria",
    "InteractionEvent",
    "JobPosting",
    "Location",
    "OutcomeEvent",
    "Scheme",
    "SkillProgram",
    "UserPreferences",
    "UserProfile",
]

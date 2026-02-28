"""Skills and Employment models"""
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, Numeric, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from app.database import Base


class SkillProgram(Base):
    """Skill development program information"""
    __tablename__ = "skill_programs"
    
    program_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    provider = Column(String(100), nullable=True)
    category = Column(String(50), nullable=False, index=True)  # technical, vocational, digital, entrepreneurship
    description = Column(Text, nullable=True)
    duration_weeks = Column(Integer, nullable=True)
    cost = Column(Numeric(10, 2), nullable=True)
    
    # Location
    state = Column(String(50), nullable=True, index=True)
    district = Column(String(50), nullable=True, index=True)
    
    mode = Column(String(20), nullable=True)  # in-person, online, hybrid
    eligibility_criteria = Column(JSONB, nullable=True)
    certification = Column(Boolean, default=False)
    placement_support = Column(Boolean, default=False)
    registration_url = Column(String(500), nullable=True)
    contact = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class JobPosting(Base):
    """Government job posting information"""
    __tablename__ = "job_postings"
    
    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, index=True)
    department = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=True)
    qualifications = Column(JSONB, nullable=True)  # education, experience requirements
    location = Column(JSONB, nullable=True)  # state, district, multiple locations
    application_deadline = Column(Date, nullable=True, index=True)
    application_url = Column(String(500), nullable=True)
    posted_date = Column(Date, nullable=True)
    
    last_updated = Column(DateTime, nullable=True)  # When job posting data was last verified/updated
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

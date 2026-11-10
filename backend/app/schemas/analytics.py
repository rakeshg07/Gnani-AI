"""Pydantic schemas for database-backed dashboard statistics."""
from typing import Dict, List, Optional
from pydantic import BaseModel


class LanguageStat(BaseModel):
    code: str
    name: str
    count: int
    percentage: float


class SentimentDistribution(BaseModel):
    positive: int = 0
    neutral: int = 0
    negative: int = 0
    frustrated: int = 0


class EscalationDistribution(BaseModel):
    none: int = 0
    low: int = 0
    medium: int = 0
    high: int = 0
    critical: int = 0


class DashboardStats(BaseModel):
    total_conversations: int
    completed_conversations: int
    processing_conversations: int
    failed_conversations: int
    success_rate_percentage: float
    avg_duration_seconds: float
    total_insights_generated: int
    escalated_cases_count: int
    language_distribution: List[LanguageStat]
    sentiment_distribution: SentimentDistribution
    escalation_distribution: EscalationDistribution

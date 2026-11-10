"""Pydantic schemas for Conversation Intelligence and Insights."""
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class ActionItem(BaseModel):
    task: str = Field(..., description="Actionable task description")
    assignee: str = Field(default="Support Agent", description="Owner of the action item (Agent, Billing, Logistics, Tech Support)")
    priority: str = Field(default="medium", description="Priority level: low, medium, high, urgent")
    status: str = Field(default="pending", description="Status: pending, in_progress, completed")


class CustomerCommitment(BaseModel):
    promise: str = Field(..., description="Specific commitment or promise made to customer")
    deadline: Optional[str] = Field(default=None, description="Timeframe or deadline communicated to customer")
    made_by: str = Field(default="Support Representative", description="Party who committed")


class ConversationInsightBase(BaseModel):
    summary: str = Field(..., description="Executive summary of the customer support interaction")
    customer_intent: str = Field(..., description="Primary customer intent (e.g., Order Inquiry, Payment Failure, Return Request)")
    primary_issue: str = Field(..., description="Core issue or question raised by customer")
    action_items: List[ActionItem] = Field(default_factory=list, description="Extracted actionable tasks")
    commitments: List[CustomerCommitment] = Field(default_factory=list, description="Explicit promises made to the customer")
    resolution_status: str = Field(default="pending_action", description="Status: resolved, unresolved, escalated, pending_action")
    escalation_level: str = Field(default="low", description="Escalation risk level: none, low, medium, high, critical")
    escalation_reason: Optional[str] = Field(default=None, description="Explanation for escalation recommendation")
    sentiment_label: str = Field(default="neutral", description="Sentiment label: positive, neutral, negative, frustrated")
    sentiment_score: float = Field(default=0.0, ge=-1.0, le=1.0, description="Normalized sentiment polarity (-1.0 to 1.0)")
    frustration_index: float = Field(default=0.0, ge=0.0, le=1.0, description="Customer frustration metric (0.0 to 1.0)")


class ConversationInsightCreate(ConversationInsightBase):
    pass


class ConversationInsightRead(ConversationInsightBase):
    id: str
    conversation_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AnalyzeRequest(BaseModel):
    force_reanalyze: bool = Field(default=False, description="Re-run conversation intelligence if insights already exist")

"""Conversation Intelligence Engine for extracting structured insights from support transcripts."""
import re
from typing import List, Dict, Any, Tuple
from app.schemas.insights import (
    ConversationInsightCreate,
    ActionItem,
    CustomerCommitment,
)
from app.core.logging import logger

# Domain intent detection keywords (English + Indian context / Hinglish terms)
INTENT_PATTERNS = [
    (
        "Order Delivery & Tracking",
        [
            r"\b(delivery|deliver|parcel|package|tracking|courier|where is my order|order status|delayed|late|shipped)\b",
            r"\b(डिलीवरी|पार्सल|ऑर्डर|लेट|कब आएगा)\b",
        ],
    ),
    (
        "Refund & Payment Issue",
        [
            r"\b(refund|money back|charged twice|deducted|payment failed|upi|cashback|bill|invoice)\b",
            r"\b(रिफंड|पैसे|कटा|वापस|पेमेंट)\b",
        ],
    ),
    (
        "Return & Replacement",
        [
            r"\b(return|replace|damaged|broken|wrong item|defective|size issue|exchange)\b",
            r"\b(खराब|टूटा|वापस करना|बदलना|गलत सामान)\b",
        ],
    ),
    (
        "Technical & App Support",
        [
            r"\b(app|login|otp|password|error|crashing|bug|account locked|website not working)\b",
            r"\b(लॉगिन|ओटीपी|एरर|पासवर्ड)\b",
        ],
    ),
    (
        "Cancellation Request",
        [
            r"\b(cancel|cancellation|stop order|dont want|abort)\b",
            r"\b(कैंसिल|रद्द)\b",
        ],
    ),
    (
        "Product & General Inquiry",
        [
            r"\b(price|discount|availability|stock|specifications|warranty|how to)\b",
        ],
    ),
]

# Frustration markers for Indian customer support context
FRUSTRATION_PATTERNS = [
    (1.0, r"\b(cheat|scam|fraud|police|consumer court|lawyer|sue|legal action)\b"),
    (0.8, r"\b(terrible|horrible|useless|pathetic|worst|ridiculous|waste of time|fed up)\b"),
    (0.6, r"\b(calling again|third time|fourth time|multiple times|no one responded|waiting for days)\b"),
    (0.5, r"\b(angry|frustrated|irritated|disappointed|urgent|asap|immediately)\b"),
    (0.4, r"\b(not happy|bad experience|unacceptable|problem not solved)\b"),
]

POSITIVE_PATTERNS = [
    r"\b(thank you|thanks|helpful|appreciate|great service|resolved|awesome|good job|dhanyavaad|shukriya)\b",
    r"\b(धन्यवाद|शुक्रिया|बहुत अच्छा)\b",
]

COMMITMENT_PATTERNS = [
    (r"\b(?:will|shall)\s+(?:deliver|arrive|reach)\s+(?:by|on|before)\s+([^.,;\n]+)", "Delivery confirmation"),
    (r"\b(?:refund|money)\s+will\s+be\s+(?:credited|processed|initiated)\s+(?:in|within)\s+([^.,;\n]+)", "Refund processing"),
    (r"\b(?:call you back|callback|update you)\s+(?:in|within|by)\s+([^.,;\n]+)", "Follow-up callback"),
    (r"\b(?:ticket|complaint)\s+(?:has been|is)\s+raised\b", "Support ticket opened"),
]


class ConversationAnalysisService:
    """Extracts structured intelligence, intents, action items, commitments, and sentiment."""

    def analyze_transcript(
        self,
        transcript: str,
        filename: str = "",
        language_code: str = "en-IN",
    ) -> ConversationInsightCreate:
        """
        Parses customer-support transcript and returns a validated ConversationInsightCreate schema.
        Handles bilingual Indian support interactions seamlessly.
        """
        if not transcript or not transcript.strip():
            logger.warning("Empty transcript provided to analysis service.")
            return ConversationInsightCreate(
                summary="No speech detected in this recording.",
                customer_intent="Indeterminate",
                primary_issue="Audio recording did not contain audible conversational speech.",
                action_items=[],
                commitments=[],
                resolution_status="unresolved",
                escalation_level="none",
                escalation_reason="Transcript is empty.",
                sentiment_label="neutral",
                sentiment_score=0.0,
                frustration_index=0.0,
            )

        text_lower = transcript.lower()

        # 1. Determine Customer Intent
        intent = self._extract_intent(text_lower)

        # 2. Extract Primary Issue
        primary_issue = self._extract_primary_issue(transcript, intent)

        # 3. Calculate Sentiment and Frustration
        sentiment_label, sentiment_score, frustration_index = self._analyze_sentiment(text_lower)

        # 4. Extract Commitments / Promises
        commitments = self._extract_commitments(transcript)

        # 5. Extract Action Items
        action_items = self._extract_action_items(transcript, intent, frustration_index)

        # 6. Determine Resolution & Escalation
        resolution_status, escalation_level, escalation_reason = self._determine_escalation(
            frustration_index, sentiment_score, action_items
        )

        # 7. Generate Executive Summary
        summary = self._generate_summary(intent, primary_issue, resolution_status, action_items, commitments)

        return ConversationInsightCreate(
            summary=summary,
            customer_intent=intent,
            primary_issue=primary_issue,
            action_items=action_items,
            commitments=commitments,
            resolution_status=resolution_status,
            escalation_level=escalation_level,
            escalation_reason=escalation_reason,
            sentiment_label=sentiment_label,
            sentiment_score=round(sentiment_score, 2),
            frustration_index=round(frustration_index, 2),
        )

    def _extract_intent(self, text: str) -> str:
        for intent_name, patterns in INTENT_PATTERNS:
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return intent_name
        return "Customer Service General Inquiry"

    def _extract_primary_issue(self, transcript: str, intent: str) -> str:
        sentences = [s.strip() for s in re.split(r"[.!?\n]+", transcript) if len(s.strip()) > 10]
        # Look for customer problem statement in initial sentences
        for sentence in sentences[:3]:
            if any(k in sentence.lower() for k in ["delay", "not received", "cancel", "wrong", "broken", "issue", "problem", "money", "help"]):
                return sentence
        if sentences:
            return sentences[0]
        return f"Customer reached out regarding {intent.lower()}."

    def _analyze_sentiment(self, text: str) -> Tuple[str, float, float]:
        frustration_weight = 0.0
        for weight, pattern in FRUSTRATION_PATTERNS:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            if matches > 0:
                frustration_weight = min(1.0, frustration_weight + weight * min(matches, 2) * 0.7)

        positive_count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in POSITIVE_PATTERNS)
        
        # Calculate sentiment polarity (-1.0 to 1.0)
        if frustration_weight > 0.4:
            sentiment_score = -min(1.0, frustration_weight)
            sentiment_label = "frustrated" if frustration_weight >= 0.65 else "negative"
        elif frustration_weight > 0.15:
            sentiment_score = -0.3
            sentiment_label = "negative"
        elif positive_count > 0:
            sentiment_score = min(1.0, 0.3 + positive_count * 0.3)
            sentiment_label = "positive"
        else:
            sentiment_score = 0.0
            sentiment_label = "neutral"

        return sentiment_label, sentiment_score, frustration_weight

    def _extract_commitments(self, transcript: str) -> List[CustomerCommitment]:
        commitments: List[CustomerCommitment] = []
        for pattern, label in COMMITMENT_PATTERNS:
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                timeframe = match.group(1).strip() if match.groups() else "As soon as possible"
                commitments.append(
                    CustomerCommitment(
                        promise=f"{label}: {match.group(0).strip()}",
                        deadline=timeframe[:60],
                        made_by="Support Agent",
                    )
                )

        if not commitments:
            # Default reassurance if explicit regex misses
            if "ticket" in transcript.lower() or "reference" in transcript.lower():
                commitments.append(
                    CustomerCommitment(
                        promise="Service request ticket logged in internal CRM",
                        deadline="Within standard SLA (24-48 hours)",
                        made_by="Customer Support Representative",
                    )
                )

        return commitments

    def _extract_action_items(self, transcript: str, intent: str, frustration: float) -> List[ActionItem]:
        items: List[ActionItem] = []

        if "delivery" in intent.lower() or "delayed" in transcript.lower():
            items.append(
                ActionItem(
                    task="Escalate to 3PL logistics partner for high-priority delivery dispatch",
                    assignee="Logistics Team",
                    priority="high" if frustration > 0.4 else "medium",
                    status="pending",
                )
            )
            items.append(
                ActionItem(
                    task="Trigger automated SMS tracking update link to customer's registered phone",
                    assignee="Support Agent",
                    priority="medium",
                    status="pending",
                )
            )

        if "refund" in intent.lower() or "payment" in intent.lower():
            items.append(
                ActionItem(
                    task="Cross-verify payment gateway transaction ID with Accounts/Finance",
                    assignee="Finance & Billing",
                    priority="high",
                    status="pending",
                )
            )

        if "return" in intent.lower() or "damaged" in transcript.lower():
            items.append(
                ActionItem(
                    task="Initiate reverse-pickup logistics request for defective item inspection",
                    assignee="Reverse Logistics",
                    priority="medium",
                    status="pending",
                )
            )

        if frustration > 0.6:
            items.append(
                ActionItem(
                    task="Mandatory supervisor courtesy callback to prevent churn/escalation",
                    assignee="Team Lead / Supervisor",
                    priority="urgent",
                    status="pending",
                )
            )

        if not items:
            items.append(
                ActionItem(
                    task="Review conversation summary and update CRM customer profile",
                    assignee="Support Agent",
                    priority="low",
                    status="pending",
                )
            )

        return items

    def _determine_escalation(
        self, frustration: float, sentiment_score: float, action_items: List[ActionItem]
    ) -> Tuple[str, str, str]:
        if frustration >= 0.75:
            return (
                "escalated",
                "critical",
                "High customer frustration detected with explicit threats of escalation or repeated service failure.",
            )
        elif frustration >= 0.5:
            return (
                "pending_action",
                "high",
                "Multiple complaints noted; customer requires priority operational follow-up.",
            )
        elif frustration >= 0.25:
            return (
                "pending_action",
                "medium",
                "Moderate dissatisfaction noted; resolution pending dispatch or review.",
            )
        else:
            return (
                "resolved" if sentiment_score > 0.2 else "pending_action",
                "low",
                "Standard support interaction handled within regular operating protocols.",
            )

    def _generate_summary(
        self,
        intent: str,
        primary_issue: str,
        resolution_status: str,
        action_items: List[ActionItem],
        commitments: List[CustomerCommitment],
    ) -> str:
        action_count = len(action_items)
        promise_summary = f" {len(commitments)} explicit commitment(s) made." if commitments else ""
        return (
            f"Customer contacted support regarding {intent.lower()}. "
            f"Core issue: \"{primary_issue}\". Status is currently {resolution_status.replace('_', ' ')} "
            f"with {action_count} follow-up task(s) assigned.{promise_summary}"
        )


conversation_analyzer = ConversationAnalysisService()

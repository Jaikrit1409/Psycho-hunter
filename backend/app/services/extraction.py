from __future__ import annotations

import re

from app.schemas.extraction import ExtractedInsight


# Common technology names that can be safely identified when explicitly
# mentioned in a document.
TECHNOLOGIES = {
    "AWS",
    "Azure",
    "GCP",
    "Google Cloud",
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "C++",
    "C#",
    "React",
    "Angular",
    "Vue",
    "Node.js",
    "FastAPI",
    "Django",
    "Spring Boot",
    "Docker",
    "Kubernetes",
    "PostgreSQL",
    "MySQL",
    "MongoDB",
    "Redis",
    "Terraform",
}


def _clean_text(text: str) -> str:
    """Normalize whitespace without changing the meaning of the text."""
    return re.sub(r"\s+", " ", text).strip()


def _sentence_containing(text: str, phrase: str) -> str:
    """Return the sentence containing a matched phrase."""
    sentences = re.split(r"(?<=[.!?])\s+", text)

    for sentence in sentences:
        if phrase.lower() in sentence.lower():
            return sentence.strip()

    return phrase.strip()


def extract_technologies(text: str) -> list[ExtractedInsight]:
    """
    Extract technologies that are explicitly mentioned.

    This deliberately does not infer expertise or skill level.
    """
    text = _clean_text(text)
    results: list[ExtractedInsight] = []

    for technology in TECHNOLOGIES:
        pattern = re.compile(re.escape(technology), re.IGNORECASE)

        if not pattern.search(text):
            continue

        evidence = _sentence_containing(text, technology)

        results.append(
            ExtractedInsight(
                category="TECHNOLOGY",
                subject=technology,
                observation=f"The person explicitly mentions {technology}.",
                confidence="high",
                evidence_text=evidence,
            )
        )

    return results


def extract_hobbies(text: str) -> list[ExtractedInsight]:
    """
    Extract hobbies only when the text explicitly expresses enjoyment
    or participation as a personal activity.
    """
    text = _clean_text(text)
    results: list[ExtractedInsight] = []

    patterns = [
        (
            r"\b(?:i|we)\s+(?:really\s+)?(?:enjoy|love|like)\s+"
            r"(?:playing\s+)?([a-z][a-z\s-]{1,40})",
            "The person explicitly states that they enjoy {subject}.",
        ),
        (
            r"\b(?:my|our)\s+hobbies?\s+(?:include|are)\s+"
            r"([a-z][a-z\s,&-]{1,80})",
            "The person explicitly identifies {subject} as a hobby.",
        ),
        (
            r"\bin\s+my\s+(?:free|spare)\s+time(?:,)?\s+"
            r"(?:i\s+)?(?:enjoy|like|love)\s+"
            r"(?:playing\s+)?([a-z][a-z\s-]{1,40})",
            "The person explicitly states that they enjoy {subject} in their free time.",
        ),
    ]

    for pattern, observation_template in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            subject = match.group(1).strip(" .,;:")

            if not subject:
                continue

            # Avoid treating long pieces of unrelated text as hobbies.
            if len(subject.split()) > 6:
                continue

            evidence = _sentence_containing(text, match.group(0))

            results.append(
                ExtractedInsight(
                    category="HOBBY",
                    subject=subject.title(),
                    observation=observation_template.format(subject=subject),
                    confidence="high",
                    evidence_text=evidence,
                )
            )

    return results


def extract_insights_from_text(text: str) -> list[ExtractedInsight]:
    """
    Run all deterministic extraction rules against a piece of text.
    """
    text = _clean_text(text)

    if not text:
        return []

    insights = []
    insights.extend(extract_technologies(text))
    insights.extend(extract_hobbies(text))

    return _deduplicate_insights(insights)


def _deduplicate_insights(
    insights: list[ExtractedInsight],
) -> list[ExtractedInsight]:
    """Remove duplicate category + subject combinations."""
    unique: dict[tuple[str, str], ExtractedInsight] = {}

    for insight in insights:
        key = (
            insight.category.upper(),
            insight.subject.strip().lower(),
        )

        if key not in unique:
            unique[key] = insight

    return list(unique.values())
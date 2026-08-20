"""Local, self-hosted zero-shot classification using DistilBERT.
The model loads once at process startup and stays in memory -- no
external API calls, no billing, no dependency on an outside service.
Requires a host that keeps the process running (e.g. Render), since
this can't live in a stateless serverless function.
"""
from transformers import pipeline

DEPARTMENT_DESCRIPTIONS = {
    "railway": "railway or train related issue",
    "delhi_police": "crime, theft, or law and order issue",
    "income_tax": "income tax or PAN card issue",
    "delhi_traffic": "traffic violation or road safety issue",
    "general": "general grievance not covered elsewhere",
}

_classifier = None


def _get_classifier():
    global _classifier
    if _classifier is None:
        print("Loading DistilBERT zero-shot model (first request only)...")
        _classifier = pipeline(
            "zero-shot-classification",
            model="typeform/distilbert-base-uncased-mnli",
        )
    return _classifier


def classify_department(complaint_text: str, departments: list) -> tuple[str, float]:
    labels = [DEPARTMENT_DESCRIPTIONS.get(d, d) for d in departments]
    label_to_dept = {DEPARTMENT_DESCRIPTIONS.get(d, d): d for d in departments}

    try:
        classifier = _get_classifier()
        result = classifier(complaint_text, candidate_labels=labels)
        top_label = result["labels"][0]
        top_score = result["scores"][0]
        return label_to_dept.get(top_label, "general"), float(top_score)
    except Exception as e:
        print(f"Classification error, defaulting to general: {e}")
        return "general", 0.0

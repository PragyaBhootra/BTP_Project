"""Guided slot-filling with a stronger, layered regex extraction pipeline.
Every message is scanned for date/time and location patterns regardless
of which field is currently being asked, so multi-fact answers (or
answers given out of order) still get captured. No NER, no external API
-- fully offline, zero dependency on any outside service.
"""
import re

# ---------------------------------------------------------------------
# Phone
# ---------------------------------------------------------------------
PHONE_RE = re.compile(r"(?<!\d)(\+?91[\-\s]?)?[6-9]\d{9}(?!\d)")

# ---------------------------------------------------------------------
# Date / time -- built from several alternatives, longest/most specific
# matches are tried first so "7th july at 4pm" is captured as one span
# ---------------------------------------------------------------------
_MONTH = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*"
_ORDINAL = r"(?:st|nd|rd|th)?"
_TIME_OF_DAY = (
    r"(?:\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.)"
    r"|\d{1,2}\s*o[' ]?clock"
    r"|(?:in the |at )?(?:morning|afternoon|evening|night|noon|midnight))"
)
_DAY_MONTH = rf"\d{{1,2}}{_ORDINAL}\s+{_MONTH}(?:\s+\d{{2,4}})?"
_MONTH_DAY = rf"{_MONTH}\s+\d{{1,2}}{_ORDINAL}(?:,?\s+\d{{2,4}})?"
_NUMERIC_DATE = r"\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?"
_RELATIVE_DATE = (
    r"(?:day before yesterday|today|yesterday|tomorrow"
    r"|last\s+\w+day|this\s+\w+day|next\s+\w+day"
    r"|\d+\s+days?\s+ago|a\s+week\s+ago|last\s+week|last\s+month|last\s+night)"
)

# A full date/time span: date part optionally followed by "at <time>",
# or a relative date alone, or a time-of-day alone.
DATE_TIME_RE = re.compile(
    rf"\b(?:"
    rf"(?:{_DAY_MONTH}|{_MONTH_DAY}|{_NUMERIC_DATE}|{_RELATIVE_DATE})"
    rf"(?:\s*(?:,|at|around)?\s*{_TIME_OF_DAY})?"
    rf"|{_TIME_OF_DAY}"
    rf")\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------
# Location -- two strategies, tried in order:
#   1. prepositional phrase: "near X", "at X", "in X", "outside X"
#   2. common Indian place-name suffix: "X market", "X nagar", etc.
# ---------------------------------------------------------------------
_STOP_WORDS = r"(?:on|at|around|yesterday|today|tomorrow|last|this|next|\d)"

LOCATION_PREP_RE = re.compile(
    rf"\b(?:near|at|in|outside|around)\s+"
    rf"([A-Za-z][A-Za-z\s]{{1,40}}?)"
    rf"(?=\s+{_STOP_WORDS}|[.,!?]|$)",
    re.IGNORECASE,
)

_PLACE_SUFFIXES = (
    r"market|station|chowk|nagar|colony|sector|road|gate|park|square|mandi"
    r"|basti|vihar|puram|ganj|marg|enclave|extension|phase|block|society"
    r"|mall|metro|circle|junction|bazar|bazaar|road|apartments?"
)
LOCATION_SUFFIX_RE = re.compile(
    rf"\b([A-Za-z]+(?:\s+[A-Za-z]+){{0,2}}\s+(?:{_PLACE_SUFFIXES}))\b",
    re.IGNORECASE,
)


def _strip_span(text: str, match) -> str:
    if not match:
        return text
    return (text[: match.start()] + text[match.end() :]).strip(" ,.")


def _extract_date(text: str):
    """Returns (matched_text, remaining_text) or (None, text)."""
    m = DATE_TIME_RE.search(text)
    if not m:
        return None, text
    return m.group().strip(), _strip_span(text, m)


def _extract_location(text: str):
    """Returns matched location string or None."""
    m = LOCATION_PREP_RE.search(text)
    if m:
        return m.group(1).strip()
    m = LOCATION_SUFFIX_RE.search(text)
    if m:
        return m.group(1).strip()
    return None


# ---------------------------------------------------------------------
# Slot machinery
# ---------------------------------------------------------------------
REQUIRED_FIELDS = ["description", "location", "time", "contact"]
FOLLOW_UP_QUESTIONS = {
    "description": "Could you briefly describe what happened?",
    "location": "Where did this happen? (area, landmark, or address)",
    "time": "When did this happen? (date and approximate time)",
    "contact": "What's a phone number we can reach you on for follow-up? (or type 'skip')",
}


def next_missing_field(slots: dict):
    for field in REQUIRED_FIELDS:
        if field not in slots or not slots[field]:
            return field
    return None


def _opportunistic_extract(text: str, slots: dict) -> dict:
    """Scans any message for a date/time and a location, independent of
    which field is currently being asked.
    """
    updated = dict(slots)
    working_text = text

    if "time" not in updated:
        date_val, working_text = _extract_date(working_text)
        if date_val:
            updated["time"] = date_val

    if "location" not in updated:
        loc_val = _extract_location(working_text)
        if loc_val:
            updated["location"] = loc_val

    return updated


def extract_slots(message: str, existing: dict) -> dict:
    slots = dict(existing)
    field = next_missing_field(slots)
    if field is None:
        return slots

    text = message.strip()
    if not text:
        return slots

    # catch any date/location embedded anywhere in the message first
    slots = _opportunistic_extract(text, slots)

    # if the field we were actually asking about is still empty, fill it
    # explicitly from the raw message as a fallback
    if not slots.get(field):
        if field == "contact":
            phone_match = PHONE_RE.search(text)
            if phone_match:
                slots["contact"] = phone_match.group().strip()
            elif text.lower() in ("skip", "no", "none", "n/a"):
                slots["contact"] = "not provided"
            else:
                slots["contact"] = text
        elif field == "location":
            date_val, remaining = _extract_date(text)
            slots["location"] = remaining if date_val else text
        else:  # description or time
            slots[field] = text

    return slots


def build_reply(slots: dict):
    missing = next_missing_field(slots)
    if missing is None:
        return (
            "Thanks -- I have everything I need. Click 'Send Complaint' to submit it.",
            True,
        )
    return FOLLOW_UP_QUESTIONS[missing], False

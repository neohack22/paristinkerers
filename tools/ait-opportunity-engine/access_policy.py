"""Fail-closed AI Tinkerers chapter access boundary.

This module is deliberately independent of any agent prompt. A configured
API query must be chapter-scoped and every returned record must prove that it
belongs to the same allowed chapter. Public/manual chapters never use API/MCP.
"""
from dataclasses import dataclass

API_CHAPTERS = frozenset({'paris', 'lima', 'bamako', 'conakry', 'casablanca', 'san-francisco'})
ALIASES = {
    'paris': 'paris', 'lima': 'lima', 'bko': 'bamako', 'bamako': 'bamako',
    'cky': 'conakry', 'conakry': 'conakry', 'casa': 'casablanca',
    'casablanca': 'casablanca', 'sf': 'san-francisco',
    'san-francisco': 'san-francisco', 'san francisco': 'san-francisco',
}

def canonical_chapter(value):
    if not isinstance(value, str):
        return None
    return ALIASES.get(value.strip().lower())

@dataclass(frozen=True)
class ScopeDecision:
    allowed: bool
    reason: str


def validate_job(job, endpoint, policy):
    """Reject any unscoped or overly broad job BEFORE API invocation.

    chapter_filter_param must be a query parameter in the authenticated
    operation schema. chapter_filter_value must be an explicitly approved
    chapter token (or an approved event token bound to that chapter). The
    returned chapter field is separately checked by caller.
    """
    chapter = canonical_chapter(job.get('chapter'))
    if chapter not in API_CHAPTERS:
        return ScopeDecision(False, 'chapter_not_in_api_scope')
    chapter_policy = policy.get('api_chapters', {}).get(chapter)
    if not isinstance(chapter_policy, dict) or not chapter_policy.get('enabled', False):
        return ScopeDecision(False, 'chapter_not_enabled')
    if not isinstance(endpoint, dict):
        return ScopeDecision(False, 'operation_not_available')
    params = job.get('params', {})
    if not isinstance(params, dict):
        return ScopeDecision(False, 'invalid_parameters')
    parameter = job.get('chapter_filter_param')
    if not parameter or parameter not in params:
        return ScopeDecision(False, 'missing_explicit_chapter_filter')
    if parameter not in {p.get('name') for p in endpoint.get('parameters', [])}:
        return ScopeDecision(False, 'unrecognized_chapter_filter')
    value = str(params[parameter])
    allowed_filters = chapter_policy.get('allowed_filters', {})
    if value not in [str(v) for v in allowed_filters.get(parameter, [])]:
        return ScopeDecision(False, 'filter_not_approved_for_chapter')
    if not job.get('chapter_field') or job.get('chapter_field') != job.get('fields', {}).get('chapter'):
        return ScopeDecision(False, 'missing_chapter_evidence_mapping')
    cap = policy.get('max_items_per_job', 100)
    if not isinstance(cap, int) or isinstance(cap, bool) or cap < 1:
        return ScopeDecision(False, 'invalid_policy_limit')
    limit = job.get('max_items', cap)
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1 or limit > cap:
        return ScopeDecision(False, 'job_exceeds_limit')
    if chapter == 'san-francisco':
        sf_cap = chapter_policy.get('max_items_per_job', 10)
        if limit > sf_cap:
            return ScopeDecision(False, 'sf_limit_exceeded')
    return ScopeDecision(True, 'allowed')


def record_is_allowed(record, expected_chapter):
    return canonical_chapter(record.get('chapter')) == canonical_chapter(expected_chapter)


def is_api_chapter(chapter, policy):
    canonical = canonical_chapter(chapter)
    return canonical in API_CHAPTERS and bool(policy.get('api_chapters', {}).get(canonical, {}).get('enabled'))
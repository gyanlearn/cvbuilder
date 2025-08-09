import re
import math
from typing import Any, Dict, List, Tuple


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[\t\r]", " ", text)
    text = re.sub(r"[\u2013\u2014]", "-", text)
    text = re.sub(r"[^a-z0-9%$+\-/.,()\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def flatten_keywords(d: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    def rec(x: Any):
        if isinstance(x, dict):
            for v in x.values():
                rec(v)
        elif isinstance(x, list):
            for v in x:
                rec(v)
        elif isinstance(x, str):
            out.append(x)
    rec(d)
    # de-dupe normalized
    seen = set()
    final = []
    for k in out:
        n = re.sub(r"\s+", " ", k.strip().lower())
        if n and n not in seen:
            seen.add(n)
            final.append(n)
    return final


def count_matches(text: str, terms: List[str]) -> Tuple[List[str], List[str]]:
    matched = []
    missing = []
    for t in terms:
        pattern = r"(^|\W)" + re.escape(t) + r"(\W|$)"
        if re.search(pattern, text):
            matched.append(t)
        else:
            missing.append(t)
    return matched, missing


def calc_readability(text: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    words = re.findall(r"[a-zA-Z]+", text)
    sents = re.split(r"[.!?]+\s+", text)
    sents = [s for s in sents if s.strip()]
    word_count = len(words)
    sent_count = max(1, len(sents))
    avg_sent_len = word_count / sent_count
    complex_words = [w for w in words if len(w) >= cfg.get('complex_word_min_len', 7)]
    complex_ratio = (len(complex_words) / max(1, word_count))
    warnings = []
    if avg_sent_len > cfg.get('max_sentence_length', 24):
        warnings.append('Average sentence length is high')
    if complex_ratio > cfg.get('max_complex_ratio', 0.15):
        warnings.append('Too many complex words')
    return {
        'word_count': word_count,
        'sentence_count': sent_count,
        'avg_sentence_length': round(avg_sent_len, 2),
        'complex_word_ratio': round(complex_ratio, 3),
        'warnings': warnings,
    }


def regex_findall(patterns: List[str], text: str) -> List[str]:
    hits = []
    for p in patterns:
        hits += re.findall(p, text, flags=re.IGNORECASE)
    return hits


def ats_score(cv_text: str, industry: str, lang_cfg: Dict[str, Any], prof_cfg: Dict[str, Any], ind_cfg: Dict[str, Any]) -> Dict[str, Any]:
    norm = normalize(cv_text)

    # Keywords
    general_keywords = [re.sub(r"\s+", " ", k.lower()) for k in lang_cfg.get('general_keywords', [])]
    industry_terms = flatten_keywords(ind_cfg)
    action_verbs_cfg = prof_cfg.get('action_verbs', {})  # {category: [verbs]}
    weak_phrases = prof_cfg.get('weak_language', {}).get('phrases', [])
    weak_to_strong = prof_cfg.get('weak_language', {}).get('replacements', {})
    buzzwords = prof_cfg.get('buzzwords', {}).get(industry.lower(), [])
    quant_patterns = prof_cfg.get('quantification_patterns', {})
    grammar_rules = lang_cfg.get('grammar', [])  # [{pattern, message, severity}]
    spelling_dicts = lang_cfg.get('spelling', {}).get('dictionaries', [])
    readability_cfg = lang_cfg.get('readability', {})

    # Matching
    kw_matched, kw_missing = count_matches(norm, general_keywords)
    ind_matched, ind_missing = count_matches(norm, industry_terms)

    # Action verbs
    action_found = {}
    for cat, verbs in action_verbs_cfg.items():
        m, _ = count_matches(norm, [v.lower() for v in verbs])
        if m:
            action_found[cat] = m

    # Quantification
    quant_found = {}
    for qcat, pats in quant_patterns.items():
        hits = regex_findall(pats, cv_text)
        if hits:
            quant_found[qcat] = hits[:10]

    # Grammar
    grammar_issues = []
    for rule in grammar_rules:
        pat = rule.get('pattern')
        if not pat:
            continue
        for m in re.finditer(pat, cv_text, flags=re.IGNORECASE):
            snippet = cv_text[max(0, m.start()-30): m.end()+30]
            grammar_issues.append({
                'message': rule.get('message', 'Grammar issue'),
                'severity': rule.get('severity', 'medium'),
                'snippet': snippet
            })

    # Spelling (very simple: find tokens not in any dictionary)
    spelling_suggestions = []
    if spelling_dicts:
        lex = set()
        for d in spelling_dicts:
            for w in d:
                lex.add(w.lower())
        for w in set(re.findall(r"[a-zA-Z]{3,}", cv_text)):
            wl = w.lower()
            if wl not in lex:
                # try simple suggestion by closest lowercase match (naive: same first 3 letters)
                sugg = [x for x in lex if x.startswith(wl[:3])][:3]
                spelling_suggestions.append({'word': w, 'suggestions': sugg})

    # Readability
    readability = calc_readability(cv_text, readability_cfg)

    # Weak language
    weak_hits = []
    for ph in weak_phrases:
        for m in re.finditer(r"(^|\W)"+re.escape(ph.lower())+r"(\W|$)", norm):
            repl = weak_to_strong.get(ph, [])
            weak_hits.append({'phrase': ph, 'suggest': repl, 'pos': m.span()})

    # Buzzwords
    buzz_found, _ = count_matches(norm, [b.lower() for b in buzzwords])

    # Scoring (weights)
    score = 0
    breakdown = {}
    def add(name: str, val: int):
        breakdown[name] = val
        nonlocal score
        score += val

    # Keywords
    add('keywords', min(len(kw_matched), 15))
    add('industry_keywords', min(len(ind_matched), 20))
    add('action_verbs', min(sum(len(v) for v in action_found.values()), 10))
    add('quantification', min(sum(len(v) for v in quant_found.values()), 10))
    # Penalize grammar issues and weak language
    add('readability', max(0, 10 - len(readability.get('warnings', []))))
    penalty = min(10, len(grammar_issues)) + min(5, len(weak_hits))
    score = max(0, score - penalty)
    add('buzzwords', min(len(buzz_found), 5))

    # Compose output
    report = {
        'ats_score': max(0, min(100, score)),
        'breakdown': breakdown,
        'keyword_matches': {
            'matched': kw_matched,
            'missing': kw_missing,
            'percentage': round((len(kw_matched)/max(1, len(general_keywords)))*100, 1) if general_keywords else 0
        },
        'industry_keyword_matches': {
            'matched': ind_matched,
            'missing': ind_missing,
            'percentage': round((len(ind_matched)/max(1, len(industry_terms)))*100, 1) if industry_terms else 0
        },
        'action_verbs_found': action_found,
        'quantification_found': quant_found,
        'grammar_issues': grammar_issues,
        'spelling_suggestions': spelling_suggestions,
        'readability_report': readability,
        'weak_language_found': weak_hits,
        'industry_buzzwords_found': buzz_found,
    }

    # Actionable issues aggregation
    issues = []
    for g in grammar_issues:
        issues.append({'type': 'grammar', 'snippet': g['snippet'], 'suggestion': 'Rewrite to fix grammar', 'message': g['message']})
    for sp in spelling_suggestions:
        issues.append({'type': 'spelling', 'snippet': sp['word'], 'suggestion': f"Consider: {', '.join(sp['suggestions'])}", 'message': 'Potential misspelling'})
    for w in weak_hits:
        best = w['suggest'][0] if w['suggest'] else 'Use a stronger verb'
        issues.append({'type': 'language', 'snippet': w['phrase'], 'suggestion': best, 'message': 'Weak phrase'})
    report['issues'] = issues

    return report



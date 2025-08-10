import re
import logging
from typing import Dict, Any, List, Tuple
import os

# Set up logging
logger = logging.getLogger(__name__)

def normalize(text: str) -> str:
    """Normalize text for analysis"""
    return re.sub(r'\s+', ' ', text.lower().strip())

def flatten_keywords(d: Dict[str, Any]) -> List[str]:
    """Flatten nested keyword structure"""
    result = []
    def rec(x: Any):
        if isinstance(x, str):
            result.append(x)
        elif isinstance(x, list):
            for item in x:
                rec(item)
        elif isinstance(x, dict):
            for v in x.values():
                rec(v)
    rec(d)
    return result

def count_matches(text: str, terms: List[str]) -> Tuple[List[str], List[str]]:
    """Count keyword matches in text"""
    norm = normalize(text)
    matched = []
    missing = []
    for term in terms:
        if term.lower() in norm:
            matched.append(term)
        else:
            missing.append(term)
    return matched, missing

def calc_readability(text: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate readability metrics"""
    sentences = re.split(r'[.!?]+', text)
    words = re.findall(r'\b\w+\b', text)
    complex_words = [w for w in words if len(w) >= cfg.get('complex_word_min_len', 8)]
    
    avg_sentence_length = len(words) / max(1, len(sentences))
    complex_ratio = len(complex_words) / max(1, len(words))
    
    warnings = []
    if avg_sentence_length > cfg.get('max_sentence_length', 24):
        warnings.append(f"Average sentence length ({avg_sentence_length:.1f}) exceeds recommended maximum")
    if complex_ratio > cfg.get('max_complex_ratio', 0.16):
        warnings.append(f"Complex word ratio ({complex_ratio:.2%}) exceeds recommended maximum")
    
    word_count = len(words)
    if word_count < cfg.get('target_word_count_min', 200):
        warnings.append(f"Word count ({word_count}) is below recommended minimum")
    elif word_count > cfg.get('target_word_count_max', 1200):
        warnings.append(f"Word count ({word_count}) exceeds recommended maximum")
    
    return {
        'avg_sentence_length': avg_sentence_length,
        'complex_word_ratio': complex_ratio,
        'total_words': word_count,
        'warnings': warnings
    }

def regex_findall(patterns: List[str], text: str) -> List[str]:
    """Find all regex matches in text"""
    matches = []
    for pattern in patterns:
        try:
            # Return the actual matched text, not Match objects
            matches.extend(re.findall(pattern, text, re.IGNORECASE))
        except re.error as e:
            logger.warning(f"Invalid regex pattern '{pattern}': {e}")
    return matches

def llm_spell_check(cv_text: str, model) -> List[Dict[str, Any]]:
    """
    Use LLM for intelligent spelling and grammar checking
    """
    if not model:
        logger.warning("LLM model not available, skipping spell check")
        return []
    
    try:
        # Create a focused prompt for spelling and grammar checking
        prompt = f"""
        You are an expert resume reviewer and spelling/grammar checker. 
        
        Analyze the following CV text and identify ONLY actual spelling mistakes and grammar errors.
        Do NOT flag:
        - Proper nouns (names, company names, product names)
        - Technical terms, programming languages, frameworks
        - Job titles, industry jargon
        - Compound words or abbreviations
        - Words that are correctly spelled but might seem unusual
        
        Focus ONLY on genuine spelling errors and grammar issues.
        
        CV Text:
        {cv_text[:3000]}
        
        Return your analysis in this exact JSON format:
        {{
            "spelling_errors": [
                {{
                    "word": "misspelled_word",
                    "correction": "correct_spelling",
                    "context": "brief explanation"
                }}
            ],
            "grammar_errors": [
                {{
                    "issue": "grammar_issue_description",
                    "suggestion": "how_to_fix_it",
                    "context": "brief explanation"
                }}
            ]
        }}
        
        If no errors found, return empty arrays. Be conservative - only flag obvious mistakes.
        """
        
        logger.info("Sending spelling/grammar check request to LLM")
        logger.info(f"LLM Input Prompt: {prompt[:500]}...")
        
        response = model.generate_content(prompt)
        llm_output = response.text
        
        logger.info(f"LLM Output: {llm_output[:500]}...")
        
        # Try to parse the JSON response
        try:
            import json
            result = json.loads(llm_output)
            
            spelling_errors = result.get('spelling_errors', [])
            grammar_errors = result.get('grammar_errors', [])
            
            logger.info(f"LLM detected {len(spelling_errors)} spelling errors and {len(grammar_errors)} grammar errors")
            
            # Convert to our standard format
            issues = []
            
            for error in spelling_errors:
                issues.append({
                    'type': 'spelling',
                    'word': error.get('word', ''),
                    'suggestion': error.get('correction', ''),
                    'message': f"Spelling error: {error.get('context', '')}"
                })
            
            for error in grammar_errors:
                issues.append({
                    'type': 'grammar',
                    'snippet': error.get('issue', ''),
                    'suggestion': error.get('suggestion', ''),
                    'message': f"Grammar issue: {error.get('context', '')}"
                })
            
            return issues
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.error(f"Raw LLM output: {llm_output}")
            
            # Fallback: try to extract information from text response
            fallback_issues = []
            if "spelling" in llm_output.lower() or "misspell" in llm_output.lower():
                fallback_issues.append({
                    'type': 'spelling',
                    'word': 'LLM detected spelling issues',
                    'suggestion': 'Review LLM feedback',
                    'message': 'LLM analysis suggests spelling improvements'
                })
            
            if "grammar" in llm_output.lower():
                fallback_issues.append({
                    'type': 'grammar',
                    'snippet': 'LLM detected grammar issues',
                    'suggestion': 'Review LLM feedback',
                    'message': 'LLM analysis suggests grammar improvements'
                })
            
            return fallback_issues
            
    except Exception as e:
        logger.error(f"LLM spell check failed: {e}")
        return []

def ats_score(cv_text: str, industry: str, lang_cfg: Dict[str, Any], prof_cfg: Dict[str, Any], ind_cfg: Dict[str, Any], model=None) -> Dict[str, Any]:
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
        hits = list(re.finditer(pat, cv_text, flags=re.IGNORECASE))
        if hits:
            # Aggregate into a single issue with count and first few snippets
            examples = []
            for m in hits[:5]:
                examples.append(cv_text[max(0, m.start()-30): m.end()+30])
            grammar_issues.append({
                'message': rule.get('message', 'Grammar issue'),
                'severity': rule.get('severity', 'medium'),
                'count': len(hits),
                'examples': examples
            })

    # LLM-based Spelling and Grammar Check
    logger.info("Starting LLM-based spelling and grammar check")
    llm_issues = llm_spell_check(cv_text, model)
    
    # Separate spelling and grammar issues from LLM
    spelling_suggestions = []
    llm_grammar_issues = []
    
    for issue in llm_issues:
        if issue['type'] == 'spelling':
            spelling_suggestions.append({
                'word': issue['word'],
                'suggestions': [issue['suggestion']] if issue['suggestion'] else []
            })
        elif issue['type'] == 'grammar':
            llm_grammar_issues.append({
                'message': issue['message'],
                'severity': 'medium',
                'count': 1,
                'examples': [issue['snippet']] if issue['snippet'] else []
            })
    
    # Merge grammar issues from rules and LLM
    all_grammar_issues = grammar_issues + llm_grammar_issues
    
    logger.info(f"LLM spell check completed: {len(spelling_suggestions)} spelling issues, {len(llm_grammar_issues)} grammar issues")

    # Readability
    readability = calc_readability(cv_text, readability_cfg)

    # Weak language
    weak_hits = []
    for ph in weak_phrases:
        for m in re.finditer(r"(^|\W)"+re.escape(ph.lower())+r"(\W|$)", norm):
            repl = weak_to_strong.get(ph, [])
            weak_hits.append({'phrase': ph, 'suggest': repl, 'pos': (m.start(), m.end())})

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
    penalty = min(10, len(all_grammar_issues)) + min(5, len(weak_hits))
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
        'grammar_issues': all_grammar_issues,
        'spelling_suggestions': spelling_suggestions,
        'readability_report': readability,
        'weak_language_found': weak_hits,
        'industry_buzzwords_found': buzz_found,
    }

    # Actionable issues aggregation
    issues = []
    for g in all_grammar_issues:
        issues.append({
            'type': 'grammar',
            'snippet': (g.get('examples') or [''])[0],
            'suggestion': 'Rewrite to fix grammar',
            'message': f"{g['message']} ({g.get('count', 1)} instances)"
        })
    for sp in spelling_suggestions:
        issues.append({'type': 'spelling', 'snippet': sp['word'], 'suggestion': f"Consider: {', '.join(sp['suggestions'])}", 'message': 'Potential misspelling'})
    for w in weak_hits:
        best = w['suggest'][0] if w['suggest'] else 'Use a stronger verb'
        issues.append({'type': 'language', 'snippet': w['phrase'], 'suggestion': best, 'message': 'Weak phrase'})
    report['issues'] = issues

    return report



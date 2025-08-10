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

    # Spelling (improved: handle compound words, proper nouns, and common terms)
    spelling_suggestions = []
    if spelling_dicts:
        lex = set()
        for d in spelling_dicts:
            for w in d:
                lex.add(w.lower())
        
        # Add common compound terms and proper nouns
        common_terms = {
            'fastest', 'software', 'engineer', 'heading', 'omni', 'channel', 'omni-channel',
            'frontend', 'backend', 'fullstack', 'full-stack', 'web', 'mobile', 'desktop',
            'database', 'api', 'rest', 'graphql', 'microservice', 'microservices',
            'devops', 'ci', 'cd', 'pipeline', 'deployment', 'infrastructure',
            'cloud', 'aws', 'azure', 'gcp', 'heroku', 'vercel', 'netlify',
            'javascript', 'typescript', 'python', 'java', 'csharp', 'c++', 'go', 'rust',
            'react', 'vue', 'angular', 'node', 'express', 'django', 'flask', 'fastapi',
            'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'kafka',
            'docker', 'kubernetes', 'terraform', 'ansible', 'jenkins', 'github', 'gitlab',
            'agile', 'scrum', 'kanban', 'waterfall', 'lean', 'sixsigma', 'togaf',
            'ux', 'ui', 'design', 'research', 'prototype', 'wireframe', 'mockup',
            'analytics', 'metrics', 'dashboard', 'reporting', 'visualization',
            'machine', 'learning', 'artificial', 'intelligence', 'neural', 'network',
            'blockchain', 'cryptocurrency', 'nft', 'defi', 'web3', 'metaverse'
        }
        
        # Add common terms to lexicon
        for term in common_terms:
            lex.add(term.lower())
        
        # Add common basic vocabulary to eliminate false positives
        basic_vocab = {
            'for', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'from', 'with', 'by',
            'of', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
            'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'can', 'must', 'shall', 'this', 'that', 'these', 'those', 'here', 'there',
            'when', 'where', 'why', 'how', 'what', 'which', 'who', 'whom', 'whose',
            'if', 'then', 'else', 'while', 'until', 'since', 'during', 'before', 'after',
            'above', 'below', 'under', 'over', 'between', 'among', 'through', 'across',
            'into', 'onto', 'upon', 'within', 'without', 'against', 'toward', 'towards',
            'about', 'around', 'across', 'along', 'beside', 'beyond', 'inside', 'outside',
            'project', 'integration', 'development', 'implementation', 'deployment',
            'management', 'administration', 'coordination', 'collaboration', 'communication',
            'documentation', 'specification', 'configuration', 'optimization', 'automation',
            'monitoring', 'testing', 'debugging', 'maintenance', 'support', 'training',
            'research', 'analysis', 'design', 'planning', 'execution', 'delivery',
            'evaluation', 'assessment', 'review', 'audit', 'compliance', 'security',
            'performance', 'scalability', 'reliability', 'availability', 'usability',
            'best', 'good', 'great', 'excellent', 'outstanding', 'superior', 'quality',
            'efficient', 'effective', 'successful', 'innovative', 'creative', 'strategic',
            'technical', 'professional', 'experienced', 'skilled', 'knowledgeable',
            'responsible', 'accountable', 'dedicated', 'motivated', 'results-oriented'
        }
        
        # Add basic vocabulary to lexicon
        for word in basic_vocab:
            lex.add(word.lower())
        
        # Add common compound terms that might appear in CVs
        compound_terms = {
            'software engineer', 'software developer', 'frontend developer', 'backend developer',
            'full stack developer', 'fullstack developer', 'web developer', 'mobile developer',
            'data engineer', 'data scientist', 'machine learning engineer', 'ml engineer',
            'devops engineer', 'site reliability engineer', 'sre', 'qa engineer',
            'test engineer', 'quality assurance engineer', 'ui designer', 'ux designer',
            'product manager', 'project manager', 'program manager', 'technical lead',
            'team lead', 'engineering manager', 'senior engineer', 'principal engineer',
            'staff engineer', 'senior developer', 'lead developer', 'architect',
            'solution architect', 'enterprise architect', 'cloud architect', 'security engineer',
            'network engineer', 'systems engineer', 'infrastructure engineer'
        }
        
        # Add compound terms to lexicon
        for term in compound_terms:
            lex.add(term.lower().replace(' ', ''))
            lex.add(term.lower().replace(' ', '-'))
        
        # Improved word tokenization - handle compound words and proper nouns
        words = re.findall(r"[a-zA-Z][a-zA-Z0-9-]*[a-zA-Z0-9]|[a-zA-Z]{2,}", cv_text)
        
        for w in set(words):
            wl = w.lower()
            
            # Skip if word is in lexicon
            if wl in lex:
                continue
                
            # Skip if it's a proper noun (starts with capital letter)
            if w[0].isupper() and len(w) > 2:
                continue
                
            # Skip if it's a compound word (contains multiple capital letters)
            if len([c for c in w if c.isupper()]) > 1 and len(w) > 3:
                continue
                
            # Skip if it's a common abbreviation or acronym
            if w.isupper() and len(w) <= 5:
                continue
                
            # Skip if it's a number or contains numbers
            if any(c.isdigit() for c in w):
                continue
                
            # Skip if it's a common technical compound term
            if any(term in wl for term in ['engineer', 'developer', 'manager', 'analyst', 'specialist', 'consultant']):
                continue
                
            # Skip if it's a common technical prefix/suffix
            if any(wl.endswith(suffix) for suffix in ['ware', 'tech', 'soft', 'net', 'sys', 'app', 'web', 'mobile', 'cloud', 'data', 'ai', 'ml', 'api', 'sdk', 'cli', 'gui', 'ui', 'ux']):
                continue
                
            # Skip if it's a common technical prefix
            if any(wl.startswith(prefix) for prefix in ['micro', 'macro', 'multi', 'cross', 'inter', 'intra', 'trans', 'sub', 'super', 'hyper', 'ultra', 'mega', 'giga', 'tera', 'nano', 'pico', 'femto']):
                continue
                
            # Skip if it contains common technical separators
            if '-' in w or '_' in w:
                continue
                
            # Only flag if it's a simple word not in lexicon
            if len(w) >= 3 and w.isalpha():
                # try simple suggestion by closest lowercase match (naive: same first 3 letters)
                sugg = [x for x in lex if x.startswith(wl[:3])][:3]
                if sugg:  # Only add if we have suggestions
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



import json
import os
from typing import Any, Dict


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_language_quality_config(base_dir: str) -> Dict[str, Any]:
    return _read_json(os.path.join(base_dir, 'language_quality.json'))


def load_professional_language_config(base_dir: str) -> Dict[str, Any]:
    return _read_json(os.path.join(base_dir, 'professional_language.json'))


def load_industry_keywords(base_dir: str, industry: str) -> Dict[str, Any]:
    # industry_keyword folder contains JSON files per industry or a single nested file
    ik_dir = os.path.join(base_dir, 'industry_keyword')
    file_path = os.path.join(ik_dir, f'{industry.lower()}.json')
    if os.path.exists(file_path):
        return _read_json(file_path)
    # fallback to a single file
    fallback = os.path.join(ik_dir, 'all.json')
    if os.path.exists(fallback):
        data = _read_json(fallback)
        return data.get(industry.lower(), {})
    return {}



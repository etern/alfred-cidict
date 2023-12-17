#!/usr/bin/env python3

import sys
import os
import json
import subprocess
import pickle
import string
import re
from typing import List, Tuple
from pathlib import Path
from bktree import BKTree, dict_words
import macdict


def parse_Oxford_Chinese_Dictionary(content) -> List[Tuple[str, str]]:
    """content in plain text, parse to structrued data
    不同词典库，格式不一样，此函数只解析 牛津英汉汉英词典
    """
    entries = []
    pinyin = r"([a-z]*[āɑ̄ēīōūǖáɑ́éíóúǘǎɑ̌ěǐǒǔǚàɑ̀èìòùǜü]+[a-z]*)+"
    # (synoym) 词义 pīnyīn
    pattern = re.compile(r";? ?(\([a-zA-Z, ]+\))? ?(«[a-zA-Z, ]+»)? [\u4e00-\u9fff…]+ " + pinyin)
    for m in pattern.finditer(content):
        entries.append(m.group(0))
    lines = []
    for ent in entries:
        if ent.startswith(';') and lines:
            lines[-1] += ent
        else:
            lines.append(ent)
    results = []
    for text in lines:
        text = re.sub(pinyin, "", text)
        text = re.sub(" +", " ", text)
        title = ','.join(re.findall(r"[\u4e00-\u9fff…]+", text))
        results.append((title, text))
    return results


def alfred_item(title, subtitle, arg=None, is_suggestion=False):
    """https://www.alfredapp.com/help/workflows/inputs/script-filter/json/"""
    arg = arg or title
    item = {
        "arg": arg,
        "title": title,
        "subtitle": subtitle or "👻本地查不到，按shift或enter网络查询",
        "valid": True,
        "quicklookurl": f"https://youdao.com/result?word={arg}&lang=en",
        "icon": { "path": "assets/translate-star.png" if is_suggestion else "assets/translate.png" },
        "mods": {
            "cmd": { "subtitle": "🔊 ", "arg": arg, "valid": True },
            "alt": { "subtitle": "📣 ", "arg": arg, "valid": True }
        },
        "text": {
            "copy": title
        }
    }
    return item


class Suggester:
    def __init__(self, cache_dir=None):
        cache_dir = cache_dir or os.getenv("alfred_workflow_data", "./dict_cache")
        self.cache_dir = Path(cache_dir)
        if self.cache_dir.exists() and (self.cache_dir / 'z.pkl').exists():
            return
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        atoz = string.ascii_lowercase
        trees = self._load_bktrees(atoz)
        for ch, tree in zip(atoz, trees):
            with open(self.cache_dir / f"{ch}.pkl", "wb") as f:
                pickle.dump(tree, f)

    @staticmethod
    def _load_bktrees(initials) -> List[BKTree]:
        trees = []
        for ch in initials:
            tree = BKTree((w for w in dict_words("/usr/share/dict/words")
                           if w[0].lower() == ch.lower()))
            trees.append(tree)
        return trees

    def suggest(self, word: str, max_count:int = 10) -> List[str]:
        if len(word) < 2:
            return []
        if word[0].lower() not in string.ascii_lowercase:
            return []
        cache_file = self.cache_dir / f"{word[0]}.pkl"
        with open(cache_file, "rb") as f:
            tree = pickle.load(f)
        results = tree.query(word, 2)
        return [s for i, s in results[:max_count] if s != word]


def lookup(word: str) -> str:
    content = macdict.lookup_word(word) or ''
    _, *rest = content.split('|')
    return '|'.join(rest)


def lookup_parsed(word) -> List[Tuple[str, str]]:
    page = lookup(word)
    parsed = parse_Oxford_Chinese_Dictionary(page)
    if not parsed:
        parsed = [(word, page)]
    return parsed


def lookup_render(word) -> str:
    entries = lookup_parsed(word)
    return ';'.join(t for t, _ in entries)


def main():
    try:
        word = sys.argv[1]
    except IndexError:
        print('You did not enter any terms to look up in the Dictionary.')
        sys.exit()
    entries = lookup_parsed(word)
    items = [alfred_item(w, m, word) for w, m in entries[:5]] or [alfred_item(word, '')]
    max_suggestions = os.getenv('max_suggestions', '0')
    max_suggestions = int(max_suggestions) if max_suggestions.isdigit() else 0
    if max_suggestions > 0:
        words = Suggester().suggest(word)[:max_suggestions]
        meanings = [lookup_render(w) for w in words]
        items += [alfred_item(w, m, is_suggestion=True) for w, m in zip(words, meanings) if m]
    print(json.dumps({"items": items}, ensure_ascii=False))


if __name__ == '__main__':
    main()

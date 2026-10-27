"""
engine.py - the brain of SamBot.

Pipeline for every message:
    1. clean      lowercase, expand contractions, strip punctuation
    2. fix typos  fuzzy-match words against the bot's own vocabulary (difflib)
    3. score      run every rule's regex patterns, longest + highest priority wins
    4. respond    run a skill handler or pick a (non-repeating) canned response
    5. fallback   "Did you mean ...?" suggestions when nothing matches
Context (name, to-dos, pending yes/no questions) is kept between messages.
"""
from __future__ import annotations

import difflib
import json
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from rules import NEGATIVE_WORDS, POSITIVE_WORDS, RULES, Rule
from skills import SKILLS

_CONTRACTIONS = {
    "what's": "what is", "who's": "who is", "how's": "how is", "it's": "it is", "that's": "that is",
    "where's": "where is", "today's": "todays", "i'm": "i am", "you're": "you are", "i've": "i have",
    "don't": "do not", "can't": "cannot", "won't": "will not", "let's": "let us", "isn't": "is not",
    "wanna": "want to", "gonna": "going to", "u": "you", "r": "are", "pls": "please", "plz": "please",
}
_YES = re.compile(r"^(yes|yeah|yep|yup|sure|ok|okay|please|why not|of course|definitely|y|go on|another)\b")
_NO = re.compile(r"^(no|nope|nah|not now|no thanks|nothing|stop|n)\b")
_NOT_A_NAME = {"ok", "okay", "yes", "no", "nope", "nothing", "none", "fine", "good", "great", "hmm",
               "lol", "skip", "cool", "nah", "yep", "sure", "later", "idk", "hi", "hello", "hey"}


class Memory:
    """Tiny JSON-backed memory so the bot remembers your name and to-dos."""

    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path) if path else None
        self.name: Optional[str] = None
        self.todos: list[dict] = []
        self._load()

    def _load(self):
        if self.path and self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                self.name = data.get("name")
                self.todos = data.get("todos", [])
            except (OSError, json.JSONDecodeError):
                pass  # corrupt file -> start fresh

    def save(self):
        if self.path:
            try:
                self.path.write_text(
                    json.dumps({"name": self.name, "todos": self.todos}, indent=2), encoding="utf-8")
            except OSError:
                pass


class ChatBot:
    def __init__(self, memory_path: Optional[Path] = None):
        self.memory = Memory(memory_path)
        self.history: list[tuple[str, str, str]] = []   # (HH:MM:SS, "you"/"bot", text)
        self.pending: Optional[str] = None               # waiting for yes/no, a name, a mood...
        self.finished = False
        self.unknown_streak = 0
        self._decks: dict[str, list[str]] = {}
        self._compiled = [(r, [re.compile(p) for p in r.patterns]) for r in RULES]
        self._rule_by_intent = {r.intent: r for r in RULES}
        self.vocab = self._build_vocab()
        self._suggestions = {r.suggest: r.intent for r in RULES if r.suggest}
        self.last_intent: Optional[str] = None           # handy for tests / debugging

    # ---------------------------------------------------------------- helpers
    def n(self) -> str:
        """', Name' if we know the user's name, else '' (used inside replies)."""
        return f", {self.memory.name}" if self.memory.name else ""

    def remember_name(self, name: str):
        self.memory.name = name.strip().title()
        self.memory.save()

    def pick(self, key: str, options: list[str]) -> str:
        """Random choice that never repeats until every option has been used."""
        deck = self._decks.get(key)
        if not deck:
            deck = options[:]
            random.shuffle(deck)
            self._decks[key] = deck
        return deck.pop()

    def pick_response(self, intent: str) -> str:
        rule = self._rule_by_intent[intent]
        return self.pick(intent, rule.responses).replace("{n}", self.n())

    def _build_vocab(self) -> set[str]:
        words = set()
        for rule in RULES:
            for p in rule.patterns:
                p = re.sub(r"\\[a-zA-Z]", " ", p)          # drop \b \w \d ...
                words.update(re.findall(r"[a-z]{4,}", p))
        words.update({w[:-1] for w in words if w.endswith("s") and len(w) > 4})   # jokes -> joke
        return words

    # ------------------------------------------------------------- text steps
    @staticmethod
    def clean(text: str) -> str:
        t = text.lower().strip()
        for k, v in _CONTRACTIONS.items():
            t = re.sub(rf"(?<![\w']){re.escape(k)}(?![\w'])", v, t)
        t = t.replace("'", "")
        t = re.sub(r"[^a-z0-9\s\+\-\*/\(\)\.%\^]", " ", t)       # keep maths symbols
        t = re.sub(r"(?<!\d)\.|\.(?!\d)", " ", t)                 # dots only inside numbers
        t = re.sub(r"-(?!\s*[\d\(])", " ", t)                      # hyphens only survive as maths minus
        return re.sub(r"\s+", " ", t).strip()

    def fix_typos(self, text: str) -> str:
        fixed = []
        for tok in text.split():
            if len(tok) < 4 or tok in self.vocab or not tok.isalpha():
                fixed.append(tok)
                continue
            match = difflib.get_close_matches(tok, self.vocab, n=1, cutoff=0.8)
            if not match:   # transposed letters, e.g. "joek" -> "joke"
                match = [w for w in self.vocab
                         if len(w) == len(tok) and w[0] == tok[0] and sorted(w) == sorted(tok)][:1]
            fixed.append(match[0] if match else tok)
        return " ".join(fixed)

    # --------------------------------------------------------------- matching
    def match(self, text: str) -> Optional[Rule]:
        best, best_score = None, 0
        for rule, patterns in self._compiled:
            for pat in patterns:
                m = pat.search(text)
                if m:
                    score = rule.priority * 1000 + len(m.group(0))
                    if score > best_score:
                        best, best_score = rule, score
        return best

    def _did_you_mean(self, text: str) -> str:
        close = difflib.get_close_matches(text, list(self._suggestions), n=2, cutoff=0.45)
        if close:
            opts = " or ".join(f"'{c}'" for c in close)
            return f"I'm not sure I got that. Did you mean {opts}?"
        return ""

    # ------------------------------------------------------------------ reply
    def reply(self, user_text: str) -> str:
        raw = (user_text or "").strip()[:500]
        self._log("you", raw)
        answer = self._respond(raw) if raw else "Say something and I'll do my best to help!"
        self._log("bot", answer)
        return answer

    def _log(self, who: str, text: str):
        self.history.append((datetime.now().strftime("%H:%M:%S"), who, text))

    def _respond(self, raw: str) -> str:
        if raw.startswith("/"):
            return self._command(raw)

        clean = self.clean(raw)
        fixed = self.fix_typos(clean)

        # 1) a yes/no/name/mood answer to something the bot just asked
        if self.pending:
            handled = self._handle_pending(raw, clean, fixed)
            if handled is not None:
                return handled

        # 2) normal rule matching
        rule = self.match(fixed)

        # 2b) no rule matched, but the whole sentence is almost a known phrase ("what is yur nme")
        if rule is None:
            close = difflib.get_close_matches(fixed, list(self._suggestions), n=1, cutoff=0.8)
            if close:
                rule = self._rule_by_intent[self._suggestions[close[0]]]

        if rule:
            self.unknown_streak = 0
            self.last_intent = rule.intent
            if rule.handler:
                return SKILLS[rule.handler](self, raw, fixed)
            return self.pick_response(rule.intent)

        # 3) fallback
        self.last_intent = "fallback"
        self.unknown_streak += 1
        hint = self._did_you_mean(fixed)
        if hint:
            return hint
        if self.unknown_streak >= 3:
            return "I'm still stuck. Type 'help' and I'll show you everything I understand."
        return self.pick("fallback", [
            "Hmm, I don't know that one yet. Try 'help' to see what I can do.",
            "I didn't understand that. Could you rephrase it?",
            "I'm a rule-based bot, so I only know my rules - type 'help' to see them.",
        ])

    # ---------------------------------------------------------------- pending
    def _handle_pending(self, raw: str, clean: str, fixed: str) -> Optional[str]:
        pending, self.pending = self.pending, None   # one-shot: cleared unless re-set below

        if pending in ("joke", "fact", "quote"):
            if _YES.match(clean):
                self.last_intent = pending
                return SKILLS[pending](self, raw, fixed)
            if _NO.match(clean):
                self.last_intent = "decline"
                return "No problem! Ask me anything else whenever you like."
            return None

        if pending == "mood":
            words = set(clean.split())
            if "not" in words and words & POSITIVE_WORDS:
                return "Sorry to hear that. Say 'joke' or 'motivate me' if you want a lift."
            if words & NEGATIVE_WORDS and len(words) <= 4:
                self.last_intent = "sad"
                return self.pick_response("sad")
            if words & POSITIVE_WORDS and len(words) <= 4:
                self.last_intent = "happy"
                return self.pick_response("happy")
            return None

        if pending == "name":
            if self.match(fixed) is None and re.fullmatch(r"[A-Za-z][A-Za-z'\-]{1,20}( [A-Za-z][A-Za-z'\-]{1,20})?", raw) \
                    and clean not in _NOT_A_NAME:
                self.remember_name(raw)
                self.last_intent = "name_set"
                return f"Nice to meet you, {self.memory.name}! Type 'help' to see what I can do."
            return None
        return None

    # --------------------------------------------------------------- commands
    def _command(self, raw: str) -> str:
        cmd = raw.split()[0].lower()
        if cmd == "/help":
            return SKILLS["help_menu"](self, raw, "help")
        if cmd == "/history":
            return SKILLS["history"](self, raw, "history")
        if cmd == "/todo":
            return SKILLS["todo_show"](self, raw, "todo")
        return f"Unknown command '{cmd}'. Try /help, /history, /todo, /clear, /save or /exit."

    # ---------------------------------------------------------------- export
    def transcript(self) -> str:
        lines = [f"SamBot conversation - {datetime.now():%d %b %Y %H:%M}", "-" * 40]
        for ts, who, text in self.history:
            speaker = "You   " if who == "you" else "SamBot"
            lines.append(f"[{ts}] {speaker}: {text}")
        return "\n".join(lines)

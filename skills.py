"""
skills.py - small "abilities" that go beyond fixed replies.

Every skill has the same signature:  skill(bot, raw, clean) -> str
    bot   - the ChatBot (gives access to memory, history, decks)
    raw   - what the user typed (original capitalisation)
    clean - normalised lowercase text used for matching
"""
from __future__ import annotations

import ast
import operator
import re
from datetime import datetime

from rules import FACTS, JOKES, QUOTES, BOT_NAME

# --------------------------------------------------------------------------
# Greetings, mood, goodbye
# --------------------------------------------------------------------------

def greet(bot, raw, clean):
    hour = datetime.now().hour
    part = "morning" if hour < 12 else "afternoon" if hour < 17 else "evening"
    said = re.search(r"good (morning|afternoon|evening)", clean)
    if said:
        opener = f"Good {said.group(1)}{bot.n()}!"      # echo what the user said
    else:
        opener = bot.pick("greet_open", [f"Hello{bot.n()}!", f"Hey{bot.n()}!", f"Hi{bot.n()}!",
                                         f"Good {part}{bot.n()}!"])
    if bot.memory.name:
        return f"{opener} Nice to see you again. How can I help? (type 'help' to see what I can do)"
    bot.pending = "name"
    return f"{opener} I'm {BOT_NAME}. What's your name?"


def how_are_you(bot, raw, clean):
    bot.pending = "mood"
    return bot.pick_response("how_are_you")


def bye(bot, raw, clean):
    bot.finished = True
    return bot.pick("bye", [f"Goodbye{bot.n()}! Come back soon.",
                            f"See you later{bot.n()}! Keep building.",
                            f"Take care{bot.n()}! It was great chatting."])


def help_menu(bot, raw, clean):
    return (
        f"Here's what {BOT_NAME} can do:\n"
        "  * Chat         - hello, how are you, who are you, thanks, bye\n"
        "  * Remember     - 'my name is Asha' (I remember it next time too)\n"
        "  * Maths        - 'calculate 12 * (3 + 4)', 'what is 2^10', 'square root of 144'\n"
        "  * Time & date  - 'what time is it', 'what is today's date'\n"
        "  * To-do list   - 'add buy milk to my todo', 'show my todo', 'done 1', 'remove 2', 'clear my todo'\n"
        "  * Fun          - 'tell me a joke', 'fun fact', 'motivate me'\n"
        "  * Commands     - /help  /history  /clear  /save  /exit\n"
        "Typos are fine - I'll try to understand you anyway!"
    )

# --------------------------------------------------------------------------
# Name memory
# --------------------------------------------------------------------------
_NOT_NAMES = {"a", "an", "the", "not", "so", "very", "fine", "good", "ok", "okay", "here", "back"}


def set_name(bot, raw, clean):
    m = re.search(r"(?:my name is|call me|i go by|i am called)\s+([A-Za-z][A-Za-z'\-]*)", raw, re.I)
    if not m or m.group(1).lower() in _NOT_NAMES:
        return "I didn't catch that - try 'my name is Asha'."
    bot.remember_name(m.group(1))
    return f"Nice to meet you, {bot.memory.name}! I'll remember your name."


def get_name(bot, raw, clean):
    if bot.memory.name:
        return f"Your name is {bot.memory.name}."
    bot.pending = "name"
    return "I don't know your name yet. What should I call you?"

# --------------------------------------------------------------------------
# Time and date
# --------------------------------------------------------------------------

def time_date(bot, raw, clean):
    now = datetime.now()
    t, d = now.strftime("%I:%M %p").lstrip("0"), now.strftime("%A, %d %B %Y")
    wants_date = bool(re.search(r"\b(date|day|today|todays)\b", clean))
    wants_time = bool(re.search(r"\b(time|clock)\b", clean))
    if wants_date and not wants_time:
        return f"Today is {d}."
    if wants_time and not wants_date:
        return f"It's {t} right now."
    return f"It's {t} on {d}."

# --------------------------------------------------------------------------
# Safe calculator (uses the ast module - never eval())
# --------------------------------------------------------------------------
_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Mod: operator.mod, ast.Pow: operator.pow,
    ast.FloorDiv: operator.floordiv,
}


def _safe_eval(node):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        v = _safe_eval(node.operand)
        return v if isinstance(node.op, ast.UAdd) else -v
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        left, right = _safe_eval(node.left), _safe_eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 1000:
            raise ValueError("exponent too large")
        return _OPS[type(node.op)](left, right)
    raise ValueError("unsupported expression")


_WORD_OPS = [
    (r"\bsquare root of\s+(\d+(?:\.\d+)?)", r"(\1)**0.5"),
    (r"\bsqrt of\s+(\d+(?:\.\d+)?)", r"(\1)**0.5"),
    (r"(\d+(?:\.\d+)?)\s*squared\b", r"(\1)**2"),
    (r"\bto the power of\b|\bpower\b", "**"),
    (r"\bmultiplied by\b|\btimes\b", "*"),
    (r"\bdivided by\b|\bover\b", "/"),
    (r"\bplus\b", "+"),
    (r"\bminus\b", "-"),
    (r"\bmod\b|\bmodulo\b", "%"),
    (r"(?<=\d)\s*x\s*(?=\d)", "*"),
    (r"\^", "**"),
]


def _fmt(value):
    if isinstance(value, float):
        return int(value) if value.is_integer() else round(value, 6)
    return value


def calculate(bot, raw, clean):
    pct = re.search(r"(\d+(?:\.\d+)?)\s*%\s*of\s*(\d+(?:\.\d+)?)", clean)
    if pct:
        a, b = float(pct.group(1)), float(pct.group(2))
        return f"{pct.group(1)}% of {pct.group(2)} = {_fmt(a * b / 100)}"
    text = clean
    for pat, rep in _WORD_OPS:
        text = re.sub(pat, rep, text)
    candidates = re.findall(r"[\d\.\s\+\-\*/\(\)%]+", text)
    candidates = [c.strip() for c in candidates if re.search(r"\d", c) and re.search(r"[\+\-\*/%]", c)]
    if not candidates:
        return "Give me an expression to solve, e.g. 'calculate 12 * (3 + 4)'."
    expr = max(candidates, key=len)
    try:
        value = _safe_eval(ast.parse(expr, mode="eval"))
    except ZeroDivisionError:
        return "Division by zero is undefined - try another expression."
    except (ValueError, SyntaxError, OverflowError):
        return "I couldn't work that out. Try something like 'calculate 12 * (3 + 4)'."
    pretty = expr.replace("**", "^")
    return f"{pretty} = {_fmt(value)}"

# --------------------------------------------------------------------------
# Fun
# --------------------------------------------------------------------------

def joke(bot, raw, clean):
    bot.pending = "joke"
    return bot.pick("joke", JOKES) + "\n\nWant another one? (yes/no)"


def fact(bot, raw, clean):
    bot.pending = "fact"
    return "Fun fact: " + bot.pick("fact", FACTS) + "\n\nWant another? (yes/no)"


def quote(bot, raw, clean):
    bot.pending = "quote"
    return bot.pick("quote", QUOTES) + "\n\nWant another? (yes/no)"

# --------------------------------------------------------------------------
# To-do list (saved to memory.json so it survives restarts)
# --------------------------------------------------------------------------

def _fmt_todos(bot):
    if not bot.memory.todos:
        return "Your to-do list is empty. Add something with 'add buy milk to my todo'."
    lines = [f"Your to-do list ({len(bot.memory.todos)}):"]
    for i, t in enumerate(bot.memory.todos, 1):
        box = "[x]" if t["done"] else "[ ]"
        lines.append(f"  {i}. {box} {t['text']}")
    return "\n".join(lines)


_ADD_PATTERNS = [
    r"(?:add|put|create)\s+(?:a\s+)?(?:new\s+)?(.+?)\s+(?:to|in|into|on)\s+(?:my\s+|the\s+)?(?:to[- ]?do|todo|task list|tasks|list)\b",
    r"(?:add|create|new)\s+(?:a\s+)?(?:to[- ]?do|todo|task)s?\s*:?\s*(.+)",
    r"remind me to\s+(.+)",
    r"^(?:todo|to do|task)\s*:?\s*(.+)",
]


def todo_add(bot, raw, clean):
    item = None
    for pat in _ADD_PATTERNS:
        m = re.search(pat, raw.strip(), re.I)
        if m:
            item = m.group(1)
            break
    if item:
        item = re.sub(r"^(task|todo|to do)\s*:?\s*", "", item.strip(), flags=re.I).strip(" .!?")
    if not item:
        return "What should I add? Try: 'add buy milk to my todo'."
    item = item[0].upper() + item[1:]
    bot.memory.todos.append({"text": item, "done": False})
    bot.memory.save()
    return f"Added: \"{item}\" (task #{len(bot.memory.todos)}).\n\n" + _fmt_todos(bot)


def todo_show(bot, raw, clean):
    return _fmt_todos(bot)


def _task_number(bot, clean):
    m = re.search(r"\d+", clean)
    n = int(m.group()) if m else 0
    if not 1 <= n <= len(bot.memory.todos):
        return None
    return n


def todo_done(bot, raw, clean):
    n = _task_number(bot, clean)
    if n is None:
        return "I couldn't find that task number.\n\n" + _fmt_todos(bot)
    bot.memory.todos[n - 1]["done"] = True
    bot.memory.save()
    return f"Nice work! Marked task #{n} as done.\n\n" + _fmt_todos(bot)


def todo_remove(bot, raw, clean):
    n = _task_number(bot, clean)
    if n is None:
        return "I couldn't find that task number.\n\n" + _fmt_todos(bot)
    removed = bot.memory.todos.pop(n - 1)
    bot.memory.save()
    return f"Removed \"{removed['text']}\".\n\n" + _fmt_todos(bot)


def todo_clear(bot, raw, clean):
    count = len(bot.memory.todos)
    bot.memory.todos.clear()
    bot.memory.save()
    return f"Cleared {count} task(s). Fresh start!" if count else "Your to-do list is already empty."

# --------------------------------------------------------------------------
# Conversation history
# --------------------------------------------------------------------------

def history(bot, raw, clean):
    mine = [text for _, who, text in bot.history if who == "you"][:-1][-5:]
    if not mine:
        return "We haven't talked about anything yet - say hello!"
    return "Your last messages:\n" + "\n".join(f"  {i}. {t}" for i, t in enumerate(mine, 1))


SKILLS = {
    "greet": greet, "how_are_you": how_are_you, "bye": bye, "help_menu": help_menu,
    "set_name": set_name, "get_name": get_name, "time_date": time_date, "calculate": calculate,
    "joke": joke, "fact": fact, "quote": quote,
    "todo_add": todo_add, "todo_show": todo_show, "todo_done": todo_done,
    "todo_remove": todo_remove, "todo_clear": todo_clear, "history": history,
}

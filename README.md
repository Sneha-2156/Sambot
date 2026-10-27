# SamBot - Rule-Based Chatbot

**SAM AI Technologies - AI Internship - Task 1: Chatbot with Rule-Based Responses**

A rule-based chatbot in pure Python (no external libraries) that understands typos, remembers your name and to-do list, does maths, and chats in the terminal **or** in a desktop window.

## Task requirements -> how SamBot meets them

| Requirement | Implementation |
|---|---|
| Predefined rules | 30+ intents in `rules.py` |
| if-else / pattern matching | Regex patterns scored by priority and match length (`engine.py`) |
| Take user input and respond | Console loop and tkinter GUI |
| Greetings, help, etc. | Greetings, small talk, help menu, jokes, facts, quotes, time/date, maths, to-do list |
| Console or simple UI | **Both**: coloured console app and a chat-bubble GUI |

## Features

- **Typo tolerance**: `tel me a joek` and `wat tiem is it` still work (difflib fuzzy matching).
- **Smart matching**: every rule is scored (`priority x 1000 + match length`), so the most specific rule wins.
- **Context and memory**: remembers your name and to-do list between runs (`memory.json`).
- **Follow-ups**: "Want another joke?" -> "yes" gives a fresh one (no repeats until all are used).
- **Safe calculator**: `calculate 12 * (3 + 4)`, `2^10`, `square root of 144`, `15% of 200` (uses `ast`, never `eval`).
- **To-do manager**: add, show, done, remove, clear.
- **Did you mean...?** suggestions when it doesn't understand.
- **Safety rule**: responds with care and points to real support if someone mentions self-harm.
- **Transcripts**: `/save` writes the conversation to `chat_logs/`.
- **Unit tests**: 13 test groups, run in milliseconds.

## Run it

Requires Python 3.9+.

```bash
python console_app.py          # terminal chat
python console_app.py --fast   # without typing animation
python gui_app.py              # desktop window (needs tkinter, included with most Python installs)
python -m unittest -v test_chatbot
```

## Try these

```
hello                              what is your name
my name is Asha                    what is my name
calculate 12 * (3 + 4)             what is 15% of 200
add buy milk to my todo            show my todo
done 1                             remove 1
what time is it                    tell me a joke
fun fact                           motivate me
help                               bye
```

Commands: `/help` `/history` `/todo` `/clear` `/save` `/exit`

## How it works

```
user text -> clean -> fix typos -> score all rules -> run skill / pick reply -> (fallback)
```

1. **clean**: lowercase, expand contractions (`what's` -> `what is`), strip punctuation.
2. **fix typos**: words not in the bot's vocabulary are matched to the closest known word.
3. **score**: each regex pattern that matches gives its rule a score; the best rule wins.
4. **respond**: a skill function (`skills.py`) or a random non-repeating canned reply.
5. **fallback**: "Did you mean ...?" or a gentle hint to type `help`.

## Project structure

```
sambot/
  rules.py         # intents, patterns, replies, jokes, facts  (edit here to teach the bot)
  skills.py        # calculator, to-do, time, name memory, jokes ...
  engine.py        # cleaning, typo fixing, scoring, memory, context
  console_app.py   # terminal UI
  gui_app.py       # tkinter UI
  test_chatbot.py  # unit tests
```

## Add your own rule (30 seconds)

In `rules.py`, add to `RULES`:

```python
Rule("coffee",
     [r"\bcoffee\b", r"\bchai\b"],
     ["Coffee is just a debugging fuel{n}!", "Chai or coffee - both compile code into features."],
     priority=5),
```

## Ideas to extend

- Load rules from a JSON file
- Add a Flask web UI
- Use TF-IDF similarity as a smarter fallback
- Add multilingual greetings

---
Built by Sneha for the SAM AI Technologies internship program.

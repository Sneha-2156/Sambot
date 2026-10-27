"""
rules.py - all the "knowledge" of SamBot lives here.

A Rule says:  "if the user's text matches one of these regex patterns,
reply with one of these responses (or run this handler)".

To teach SamBot something new, just add a Rule to RULES - no engine changes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

BOT_NAME = "SamBot"
AUTHOR = "Sneha"  # change if needed - shown when someone asks who built the bot


@dataclass
class Rule:
    intent: str                      # unique name of the intent
    patterns: list[str]              # regex patterns (matched on cleaned lowercase text)
    responses: list[str] = field(default_factory=list)  # random pick; {n} = ", <name>" if known
    handler: Optional[str] = None    # name of a function in skills.py (overrides responses)
    priority: int = 5                # higher = wins when several rules match
    suggest: Optional[str] = None    # example phrase used for "Did you mean ...?"


# --------------------------------------------------------------------------
# Static content used by skills (served without repeats until all are used)
# --------------------------------------------------------------------------
JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "There are 10 types of people: those who understand binary and those who don't.",
    "A SQL query walks into a bar, walks up to two tables and asks: 'Can I join you?'",
    "Why did the developer go broke? Because he used up all his cache.",
    "I would tell you a UDP joke, but you might not get it.",
    "Debugging: being the detective in a crime movie where you are also the murderer.",
    "Why do Java developers wear glasses? Because they don't C#.",
    "A programmer's partner says: 'Go to the shop and buy a loaf of bread. If they have eggs, buy a dozen.' He came back with 12 loaves.",
]

FACTS = [
    "The first computer 'bug' was a real moth found inside Harvard's Mark II computer in 1947.",
    "Python is named after the comedy group Monty Python, not the snake.",
    "The word 'robot' comes from the Czech word 'robota', meaning forced labour.",
    "ELIZA, created in the 1960s, was one of the first chatbots - and it was rule-based, just like me!",
    "The first email was sent by Ray Tomlinson in 1971, and he picked the @ symbol for addresses.",
    "The very first website is still online at info.cern.ch.",
    "The first 1 GB hard drive (1980) weighed over 200 kg.",
]

QUOTES = [
    "Talk is cheap. Show me the code. - Linus Torvalds",
    "Every expert was once a beginner. Keep shipping small projects.",
    "Done is better than perfect - push that commit.",
    "You don't have to be great to start, but you have to start to be great.",
    "Debugging teaches you more than a tutorial ever will.",
    "Consistency beats intensity: one hour of coding every day wins.",
]

# Words used by the "how are you?" follow-up
POSITIVE_WORDS = {"good", "great", "fine", "awesome", "amazing", "happy", "well", "okay",
                  "ok", "fantastic", "excellent", "superb", "nice", "better", "cool"}
NEGATIVE_WORDS = {"bad", "sad", "tired", "awful", "terrible", "stressed", "upset", "worse",
                  "lonely", "anxious", "angry", "exhausted", "worried"}


# --------------------------------------------------------------------------
# Intent rules
# --------------------------------------------------------------------------
RULES: list[Rule] = [
    # ---- safety first -----------------------------------------------------
    Rule(
        "safety",
        [r"\bsuicid\w*\b", r"\bkill myself\b", r"\bend my life\b", r"\bwant to die\b",
         r"\bself harm\b", r"\bhurt myself\b"],
        ["I'm really sorry you're going through something this painful. You deserve support "
         "from a real person right now - please reach out to someone you trust, or contact "
         "your local emergency number or a mental-health helpline. You don't have to face "
         "this alone."],
        priority=100,
    ),

    # ---- small talk -------------------------------------------------------
    Rule("greeting",
         [r"\b(hi+|hello+|hey+|heya|hola|namaste|yo|howdy)\b", r"\bgood (morning|afternoon|evening)\b"],
         handler="greet", priority=3, suggest="hello"),
    Rule("how_are_you",
         [r"\bhow are you\b", r"\bhow (is|are) (it going|things|you doing)\b", r"\bhow do you do\b",
          r"\bwhat is up\b", r"\bwhats up\b", r"\bsup\b"],
         ["I'm running at 100% CPU and 0% bugs - thanks for asking{n}! How about you?",
          "Doing great{n}! No errors in my logs today. How are you feeling?",
          "All systems operational{n}! How's your day going?"],
         handler="how_are_you", priority=5, suggest="how are you"),
    Rule("thanks",
         [r"\b(thanks|thank you|thank u|thx|thankyou|ty|appreciate it)\b"],
         ["You're welcome{n}! Happy to help.", "Anytime{n}!", "My pleasure{n} - ask me anything else!"],
         priority=3, suggest="thank you"),
    Rule("bye",
         [r"\b(bye|goodbye|see you|see ya|cya|good night|take care|quit|exit|talk later|gtg)\b"],
         handler="bye", priority=4, suggest="bye"),
    Rule("compliment",
         [r"\b(you are|youre) (so |very |really |quite )?(great|awesome|smart|amazing|cool|good|helpful|nice|best|clever)\b",
          r"\b(good|nice|great) (bot|job|work)\b", r"\bwell done\b", r"\bi love you\b"],
         ["Aww, thank you{n}! You're pretty awesome yourself.",
          "That made my day{n}. I'll keep my pattern-matching sharp!"],
         priority=4),
    Rule("insult",
         [r"\b(stupid|dumb|useless|idiot|worst|hate you|bad bot|you suck)\b"],
         ["Sorry I let you down{n}. Tell me what went wrong or type 'help' and I'll try again.",
          "I'm still learning - every rule I get makes me better. Try 'help' to see what I do well."],
         priority=4),

    # ---- about the bot ----------------------------------------------------
    Rule("bot_name",
         [r"\bwhat is your name\b", r"\bwho are you\b", r"\bintroduce yourself\b", r"\byour name\b",
          r"\btell me about yourself\b"],
         [f"I'm {BOT_NAME}, a rule-based assistant built for the SAM AI Technologies internship. "
          "I use regex pattern matching, typo-tolerance and a little memory to chat with you."],
         priority=5, suggest="what is your name"),
    Rule("creator",
         [r"\bwho (made|created|built|developed|programmed|wrote) you\b", r"\bwho is your (creator|developer|maker|author)\b"],
         [f"I was built by {AUTHOR} in Python as part of the SAM AI Technologies AI internship (Task 1)."],
         priority=6, suggest="who made you"),
    Rule("how_work",
         [r"\bhow do you work\b", r"\bare you (an |a )?(ai|robot|human|bot|real)\b", r"\bhow (were|are) you (built|made)\b"],
         ["I'm a rule-based bot: I clean your text, fix small typos, score every rule using regex "
          "patterns, and answer with the best match. No machine learning - every reply is explainable."],
         priority=6, suggest="how do you work"),
    Rule("age",
         [r"\bhow old are you\b", r"\byour age\b"],
         ["I'm brand new - a Python project - but I never get older than my latest commit."],
         priority=5),
    Rule("internship",
         [r"\bsam ai\b", r"\binternship\b", r"\bsam technologies\b"],
         ["I'm Task 1 of the SAM AI Technologies AI internship: a chatbot with rule-based responses "
          "using pattern matching, handling greetings, help and much more."],
         priority=5),
    Rule("help",
         [r"\bhelp\b", r"\bwhat can you do\b", r"\bcommands?\b", r"\bfeatures?\b", r"\bmenu\b", r"\bhow to use\b"],
         handler="help_menu", priority=5, suggest="help"),

    # ---- skills -----------------------------------------------------------
    Rule("name_set",
         [r"\bmy name is \w+", r"\bcall me \w+", r"\bi go by \w+", r"\bi am called \w+"],
         handler="set_name", priority=7),
    Rule("name_get",
         [r"\bwhat is my name\b", r"\bdo you (know|remember) my name\b", r"\bwho am i\b"],
         handler="get_name", priority=7, suggest="what is my name"),
    Rule("time_date",
         [r"\bwhat time\b", r"\bcurrent time\b", r"\btime is it\b", r"\btell me the time\b",
          r"\bwhat is the (date|day)\b", r"\bwhat (date|day)\b", r"\btodays date\b", r"\bcurrent date\b",
          r"\bdate today\b", r"\bwhat is today\b", r"\bthe time\b"],
         handler="time_date", priority=6, suggest="what time is it"),
    Rule("calculator",
         [r"\b(calculate|calc|compute|evaluate|solve)\b", r"\d\s*(\+|-|\*|/|x|\^|%)\s*\d",
          r"\d+\s+(plus|minus|times|multiplied by|divided by|mod|power)\s+\d+", r"\bwhat is \d",
          r"\b(square root|sqrt) of\b", r"\d\s*squared\b"],
         handler="calculate", priority=7, suggest="calculate 12 * (3 + 4)"),
    Rule("joke",
         [r"\bjokes?\b", r"\bmake me laugh\b", r"\bfunny\b", r"\bcheer me up\b", r"\bhumou?r\b"],
         handler="joke", priority=6, suggest="tell me a joke"),
    Rule("fact",
         [r"\b(fun|random|interesting|cool|tech) facts?\b", r"\btell me something (interesting|cool|new)\b", r"\bfacts?\b"],
         handler="fact", priority=6, suggest="tell me a fun fact"),
    Rule("quote",
         [r"\bquotes?\b", r"\bmotivat\w*\b", r"\binspir\w*\b"],
         handler="quote", priority=6, suggest="motivate me"),

    # ---- to-do list ---------------------------------------------------------
    Rule("todo_add",
         [r"\b(add|put|create|new)\b.*\b(to[- ]?do|task|tasks|list)\b", r"\bremind me to\b",
          r"^(todo|to do|task)\s+(?!list\b)[a-z]"],
         handler="todo_add", priority=8, suggest="add buy milk to my todo"),
    Rule("todo_show",
         [r"\b(show|list|view|see|display|open|check)\b.*\b(to[- ]?do|tasks?|list)\b",
          r"\bmy (to[- ]?do|tasks?|list)\b", r"^(todo|to do|tasks?|todo list)$"],
         handler="todo_show", priority=7, suggest="show my todo"),
    Rule("todo_done",
         [r"^(done|finish|finished|complete|completed|mark|tick|check off)\s+(task\s+|item\s+|number\s+|no\s+)?\d+\b",
          r"\bmark (task |item )?\d+ (as )?(done|complete|completed)\b"],
         handler="todo_done", priority=9, suggest="done 1"),
    Rule("todo_remove",
         [r"^(remove|delete)\s+(task\s+|item\s+|todo\s+)?\d+\b"],
         handler="todo_remove", priority=9, suggest="remove 1"),
    Rule("todo_clear",
         [r"\b(clear|empty|reset|delete all)\b.*\b(to[- ]?do|tasks|list)\b"],
         handler="todo_clear", priority=9, suggest="clear my todo"),
    Rule("history",
         [r"\b(show|see|view)\b.*\b(history|conversation)\b"],
         handler="history", priority=7),

    # ---- feelings / misc ----------------------------------------------------
    Rule("sad",
         [r"\b(sad|unhappy|depressed|lonely|stressed|anxious|worried|upset|tired|exhausted|angry|frustrated)\b"],
         ["I'm sorry you're feeling that way{n}. Taking a short break, some water and a deep breath "
          "can help. Say 'joke' or 'motivate me' if you'd like a boost.",
          "That sounds tough{n}. I'm here to chat - say 'joke' or 'motivate me' if you want a lift."],
         priority=5),
    Rule("happy",
         [r"\b(i am|i feel|im|feeling)\s+(so |very |really )?(happy|good|great|fine|awesome|amazing|excited|well|okay|ok|fantastic)\b"],
         ["That's wonderful to hear{n}! Keep that energy going.",
          "Love that{n}! Say 'fun fact' if you want a little bonus."],
         priority=5),
    Rule("bored",
         [r"\bbored\b", r"\bnothing to do\b"],
         ["Bored{n}? Try: 'tell me a joke', 'fun fact', 'calculate 25 * 4' or 'motivate me'."],
         priority=5),
    Rule("weather",
         [r"\bweather\b", r"\btemperature\b", r"\bforecast\b", r"\braining\b"],
         ["I'm an offline bot, so I can't check live weather - a weather app will do better! "
          "I can help with time, maths, jokes, facts and your to-do list though."],
         priority=5),
    Rule("tech_chat",
         [r"\b(python|java|javascript|programming|coding|developer)\b"],
         ["Love tech talk{n}! I'm written in Python. Ask me for a programming joke or a tech fun fact."],
         priority=4),
]

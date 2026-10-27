"""
console_app.py - colourful terminal chat with SamBot.

Run:   python console_app.py
Flags: --fast       no typing animation
       --no-memory  don't load/save memory.json (fresh bot every run)
       --reset      forget the saved name and to-do list first
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from engine import ChatBot
from rules import BOT_NAME

HERE = Path(__file__).resolve().parent
MEMORY_FILE = HERE / "memory.json"
LOG_DIR = HERE / "chat_logs"

# ANSI colours (enabled on Windows 10+ by the os.system("") trick below)
RESET, BOLD, DIM = "\033[0m", "\033[1m", "\033[2m"
CYAN, GREEN, YELLOW = "\033[96m", "\033[92m", "\033[93m"


def setup_terminal():
    os.system("")  # turns on ANSI escape support in the Windows terminal
    for stream in (sys.stdout, sys.stdin):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def banner():
    line = "+" + "-" * 52 + "+"
    print(CYAN + line)
    print(f"|{BOLD}{(BOT_NAME + ' - Rule-Based Chatbot').center(52)}{RESET}{CYAN}|")
    print(f"|{'SAM AI Technologies | AI Internship | Task 1'.center(52)}|")
    print(line + RESET)
    print(f"{DIM}Type 'help' for ideas. Commands: /help /history /clear /save /exit{RESET}\n")


def bot_say(text: str, animate: bool):
    stamp = datetime.now().strftime("%H:%M")
    prefix = f"{DIM}{stamp}{RESET} {CYAN}{BOLD}{BOT_NAME}:{RESET} "
    if not animate:
        print(prefix + text.replace("\n", "\n         ") + "\n")
        return
    print(f"{DIM}{BOT_NAME} is typing...{RESET}", end="\r", flush=True)
    time.sleep(0.35)
    print(" " * 30, end="\r")
    print(prefix, end="", flush=True)
    for ch in text.replace("\n", "\n         "):
        print(ch, end="", flush=True)
        time.sleep(0.006)
    print("\n")


def save_transcript(bot: ChatBot) -> Path:
    LOG_DIR.mkdir(exist_ok=True)
    path = LOG_DIR / f"chat_{datetime.now():%Y%m%d_%H%M%S}.txt"
    path.write_text(bot.transcript(), encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser(description="Chat with SamBot in the terminal")
    parser.add_argument("--fast", action="store_true", help="disable typing animation")
    parser.add_argument("--no-memory", action="store_true", help="do not use memory.json")
    parser.add_argument("--reset", action="store_true", help="forget saved name and to-dos")
    args = parser.parse_args()

    setup_terminal()
    if args.reset and MEMORY_FILE.exists():
        MEMORY_FILE.unlink()
    bot = ChatBot(None if args.no_memory else MEMORY_FILE)
    animate = not args.fast

    banner()
    bot_say(f"Hi{bot.n()}! I'm {BOT_NAME}. " +
            ("Welcome back!" if bot.memory.name else "What's your name?"), animate)
    if not bot.memory.name:
        bot.pending = "name"

    while True:
        try:
            user = input(f"{GREEN}{BOLD}You:{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        cmd = user.lower()
        if cmd in ("/exit", "/quit"):
            bot_say(f"Goodbye{bot.n()}! Saving our chat...", animate=False)
            break
        if cmd == "/clear":
            os.system("cls" if os.name == "nt" else "clear")
            banner()
            continue
        if cmd == "/save":
            print(f"{YELLOW}Saved to {save_transcript(bot)}{RESET}\n")
            continue
        bot_say(bot.reply(user), animate)
        if bot.finished:
            break

    if len(bot.history) > 2:
        print(f"{YELLOW}Transcript saved to {save_transcript(bot)}{RESET}")


if __name__ == "__main__":
    main()

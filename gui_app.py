"""
gui_app.py - desktop chat window for SamBot (tkinter, ships with Python).

Run:  python gui_app.py
"""
from __future__ import annotations

import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog

from engine import ChatBot
from rules import BOT_NAME

MEMORY_FILE = Path(__file__).resolve().parent / "memory.json"

NAVY, BLUE, LIGHT = "#12305c", "#1f6feb", "#f4f6fa"
USER_BG, BOT_BG = "#d9ecff", "#ffffff"
FONT, SMALL = ("Segoe UI", 11), ("Segoe UI", 8)

QUICK_REPLIES = [("Help", "help"), ("Joke", "tell me a joke"), ("Fun fact", "fun fact"),
                 ("Time", "what time is it"), ("To-do", "show my todo"), ("Motivate", "motivate me")]


class ChatWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.bot = ChatBot(MEMORY_FILE)
        root.title(f"{BOT_NAME} - Rule-Based Chatbot")
        root.geometry("520x680")
        root.minsize(420, 520)
        root.configure(bg=LIGHT)
        self._build_header()
        self._build_chat()
        self._build_input()
        if self.bot.memory.name:
            self._bot_message(f"Welcome back, {self.bot.memory.name}! How can I help?")
        else:
            self._bot_message(f"Hi! I'm {BOT_NAME}. What's your name?")
            self.bot.pending = "name"
        self.entry.focus_set()
        root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------ UI
    def _build_header(self):
        bar = tk.Frame(self.root, bg=NAVY, height=64)
        bar.pack(fill="x")
        tk.Label(bar, text=BOT_NAME, bg=NAVY, fg="white", font=("Segoe UI", 16, "bold")).pack(
            side="left", padx=16, pady=(10, 0), anchor="n")
        tk.Label(bar, text="SAM AI Technologies  |  Task 1", bg=NAVY, fg="#9fb8e0",
                 font=SMALL).pack(side="left", pady=(22, 0))
        tk.Button(bar, text="Save chat", command=self._save_chat, bg=BLUE, fg="white", bd=0,
                  padx=10, pady=3, activebackground="#1858c0", activeforeground="white",
                  cursor="hand2").pack(side="right", padx=12, pady=16)

    def _build_chat(self):
        frame = tk.Frame(self.root, bg=LIGHT)
        frame.pack(fill="both", expand=True)
        self.chat = tk.Text(frame, wrap="word", state="disabled", bg=LIGHT, bd=0, padx=8, pady=8,
                            font=FONT, cursor="arrow", highlightthickness=0)
        scroll = tk.Scrollbar(frame, command=self.chat.yview)
        self.chat.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.chat.pack(side="left", fill="both", expand=True)

        self.chat.tag_configure("user", background=USER_BG, justify="right", lmargin1=90,
                                lmargin2=90, rmargin=10, spacing1=4, spacing3=2)
        self.chat.tag_configure("bot", background=BOT_BG, justify="left", lmargin1=10,
                                lmargin2=10, rmargin=90, spacing1=4, spacing3=2)
        self.chat.tag_configure("time_user", foreground="#7a8699", font=SMALL, justify="right",
                                rmargin=10, spacing3=8)
        self.chat.tag_configure("time_bot", foreground="#7a8699", font=SMALL, justify="left",
                                lmargin1=10, spacing3=8)
        self.chat.tag_configure("typing", foreground="#7a8699", font=("Segoe UI", 9, "italic"),
                                lmargin1=10)

    def _build_input(self):
        quick = tk.Frame(self.root, bg=LIGHT)
        quick.pack(fill="x", padx=8, pady=(4, 0))
        for label, text in QUICK_REPLIES:
            tk.Button(quick, text=label, command=lambda t=text: self._send(t), bd=0, bg="white",
                      fg=NAVY, padx=8, pady=3, cursor="hand2", activebackground="#e3ecfa",
                      font=("Segoe UI", 9)).pack(side="left", padx=2)

        row = tk.Frame(self.root, bg=LIGHT)
        row.pack(fill="x", padx=8, pady=8)
        self.entry = tk.Entry(row, font=FONT, bd=0, relief="flat", highlightthickness=1,
                              highlightbackground="#c9d3e3", highlightcolor=BLUE)
        self.entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self.entry.bind("<Return>", lambda _e: self._send())
        tk.Button(row, text="Send", command=self._send, bg=BLUE, fg="white", bd=0, padx=18,
                  pady=7, activebackground="#1858c0", activeforeground="white",
                  cursor="hand2", font=("Segoe UI", 10, "bold")).pack(side="right")

    # ------------------------------------------------------------ messaging
    def _append(self, text: str, tag: str, stamp_tag: str):
        stamp = datetime.now().strftime("%H:%M")
        self.chat.configure(state="normal")
        self.chat.insert("end", f" {text} \n", tag)
        self.chat.insert("end", f"{stamp}\n", stamp_tag)
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def _user_message(self, text: str):
        self._append(text, "user", "time_user")

    def _bot_message(self, text: str):
        self._append(text, "bot", "time_bot")

    def _show_typing(self):
        self.chat.configure(state="normal")
        self.chat.insert("end", f"{BOT_NAME} is typing...\n", "typing")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def _hide_typing(self):
        self.chat.configure(state="normal")
        ranges = self.chat.tag_ranges("typing")
        if ranges:
            self.chat.delete(ranges[0], ranges[-1])
        self.chat.configure(state="disabled")

    def _send(self, text: str | None = None):
        text = (text if text is not None else self.entry.get()).strip()
        if not text:
            return
        self.entry.delete(0, "end")
        if text.lower() == "/clear":
            self.chat.configure(state="normal")
            self.chat.delete("1.0", "end")
            self.chat.configure(state="disabled")
            return
        if text.lower() == "/save":
            self._save_chat()
            return
        if text.lower() in ("/exit", "/quit"):
            self._on_close()
            return
        self._user_message(text)
        self._show_typing()
        self.root.after(450, lambda: self._deliver(text))

    def _deliver(self, text: str):
        answer = self.bot.reply(text)
        self._hide_typing()
        self._bot_message(answer)
        if self.bot.finished:
            self.root.after(1400, self._on_close)

    def _save_chat(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("Text file", "*.txt")],
            initialfile=f"sambot_chat_{datetime.now():%Y%m%d_%H%M}.txt")
        if path:
            Path(path).write_text(self.bot.transcript(), encoding="utf-8")
            self._bot_message("Conversation saved.")

    def _on_close(self):
        self.root.destroy()


def main():
    root = tk.Tk()
    ChatWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()

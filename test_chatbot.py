"""Run with:  python -m unittest -v test_chatbot"""
import tempfile
import unittest
from pathlib import Path

from engine import ChatBot


def fresh(named=True):
    bot = ChatBot(None)
    if named:
        bot.memory.name = "Asha"
    return bot


class IntentTests(unittest.TestCase):
    def check(self, text, intent, bot=None):
        bot = bot or fresh()
        bot.reply(text)
        self.assertEqual(bot.last_intent, intent, f"'{text}' -> {bot.last_intent}")

    def test_core_intents(self):
        cases = {
            "hello": "greeting", "Hey there!": "greeting", "good morning": "greeting",
            "how are you?": "how_are_you", "what's your name": "bot_name", "who made you": "creator",
            "help": "help", "what can you do": "help", "thanks a lot": "thanks", "bye": "bye",
            "what time is it": "time_date", "what's today's date": "time_date",
            "tell me a joke": "joke", "fun fact please": "fact", "motivate me": "quote",
            "i am so sad": "sad", "i am bored": "bored", "how's the weather": "weather",
            "who are you": "bot_name", "how do you work": "how_work",
        }
        for text, intent in cases.items():
            with self.subTest(text=text):
                self.check(text, intent)

    def test_typo_tolerance(self):
        for text, intent in {"helo": "greeting", "tel me a joek": "joke", "wat tiem is it": "time_date",
                             "whats yuor name": "bot_name", "thnaks": "thanks", "what is yur nme": "bot_name"}.items():
            with self.subTest(text=text):
                self.check(text, intent)

    def test_greeting_echoes_part_of_day(self):
        self.assertTrue(fresh().reply("good evening").startswith("Good evening"))

    def test_safety_rule_wins(self):
        self.check("i want to die, help", "safety")


class CalculatorTests(unittest.TestCase):
    def test_expressions(self):
        cases = {
            "calculate 12 * (3 + 4)": "84", "what is 2^10": "1024", "5 plus 7": "12",
            "what is 10 divided by 4": "2.5", "square root of 144": "12", "9 squared": "81",
            "compute 100 - 45": "55", "what is 15% of 200": "30", "what is 7 x 6": "42", "17 mod 5": "2",
        }
        for text, result in cases.items():
            with self.subTest(text=text):
                self.assertIn(f"= {result}", fresh().reply(text))

    def test_errors_and_safety(self):
        self.assertIn("zero", fresh().reply("calculate 5 / 0"))
        self.assertNotIn("Error", fresh().reply("calculate 9 ** 99999"))  # guarded, no hang


class MemoryAndTodoTests(unittest.TestCase):
    def test_name_flow(self):
        bot = fresh(named=False)
        self.assertIn("name", bot.reply("hello").lower())
        self.assertIn("Sneha", bot.reply("sneha"))          # bare name accepted after the question
        self.assertEqual(bot.reply("what is my name"), "Your name is Sneha.")
        self.assertIn("Ravi", bot.reply("call me ravi"))

    def test_yes_no_follow_up(self):
        bot = fresh()
        first = bot.reply("tell me a joke")
        self.assertIn("Want another", first)
        self.assertNotEqual(bot.reply("yes").split("\n")[0], first.split("\n")[0])
        self.assertIn("No problem", bot.reply("no"))

    def test_todo_lifecycle(self):
        bot = fresh()
        self.assertIn("empty", bot.reply("show my todo"))
        self.assertIn("Buy milk", bot.reply("add buy milk to my todo"))
        bot.reply("remind me to call mom")
        bot.reply("add task: finish report")
        self.assertEqual(len(bot.memory.todos), 3)
        self.assertIn("[x]", bot.reply("done 1"))
        self.assertIn("Removed", bot.reply("remove 2"))
        self.assertEqual(len(bot.memory.todos), 2)
        self.assertIn("Cleared", bot.reply("clear my todo"))

    def test_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "memory.json"
            bot = ChatBot(path)
            bot.reply("my name is Meera")
            bot.reply("add study DSA to my todo")
            again = ChatBot(path)
            self.assertEqual(again.memory.name, "Meera")
            self.assertEqual(again.memory.todos[0]["text"], "Study DSA")


class RobustnessTests(unittest.TestCase):
    def test_fallback_and_suggestions(self):
        bot = fresh()
        self.assertTrue(bot.reply("asdfgh qwerty"))
        self.assertEqual(bot.last_intent, "fallback")

    def test_empty_and_long_input(self):
        bot = fresh()
        self.assertIn("Say something", bot.reply("   "))
        self.assertTrue(bot.reply("a" * 5000))

    def test_goodbye_sets_finished(self):
        bot = fresh()
        bot.reply("bye")
        self.assertTrue(bot.finished)

    def test_commands(self):
        bot = fresh()
        self.assertIn("can do", bot.reply("/help"))
        self.assertIn("Unknown command", bot.reply("/nope"))


if __name__ == "__main__":
    unittest.main()

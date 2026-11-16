"""Coloured console messages."""
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import TerminalFormatter
from pygments.util import ClassNotFound


class Logger:
    """Prints a message in a colour; every method is static."""

    @staticmethod
    def error(text: str) -> None:
        """Print *text* in red."""
        print("\033[31m" + text + "\033[0m")

    @staticmethod
    def success(text: str) -> None:
        """Print *text* in green."""
        print("\033[92m" + text + "\033[0m")

    @staticmethod
    def warning(text: str) -> None:
        """Print *text* in yellow."""
        print("\033[33m" + text + "\033[0m")

    @staticmethod
    def log(text: str) -> None:
        """Print *text* unchanged."""
        print(text)

    @staticmethod
    def code(code: str, language: str = "python") -> None:
        """Print code with syntax highlighting."""
        print()
        try:
            lexer = get_lexer_by_name(language)
            formatted = highlight(code, lexer, TerminalFormatter())
            print(formatted, end="")
        except ClassNotFound:
            Logger.warning(f"Unknown language: {language}")
            print(code)
        print()
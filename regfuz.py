"""Compatibility entry point; prefer refuzz and the refuzz command."""

from refuzz import (LimitError, Regex, RegexError, generate_pattern, main,
                      print_tree)

__all__ = ['LimitError', 'Regex', 'RegexError', 'generate_pattern', 'main',
           'print_tree']

if __name__ == '__main__':
    raise SystemExit(main())

"""Compatibility entry point; prefer r_e_fuzz and the r-e-fuzz command."""

from r_e_fuzz import (LimitError, Regex, RegexError, generate_pattern, main,
                      print_tree)

__all__ = ['LimitError', 'Regex', 'RegexError', 'generate_pattern', 'main',
           'print_tree']

if __name__ == '__main__':
    raise SystemExit(main())

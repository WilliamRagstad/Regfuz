<div align="center"><img src="logo.png" alt="Regfuz logo"><h3>Regular Expression Fuzzer</h3></div>

Regfuz generates examples of a defined subset of Python's string regular
expressions. Each returned example satisfies `re.fullmatch(pattern, example)`.
It is a small generator, not a regex engine or a uniform sampler.

## Supported syntax

- Literal Unicode characters, including significant leading/trailing whitespace.
  The empty pattern generates the empty string.
- Concatenation, dot (excluding newline), positive and negated character classes,
  inclusive Unicode ranges, and literal `]` as the first class member or escaped.
- Escaped ASCII punctuation and space; `\n \r \t \f \a \v`;
  categories `\d \D \w \W \s \S`, also inside classes.
- Greedy `?`, `*`, `+`, `{m}`, `{m,n}`, `{m,}`. Bounds use ASCII digits,
  at most nine digits each. Reversed bounds/ranges are errors.

Groups (including capturing groups), alternation, anchors, assertions,
backreferences, inline flags, lazy/possessive quantifiers, and other escapes
(including hex, octal, Unicode escapes and named characters) are unsupported and
raise `RegexError`. Use literal Unicode characters instead of Unicode escapes.
Escape literal operators; unescaped braces and closing brackets outside classes
are rejected even where Python would accept them as literals.

Dot, categories, and negated classes sample only from `string.printable` (100
ASCII characters, including whitespace). Positive classes and literals may emit
Unicode. This is intentionally incomplete sampling of Python's Unicode matching
language. A negated class with no candidates in that alphabet is rejected, even
if quantified with `?` or `{0}`. No flags or compiled-pattern inputs are accepted.
Python's `re` validates syntax, but generation does not use rejection sampling or
execute potentially expensive regex matches.

## Usage

Requires Python 3.10 or later, with no runtime dependencies. Install from a checkout:

```sh
python -m pip install .
regfuz 'hel+o[0a-z\.]+' --seed 42 -t 5
regfuz '[A-Z]{2}\d{3}' --seed 42 --max-length 5
python -m regfuz '[a-z]+' --seed 7 -t 3
```

The installed `regfuz` command, `python -m regfuz`, and direct script entry point
use the same CLI. Build wheel and source distributions using the standard
[Python packaging workflow](https://packaging.python.org/en/latest/tutorials/packaging-projects/):

```sh
python -m pip install build
python -m build
```

Run directly from a checkout:

```sh
python regfuz.py 'hel+o[0a-z\.]+' --seed 42 -t 5
python regfuz.py '[a-zA-Z0-9\.]+' -t 1 -v --seed 7
python regfuz.py '[a-z]+' -t 0 -v
python regfuz.py 'a*bbbb' --max-length 4 --seed 1
```

`-v` prints the parsed atoms and uses `repr` for generated strings, so whitespace
is visible. Otherwise each result is printed followed by a newline; generated
values may themselves contain newlines. Shell-quote patterns and use `--` before
a pattern beginning with `-`.

| Option | Default | Meaning |
| --- | --- | --- |
| `-t`, `--tests` | 10 | Number of examples (zero allows tree inspection) |
| `-q`, `--quantity` | 10 | Maximum repetitions per quantified atom |
| `--seed` | unset | Integer seed for a private random generator |
| `--max-length` | 1024 | Maximum characters per result |
| `--max-work` | 100000 | Maximum generation units for the entire batch |

All counts and limits must be nonnegative integers. Patterns are limited to
4096 characters before parsing. Work counts one unit per result, one per atom
visit, and one per emitted character. Character selection scans at most the
bounded pattern's class entries; these units are not CPU time or bytes.
Minimum lengths are reserved for following atoms. Quantifier minima exceeding
`--quantity`, or patterns whose minimum length exceeds `--max-length`, fail
clearly. A work-budget failure aborts the batch without printing partial results.
Bounds apply even with `-t 0`. Limits count Unicode code points, not encoded bytes.
Increasing limits explicitly allows more memory and work.

The same pattern, options, seed, and Regfuz/Python version reproduce the same
ordered batch; global `random` state is untouched. Version-to-version sequence
stability is not promised. Invalid input and exhausted limits exit with status 2
and a message on stderr.

## Python API and tests

```python
import re
from regfuz import Regex

pattern = r'[A-Z]{2}\d{3}'
values = Regex(pattern).generate(20, seed=42, max_length=5)
assert all(re.fullmatch(pattern, value) for value in values)
```

`RegexError` and `LimitError` inherit from `ValueError`. The former
`generate_pattern(Regex(pattern).root, quantityMax)` call is retained; use
`Regex.generate` for seeded batches. Internal tree node classes have changed.

```sh
python -m unittest discover -s tests -v
```

Tests cover a fixed and deterministically constructed corpus against Python
[`re.fullmatch`](https://docs.python.org/3/library/re.html#re.fullmatch), seeds,
limits, unsupported/malformed inputs, and CLI errors.

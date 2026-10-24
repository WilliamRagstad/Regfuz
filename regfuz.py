"""Generate bounded examples of a deliberately small Python regex subset."""

import argparse
from dataclasses import dataclass
import random
import re
import string


class RegexError(ValueError):
    """Malformed, unsupported, or unsatisfiable regular expression."""


class LimitError(ValueError):
    """A configured resource limit cannot be satisfied."""


ALPHABET = string.printable  # fixed ASCII sampling domain for negation/dot/categories
CATEGORIES = {'d': string.digits, 'w': string.ascii_letters + string.digits + '_',
              's': ' \t\n\r\f\v'}
CONTROLS = dict(zip('nrtfav', '\n\r\t\f\a\v'))
MAX_PATTERN = 4096


def _integer(name, value):
    if type(value) is not int or value < 0:
        raise ValueError(f'{name} must be a non-negative integer')
    return value


@dataclass(frozen=True)
class Atom:
    ranges: tuple
    minimum: int = 1
    maximum: object = 1
    quantified: bool = False

    def choose(self, rng):
        index = rng.randrange(sum(hi - lo + 1 for lo, hi in self.ranges))
        for lo, hi in self.ranges:
            width = hi - lo + 1
            if index < width:
                return chr(lo + index)
            index -= width
        raise AssertionError('empty character set')


def _chars(chars):
    return tuple((ord(c), ord(c)) for c in chars)


class _Parser:
    def __init__(self, pattern):
        self.pattern = pattern
        self.i = 0

    def error(self, message):
        raise RegexError(f'{message} at index {self.i}')

    def escape(self):
        self.i += 1
        if self.i == len(self.pattern):
            self.error('missing escaped character')
        c = self.pattern[self.i]
        self.i += 1
        if c.lower() in CATEGORIES:
            chars = CATEGORIES[c.lower()]
            if c.isupper():
                chars = ''.join(x for x in ALPHABET if x not in chars)
            return _chars(chars), False
        if c in CONTROLS:
            return _chars(CONTROLS[c]), True
        if c in string.punctuation or c == ' ':
            return _chars(c), True
        self.error(f'unsupported escape \\{c}')

    def class_item(self):
        if self.pattern[self.i] == '\\':
            return self.escape()
        c = self.pattern[self.i]
        self.i += 1
        return _chars(c), True

    def character_class(self):
        self.i += 1
        negate = self.i < len(self.pattern) and self.pattern[self.i] == '^'
        if negate:
            self.i += 1
        ranges = []
        first = True
        while self.i < len(self.pattern):
            if self.pattern[self.i] == ']' and not first:
                self.i += 1
                if negate:
                    ranges = _chars(c for c in ALPHABET
                                    if not any(lo <= ord(c) <= hi for lo, hi in ranges))
                if not ranges:
                    self.error('character class has no values in the sampling alphabet')
                return tuple(ranges)
            left, single = self.class_item()
            first = False
            if (self.i + 1 < len(self.pattern) and self.pattern[self.i] == '-'
                    and self.pattern[self.i + 1] != ']'):
                self.i += 1
                right, right_single = self.class_item()
                if not single or not right_single or left[0][0] > right[0][0]:
                    self.error('invalid character range')
                ranges.append((left[0][0], right[0][0]))
            else:
                ranges.extend(left)
        self.error('unterminated character class')

    def parse(self):
        atoms = []
        while self.i < len(self.pattern):
            c = self.pattern[self.i]
            if c == '[':
                ranges = self.character_class()
            elif c == '\\':
                ranges, _ = self.escape()
            elif c == '.':
                self.i += 1
                ranges = _chars(ALPHABET.replace('\n', ''))
            elif c in '()|^$':
                self.error(f'unsupported construct {c!r}')
            elif c in '*+?{}]':
                self.error(f'unexpected operator {c!r}; escape it for a literal')
            else:
                self.i += 1
                ranges = _chars(c)
            low = high = 1
            quantified = False
            if self.i < len(self.pattern):
                c = self.pattern[self.i]
                if c in '*+?':
                    quantified = True
                    low, high = {'*': (0, None), '+': (1, None), '?': (0, 1)}[c]
                    self.i += 1
                elif c == '{':
                    quantified = True
                    end = self.pattern.find('}', self.i)
                    if end < 0:
                        self.error('unterminated quantifier')
                    body = self.pattern[self.i + 1:end]
                    if not re.fullmatch(r'[0-9]+(?:,[0-9]*)?', body):
                        self.error('unsupported quantifier; use {m}, {m,n}, or {m,}')
                    parts = body.split(',')
                    # Avoid huge integers and Python re overflow, before conversion.
                    if any(len(part) > 9 for part in parts):
                        self.error('quantifier exceeds supported integer range')
                    low = int(parts[0])
                    high = low if len(parts) == 1 else int(parts[1]) if parts[1] else None
                    if high is not None and high < low:
                        self.error('quantifier maximum is less than minimum')
                    self.i = end + 1
            atoms.append(Atom(ranges, low, high, quantified))
        return tuple(atoms)


class Regex:
    """Parsed subset. Whitespace is significant; empty patterns are supported."""

    def __init__(self, regex):
        if not isinstance(regex, str):
            raise TypeError('regex must be a string')
        if len(regex) > MAX_PATTERN:
            raise LimitError(f'pattern exceeds {MAX_PATTERN} characters')
        self.root = _Parser(regex).parse()
        # Python is the syntax authority, but never used to search generated output.
        try:
            re.compile(regex)
        except (re.error, OverflowError) as exc:
            raise RegexError(f'invalid regular expression: {exc}') from exc
        self.matched = True

    def generate(self, count=1, *, seed=None, quantity=10, max_length=1024,
                 max_work=100000):
        """Return examples; work counts cases, atom visits, and emitted characters."""
        return _generate(self.root, count, random.Random(seed), quantity,
                         max_length, max_work)


def _generate(atoms, count, rng, quantity, max_length, max_work):
    for name, value in [('count', count), ('quantity', quantity),
                        ('max_length', max_length), ('max_work', max_work)]:
        _integer(name, value)
    minimum = sum(atom.minimum for atom in atoms)
    if minimum > max_length:
        raise LimitError('minimum match length exceeds max_length')
    maxima = [quantity if a.maximum is None else min(a.maximum, quantity) for a in atoms]
    # quantity applies to quantified atoms; bare characters always occur once.
    maxima = [1 if not a.quantified else n for a, n in zip(atoms, maxima)]
    if any(a.minimum > n for a, n in zip(atoms, maxima)):
        raise LimitError('quantifier minimum exceeds quantity')
    if count * (1 + len(atoms) + minimum) > max_work:
        raise LimitError('minimum generation work exceeds max_work')
    work = 0
    results = []
    for _ in range(count):
        work += 1
        remaining = minimum
        length = 0
        chunks = []
        for atom, maximum in zip(atoms, maxima):
            remaining -= atom.minimum
            times = rng.randint(atom.minimum, min(maximum, max_length - length - remaining))
            work += 1 + times
            if work > max_work:
                raise LimitError('generation exceeds max_work')
            chunks.extend(atom.choose(rng) for _ in range(times))
            length += times
        results.append(''.join(chunks))
    return results


def generate_pattern(node, quantityMax=10, *, seed=None, max_length=1024, max_work=100000):
    """Compatibility wrapper for generate_pattern(Regex(pattern).root, quantityMax)."""
    return _generate(node, 1, random.Random(seed), quantityMax, max_length, max_work)[0]


def print_tree(node):
    print('ROOT')
    for atom in node:
        print(f' {atom!r}')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('regex', help='supported Python regex (see README)')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-t', '--tests', type=int, default=10)
    parser.add_argument('-q', '--quantity', type=int, default=10)
    parser.add_argument('--seed', type=int)
    parser.add_argument('--max-length', type=int, default=1024)
    parser.add_argument('--max-work', type=int, default=100000)
    args = parser.parse_args(argv)
    try:
        regex = Regex(args.regex)
        values = regex.generate(args.tests, seed=args.seed, quantity=args.quantity,
                                max_length=args.max_length, max_work=args.max_work)
    except (ValueError, TypeError) as exc:
        parser.error(str(exc))
    if args.verbose:
        print_tree(regex.root)
    for i, value in enumerate(values, 1):
        print(f'Test {i}: {value!r}' if args.verbose else value)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

import random
import re
import subprocess
import sys
import unittest

from refuzz import LimitError, Regex, RegexError, generate_pattern


class GenerationTests(unittest.TestCase):
    def test_corpus(self):
        patterns = ['', ' ', ' a ', 'hello', 'é水😀', '.', '.*', '.+',
                    '[a-zA-Z0-9_.]+', r'\d+\s?\w{2,5}', r'\D\S\W',
                    '[^a-z]+', '[^\n]', '[]a]+', '[-a]+', '[a-]+',
                    r'[\]\-\\]+', r'[\dA-F]{2,8}', '[é-水]{1,3}',
                    r'\n\r\t\f\a\v', r'\.\*\+\?\{\}\[\]\(\)\|\^\$',
                    'a{0}b{2}c{1,}d?', 'a*bbbb',
                    r'[^\d\w]']
        rng = random.Random(2048)
        atoms = ['a', '水', '.', '[a-f]', '[^x]', r'\d', r'\s', r'\W', r'\+']
        repeats = ['', '*', '+', '?', '{0}', '{2}', '{1,4}', '{0,}']
        patterns += [''.join(rng.choice(atoms) + rng.choice(repeats)
                             for _ in range(rng.randrange(1, 9))) for _ in range(300)]
        for pattern in patterns:
            with self.subTest(pattern=pattern):
                for value in Regex(pattern).generate(30, seed=42, max_length=80):
                    self.assertIsNotNone(re.fullmatch(pattern, value), (pattern, value))
                    self.assertLessEqual(len(value), 80)

    def test_seed_and_global_random(self):
        regex = Regex(r'[a-z]+\d*')
        state = random.getstate()
        self.assertEqual(regex.generate(100, seed=5), regex.generate(100, seed=5))
        self.assertEqual(state, random.getstate())
        self.assertNotEqual(regex.generate(10, seed=5), regex.generate(10, seed=6))
        self.assertEqual(generate_pattern(regex.root, seed=5), regex.generate(seed=5)[0])

    def test_rejections(self):
        for pattern in ['[', '[]', '[z-a]', '\\', '*a', 'a**', 'a{', 'a{2,1}',
                        'a{,2}', 'a{999999999999}', '(a)', '(?:a)', '(?=a)',
                        '(?i)a', 'a|b', '^a$', r'\1', r'\b', r'\x41',
                        'a*?', 'a++', r'[\d-z]', r'[^\s\S]']:
            with self.subTest(pattern=pattern), self.assertRaises(RegexError):
                Regex(pattern)

    def test_limits(self):
        with self.assertRaises(LimitError):
            Regex('a' * 4097)
        for pattern, kwargs in [('a{20}', {}), ('aaaa', {'max_length': 3}),
                                ('a+', {'quantity': 0}), ('a{1}', {'quantity': 0}), ('a', {'max_work': 2}),
                                ('', {'count': 100001}), ('a*', {'max_work': 2, 'seed': 0})]:
            with self.subTest(pattern=pattern, kwargs=kwargs), self.assertRaises(LimitError):
                Regex(pattern).generate(**kwargs)
        for key in ['count', 'quantity', 'max_length', 'max_work']:
            for value in [-1, 1.5, True]:
                with self.assertRaises(ValueError):
                    Regex('a').generate(**{key: value})
        self.assertEqual(Regex('').generate(3, max_length=0, max_work=3), ['', '', ''])
        self.assertEqual(Regex('a*bbbb').generate(10, max_length=4), ['bbbb'] * 10)
        self.assertEqual(Regex('a{0}').generate(1, quantity=0, max_length=0), [''])

    def test_cli(self):
        command = [sys.executable, 'refuzz.py', r'[a-z]+', '--seed', '12', '-t', '3']
        first = subprocess.run(command, capture_output=True, text=True, check=True)
        second = subprocess.run(command, capture_output=True, text=True, check=True)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(len(first.stdout.splitlines()), 3)
        for args in [['(a)'], ['a', '-t', '-1'], ['a+', '-q', '0']]:
            result = subprocess.run([sys.executable, 'refuzz.py'] + args,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '')
            self.assertIn('error:', result.stderr)
            self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()

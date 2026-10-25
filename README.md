<div align="center">
  <img src="logo.png" alt="ReFuzz logo" width="480">
  <hr/>
</div>

```console
$ refuzz '[A-Z]{2}\d{3}' --seed 42 -t 3
AX332
VX960
CG890
```

**Regex in, matching strings out.** ReFuzz generates test data for a defined
subset of Python regular expressions. Every result satisfies `re.fullmatch`.

## Install and run

Python 3.10+, no runtime dependencies. From a checkout:

```sh
python -m pip install .
refuzz '[A-Z]{2}\d{3}' --seed 42 -t 3
```

You can also run `python -m refuzz` or `python refuzz.py`.
Use `--seed` to repeat a batch, `-t` to set its size, and `-v` to see escaped output.
Run `refuzz --help` for all options.

## Scope and limits

Supports literals, dot, character classes, common escapes such as `\d`, and
greedy quantifiers such as `+` and `{2,5}`. Groups, alternation, anchors,
lookarounds, backreferences, and flags are rejected explicitly.

Defaults cap repetitions at 10 per atom, output at 1,024 characters per result,
and generation work at 100,000 units per batch. Dot, categories, and negated
classes sample ASCII; literals and positive ranges support Unicode.

See the [reference](docs/reference.md) for exact syntax, bounds, seed guarantees,
the Python API, and build instructions. The old `regfuz` command and imports
remain compatibility aliases.

## Tests

```sh
python -m unittest discover -s tests -v
```

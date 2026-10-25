"""Run against a wheel installed in a clean venv, outside the source checkout.

Usage: python tests/check_install.py /path/to/venv/bin/python
"""
import pathlib
import re
import subprocess
import sys
import tempfile

cli = pathlib.Path(sys.argv[1]).absolute().parent / 'r-e-fuzz'
# Keep the venv path (resolving its Python symlink would select the base interpreter).
python = pathlib.Path(sys.argv[1]).absolute()
with tempfile.TemporaryDirectory() as directory:
    def run(command):
        return subprocess.run(command, cwd=directory, text=True,
                              capture_output=True, check=True).stdout

    for pattern, extra in [(r'hel+o[0a-z\.]+', ['-t', '5']),
                           (r'[A-Z]{2}\d{3}', ['--max-length', '5']),
                           ('[a-z]+', ['-t', '3']),
                           ('a*bbbb', ['--max-length', '4'])]:
        args = [pattern, '--seed', '42'] + extra
        output = run([str(cli)] + args)
        assert output == run([str(python), '-m', 'r_e_fuzz'] + args)
        assert output == run([str(cli.with_name('regfuz'))] + args)
        assert output == run([str(python), '-m', 'regfuz'] + args)
        assert all(re.fullmatch(pattern, value) for value in output.splitlines())
    assert 'ROOT' in run([str(cli), '[a-z]+', '-t', '0', '-v'])
    assert 'Test 1:' in run([str(cli), r'[a-zA-Z0-9\.]+', '-t', '1', '-v', '--seed', '7'])
    run([str(python), '-c', 'from r_e_fuzz import Regex; assert len(Regex("a").generate()) == 1'])
    run([str(python), '-c', 'import regfuz, r_e_fuzz; assert regfuz.Regex is r_e_fuzz.Regex'])
    run([str(python), '-c', 'from importlib.metadata import metadata; assert metadata("R-E-Fuzz")["Name"] == "R-E-Fuzz"'])
print('Installed CLI, module, API, and documented examples passed')

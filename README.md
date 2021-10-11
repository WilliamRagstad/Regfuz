<div align=center>
    <img src="logo.png"> 
	<h3>Regular Expression Fuzzer</h3>
</div>



# About

This project aims to make finding bugs and understanding the structure of [regular expressions](https://en.wikipedia.org/wiki/Regular_expression) easier. This is a command line utility tool that generates valid inputs to a regular expressions.



# Usage

Download the `regfuz.py` file and run it with python.

```bash
usage: regfuz.py [-h] [-v] [-t TESTS] [-q QUANTITY] regex

A command line program that takes a regular expression as input and parses the structure into a tree. The tree is then traversed, omitting valid character patterns that satisfy the entered regular expression.

positional arguments:
  regex                 the regular expression to parse

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         prints the parsed abstract expression tree and more test information
  -t TESTS, --tests TESTS
                        number of tests to run
  -q QUANTITY, --quantity QUANTITY
                        max number of characters to generate for quantity operator patterns
```



# Examples

```bash
> py regfuz.py "hel+o[0a-z\.]+"
hellobdgd
helllloyt0past
hellllllovxzmxz.po.
helloownasful
helllllou
hellllllor.pbxe
helllo.qhshglyx
helllllovu0afbn
hellloddbs.tn
hellllllllloz
```

The `-v` option will display the parsed abstract expression tree for the regular expression. To only display the tree, use `-t 0 -v`.

```bash
> py regfuz.py "[a-zA-Z0-9\.]+" -t 1 -v 
======== Tree ========
ROOT
 PLUS
  BRACKET: ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.']
======== Tests ========
Test 1:
  Pattern: I6mUTMU.qI
  Satisfies regular expression: True
```


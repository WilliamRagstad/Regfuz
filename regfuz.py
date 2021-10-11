"""
A command line program that takes a regular expression as input and parses the structure into a tree. The tree is then traversed, omitting valid character patterns that will satesfy the input regular expression.
"""

import argparse
import re
import random

# A class that represents a node in the tree
class NodeWithValue:
	def __init__(self, name: str, value):
		self.name = name
		self.value = value
# A class that represents a node in the tree
class NodeWithChildren:
	def __init__(self, name: str, children: list):
		self.name = name
		self.children = children

# A class that represents a regular expression
class Regex:
	def __init__(self, regex: str):
		self.__parseRegExp(regex)

	# A method that parses the regular expression into a tree
	def __parseRegExp(self, regex):
		# Trim regex string
		regex = regex.strip()
		tree = NodeWithChildren('ROOT', [])

		i = 0
		c = None
		while i < len(regex):
			c = regex[i]
			if c == '[':
				# Find the closing bracket
				closing = regex.find(']', i)
				# Get the characters inside the brackets
				charExprs = regex[i+1:closing]
				# Parse the characters inside the brackets
				validCharacters = self.__parseCharExpr(charExprs, i)
				tree.children.append(NodeWithValue('BRACKET', validCharacters))
				i = closing
			elif c == '*':
				# Take the last element of the tree children and create a new node with the value 'STAR' with that node as child
				tree.children.append(NodeWithChildren('STAR', [tree.children.pop()]))
			elif c == '+':
				# Take the last element of the tree children and create a new node with the value 'PLUS' with that node as child
				tree.children.append(NodeWithChildren('PLUS', [tree.children.pop()]))
			elif c == '.':
				# Any character
				tree.children.append(NodeWithValue('ANY', None))
			else:
				# Append the character to the tree children
				tree.children.append(NodeWithValue('CHAR', c))
			i += 1

		self.root = tree
		self.matched = len(tree.children) > 0

	def __parseCharExpr(self, charExpr, globalIndex):
		# Parse regular expressions of the form [abcA-Z\.\*]
		# charExpr is the characters inside the brackets
		# Return a list of valid characters
		validCharacters = []
		i = 0
		while i < len(charExpr):
			c = charExpr[i]
			cn = None
			if i + 1 < len(charExpr):
				cn = charExpr[i+1]

			if c == '\\':
				# Append the next character to the list of valid characters
				if cn == None:
					self.__invalidRegExp('Escaped character is missing at index ' + str(globalIndex + i))
				validCharacters.append(cn)
				i += 1
			elif cn == '-':
				# Append all characters from the first character to the second character to the list of valid characters
				if i + 2 >= len(charExpr):
					self.__invalidRegExp('Invalid character range at index ' + str(globalIndex + i))
				cnn = charExpr[i+2]
				validCharacters.extend([chr(v) for v in range(ord(c),ord(cnn)+1)])
				i += 2
			else:
				# Append the character to the list of valid characters
				validCharacters.append(c)
			i += 1

		return validCharacters

	def __invalidRegExp(self, message):
		raise Exception('Invalid regular expression: ' + message)


# A method that prints the tree
def print_tree(node, depth=0):
	if node is None:
		return

	print(' '*depth + node.name, end='')

	if isinstance(node, NodeWithValue):
		print([': ' + str(node.value),''][node.value == None])
	elif isinstance(node, NodeWithChildren):
		print() # Newline
		for child in node.children:
			print_tree(child, depth+1)
	else:
		raise Exception('Invalid node type')

def generate_pattern(node, quantityMax):
	if node is None:
		return

	if isinstance(node, NodeWithValue):
		if node.name == 'ANY':
			return chr(random.randint(0,255))
		if node.name == 'CHAR':
			return node.value
		elif node.name == 'BRACKET':
			return random.choice(node.value)
	elif isinstance(node, NodeWithChildren):
		if node.name == 'ROOT':
			pattern = ''
			for child in node.children:
				pattern += generate_pattern(child, quantityMax)
			return pattern
		elif node.name == 'STAR':
			times = random.randint(0,quantityMax)
			pattern = ''
			for _ in range(times):
				pattern += generate_pattern(node.children[0], quantityMax)
			return pattern
		elif node.name == 'PLUS':
			times = random.randint(1,quantityMax)
			pattern = ''
			for _ in range(times):
				pattern += generate_pattern(node.children[0], quantityMax)
			return pattern

	raise Exception('Invalid node type: ' + node.name + ' ' + str(node))

# Main method that takes a regular expression as input and prints the tree
def main():
	parser = argparse.ArgumentParser(description='A command line program that takes a regular expression as input and parses the structure into a tree. The tree is then traversed, omitting valid character patterns that satisfy the entered regular expression.')
	parser.add_argument('regex', help='the regular expression to parse')
	parser.add_argument('-v', '--verbose', action='store_true', help='prints the parsed abstract expression tree and more test information', default=False)
	parser.add_argument('-t', '--tests', help='number of tests to run', type=int, default=10)
	parser.add_argument('-q', '--quantity', help='max number of characters to generate for quantity operator patterns', type=int, default=10)
	args = parser.parse_args() # parser.parse_args(['[123\.].[ab-g]+'])
	verbose = args.verbose
	regex = Regex(args.regex)
	if not regex.matched:
		print("Failed to parse regular expression!")
		exit(1)

	if verbose:
		print("======== Tree ========")
		print_tree(regex.root)

	reg = re.compile(args.regex)
	tests = int(args.tests) # if args.tests else 10
	quantityMax = int(args.quantity) # if args.quantity is not None else 10
	if tests > 0:
		if verbose:
			print("======== Tests ========")
		for i in range(tests):
			generated = generate_pattern(regex.root, quantityMax)
			if verbose:
				match = reg.match(generated)
				print("Test " + str(i+1) + ':')
				print("  Pattern: " + generated)
				print("  Satisfies regular expression: " + str(match != None and match.group() == generated))
			else:
				print(generated)

# Run the main method if the file is run directly
if __name__ == '__main__':
	main()
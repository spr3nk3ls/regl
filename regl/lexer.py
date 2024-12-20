from itertools import takewhile
from string import whitespace

from regl.aux import comp, const, regions_satisfying, string_regions_replace
from regl.conf import charMap, indentTok, dedentTok, vspaceTok, itemTok, \
		lineEndTok, tokTok, hspaceTok

__all__ = ['Lexer', 'Injector', 'isToken', 'isWhite', 
		'IndentLexer', 'VSpaceLexer', 'ItemLexer', 'LineEndLexer',
		'CharMapLexer', 'PyCommentLexer', 'ReglLexer']

def isToken(line):
	return line.startswith(tokTok)

def isWhite(line):
	return not line.rstrip()

class Lexer:
	def __init__(self, linesrc, ignore=isToken):
		self.linesrc = linesrc
		self.ignore = ignore
	
	def __iter__(self):
		for line in self.linesrc:
			if self.ignore(line):
				yield line
				continue
			for enil in self._lexLine(line):
				yield enil
		for line in self._lexEnd():
			yield line

	def _lexLine(self, line):
		raise NotImplementedError()

	def _lexEnd(self):
		if False: yield 42

class Injector(Lexer):
	def __init__(self, linesrc, ignore=isToken):
		Lexer.__init__(self, linesrc, ignore)
	
	def _lexLine(self, line):
		for token in self._getInjectees(line): yield token
		yield line
	
	def _getInjectees(self, line):
		raise NotImplementedError()

class IndentLexer(Injector):
	def __init__(self, linesrc, ignore=isToken, indent_chars=' \t', 
			indent_token=indentTok, 
			dedent_token=dedentTok,
			ignoreWhiteLines=True):
		Injector.__init__(self, linesrc, ignore)
		self.indent_chars = indent_chars
		self.indent_token = indent_token
		self.dedent_token = dedent_token
		self.ignoreWhiteLines = ignoreWhiteLines
		self.indent_stack = []

	def _getInjectees(self, line):
		depth = 0
		count = 0
		if self.ignoreWhiteLines:
			line = line.rstrip()
		# get remaining indentation
		indent_present = lambda ind: line[depth:].startswith(ind)
		for indent in takewhile(indent_present, self.indent_stack):
			depth += len(indent)
			count += 1
		# return the dedentation
		while len(self.indent_stack) > count:
			self.indent_stack.pop()
			yield self.dedent_token + "\n"
		# find the new indentation
		is_indent_char = lambda c: c in self.indent_chars
		new_indent = ''.join(takewhile(is_indent_char, line[depth:]))
		if not new_indent:
			return
		self.indent_stack.append(new_indent)
		yield "%s %s\n" % (self.indent_token, repr(new_indent))

	def _lexEnd(self):
		while len(self.indent_stack):
			self.indent_stack.pop()
			yield self.dedent_token + "\n"


class VSpaceLexer(Lexer):
	def __init__(self, linesrc, ignore=lambda l: False, 
			token=vspaceTok+"\n"):
		Lexer.__init__(self, linesrc, ignore)
		self.token = token
		self.stash = []

	def _lexLine(self, line):
		if not line.strip():
			self.stash.append(line);  return
		if len(self.stash):  
			yield self.token
			for oldLine in self._emptyStash():  yield oldLine
		yield line

	def _lexEnd(self):
		for line in self._emptyStash():
			yield line
		yield self.token

	def _emptyStash(self):
		for oldLine in self.stash:  yield oldLine
		del self.stash[:]


class ItemLexer(Injector):
	def __init__(self, linesrc, ignore=isToken, itemWords=["-"], 
			token=itemTok+"\n"):
		Injector.__init__(self, linesrc, ignore)
		self.token = token
		self.itemWords = itemWords
	
	def _getInjectees(self, line):
		linestr = line.lstrip()
		if any(map(linestr.startswith, self.itemWords)):
			yield self.token


class LineEndLexer(Lexer):
	def __init__(self, linesrc, ignore=lambda line: isToken(line) \
			or isWhite(line), token=lineEndTok):
		Lexer.__init__(self, linesrc, ignore)
		self.token = token

	def _lexLine(self, line):
		# Not compatible with "\n\r" line endings
		yield line[:-1] + self.token + line[-1]


class CharMapLexer(Lexer):
	def __init__(self, linesrc, charMap, ignore=isToken):
		Lexer.__init__(self, linesrc, ignore)
		self.charMap = charMap
		
	def _lexLine(self, line):
		yield ''.join([self.charMap[c] for c in line])	


class PyCommentLexer(Lexer):
	def __init__(self, linesrc, ignore=isToken):
		Lexer.__init__(self, linesrc, ignore)
	
	def _lexLine(self, line):
		idx = line.find("#")
		yield line[:idx] + "\n" if idx>=0 else line 


def defaultIsHSpace(start, stop, line):
	"""Returns True iff the slice is not at the end or start of the
	line and is either at least 2 characters wide or a tab."""
	if start==0 or stop>=len(line)-1:
		return False
	if stop - start > 1:
		return True
	return line[start]=="\t"


class HSpaceLexer(Lexer):
	def __init__(self, linesrc, ignore=const(False),
			isHSpace=defaultIsHSpace,
			token=hspaceTok):
		Lexer.__init__(self, linesrc, ignore)
		self.isHSpace = isHSpace
		self.token = token

	def _lexLine(self, line):
		isWhitespace = lambda c: c in whitespace
		hsregions = [(start,stop) for start,stop 
				in regions_satisfying(isWhitespace, line)
				if self.isHSpace(start,stop,line)]
		yield string_regions_replace(line, hsregions, 
				const(self.token))

				
def ReglLexer(linesrc):
	return comp(LineEndLexer, #VSpaceLexer,
			IndentLexer, 
			PyCommentLexer, HSpaceLexer, 
			CharMapLexer)(linesrc, charMap)

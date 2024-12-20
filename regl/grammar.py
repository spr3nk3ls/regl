from pyparsing import Suppress, Literal, Word, ZeroOrMore, OneOrMore,  \
		Optional, stringEnd, alphas, Forward, Empty, Group, \
		quotedString

from regl import conf
from regl.aux import chop

indentTok, dedentTok, lineEndTok, hspaceTok, superTok, parTok = \
		list(map(Suppress, [conf.indentTok, conf.dedentTok, 
			conf.lineEndTok, conf.hspaceTok, 
			conf.superTok, conf.parTok]))

escapedChar = (Literal("<") + Word(alphas + "-") + Literal(">"))\
		.setParseAction(lambda t: conf.charMapI[''.join(t)])

def wordParseAction(t):
	word = ''.join(t)
	return escapedChar.transformString(word)
	return word

def specWord(chrs):
	return Word(chrs).setParseAction(wordParseAction)

def specWords(chrs):
	return OneOrMore(specWord(chrs))\
			.setParseAction(lambda t: ' '.join(t))

words = specWords(conf.wordChars)
line = words + lineEndTok
lines = OneOrMore(line).setParseAction(lambda t: ' '.join(t))

class Item:
	def __init__(self, name, content):
		self.name = name
		self.content = content
	
	def __repr__(self):
		return "Item(%s,%s)" % (repr(self.name), repr(self.content))

def createItem(head, body, tail):
	return (head + body + tail)\
			.setParseAction(lambda t: Item(t[0],t[1]))

def createBlock(itemHead, itemBody, itemTail):
	return OneOrMore(createItem(itemHead, itemBody, itemTail))\
			.setParseAction(lambda t: tuple(t[:]))

indent = indentTok + Suppress(quotedString)

descriptionBlock = Forward()
body = descriptionBlock | lines
descriptionBlock << createBlock(line + indent, body, dedentTok)

itemBlock = createBlock(words + hspaceTok, body, Empty())
body = itemBlock | body

parBlock = createBlock(words + parTok + lineEndTok, body, Empty())
body = parBlock | body

superParBlock = createBlock(superTok + words + superTok + lineEndTok, 
		body, Empty())
body = superParBlock | body

sectBlock = createBlock(indent + line + dedentTok, body, Empty())
body = sectBlock | body

superSectBlock = createBlock(indent + superTok + words 
		+ superTok + lineEndTok + dedentTok, body, Empty())
body = superSectBlock | body
regl = body + stringEnd

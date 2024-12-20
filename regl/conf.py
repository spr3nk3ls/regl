from string import whitespace, ascii_letters, digits

from regl.aux import dict_invert

punctuation = "@!,.'\"\\/()-:;*?<>"
tokTok = "^"
indentTok = tokTok + "INDENT"
dedentTok = tokTok + "DEDENT"
vspaceTok = tokTok + "VSPACE"
hspaceTok = "[HSPACE]"
lineEndTok = "$"
itemTok = tokTok + "ITEM"
sectionSignTok = "[section-sign]"
superTok = "~"
parTok = "]"
commentTok = "#"
nilItemToken = '0'
articlePrefixToken = 'Artikel'
NBPrefixToken = 'NB'
specialChars = commentTok + superTok + parTok

wordChars = ascii_letters + digits + punctuation
allowedChars = wordChars + specialChars + whitespace

charNames = (
		("<", "<chevron-open>"),
		(">", "<chevron-close>"),
		("\xe9", "<e-acute>"),
		("\xeb", "<e-umlaut>"),
		("\xf3", "<o-acute>"),
		("\xf6", "<o-umlaut>"),
		("\x81", "<u-umlaut>"),
		("\xa7", sectionSignTok),
		("\u20ac", "<euro-sign>"))

LaTeXCharNames = (
		("<", r"["),
		(">", r"]"),
		("\xe9", r"\'e"),
		("\xeb", r"\"e"),
		("\xf3", r"\'o"),
		("\xf6", r"\"o"),
		("\x81", r"\"u"),
		("\xa7", sectionSignTok),
		("\u20ac", r"\euro"))

def createCharMap(n):
	charMap = {}
	for c in allowedChars:
		charMap[c]=c
	for c,n in n:
		charMap[c]=n
	return charMap
charMap = createCharMap(charNames)  # can decorators do this?
charMapI = dict_invert(charMap)
LaTeXCharMap = createCharMap(LaTeXCharNames)  # can decorators do this?
LaTeXCharMapI = dict_invert(LaTeXCharMap)

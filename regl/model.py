from regl.grammar import Item, regl
from regl.lexer import ReglLexer
from regl import conf
import six
import re

class Node(object):
	def __init__(self, document, children=None):
		self.document = document
		self.children = [] if children is None else children

	def pre_to_html(self, ctx):
		pass

	def pre_to_LaTeX(self, ctx):
		pass

class Document(object):
	def __init__(self):
		self.root = RootNode(self)

	class parseTree_to_document_context:
		def __init__(self, rootList):
			self.document = Document()
			self.stack = [(tuple(rootList),		# i
				       self.document.root,	# p
				       self.section_handler)]	# h

		def main(self):
			while self.stack:
				i, p, h = self.stack.pop()
				h(i, p)
			return self.document

		def children_of(self, i):
			if hasattr(i, 'content'):
				if isinstance(i.content, tuple):
					return i.content
				return (i.content,)
			return ()

		def section_handler(self, i, p):
			assert isinstance(i, tuple)
			for c in i:
				if isinstance(c, six.string_types):
					p.children.append(
						TextNode(self.document, c))
					assert not self.children_of(c)
					continue
				assert isinstance(c, Item)
				handler = self.section_handler
				if c.name == conf.nilItemToken:
					cp = NilItemNode(self.document)
				elif c.name.startswith(
						conf.articlePrefixToken):
					cp = ArticleNode(self.document,
							c.name)
				elif c.name.startswith(
						conf.NBPrefixToken):
					cp = NBNode(self.document, c.name)
				else:
					cp = SectionNode(self.document,
							c.name)
				p.children.append(cp)
				cc = self.children_of(c)
				assert cc
				self.stack.append((cc, cp, handler))
	
	@staticmethod
	def from_parseTree(v):
		return Document.parseTree_to_document_context(v).main()

	@staticmethod
	def from_string(s):
		f = six.StringIO(s)
		return Document.from_parseTree(regl.parseString(
				''.join(ReglLexer(f)))[0])

	def to_html(self):
		return self.to_x(lambda i,*args: i.pre_to_html(*args), 
				lambda i,*args: i.to_html(*args))

	def to_LaTeX(self):
		return self.to_x(lambda i,*args: i.pre_to_LaTeX(*args), 
				lambda i,*args: i.to_LaTeX(*args))
	def to_x(self, pre_call, call):
		stack = [[True, self.root, None, [], dict()]]
		while stack:
			frame = stack[-1]
			#0   1  2   3    4
			pre, i, to, res, ctx = frame
			if pre:
				frame[0] = False
			else:
				stack.pop()
			if pre:
				nctx = pre_call(i,ctx)
				if nctx is None:
					nctx = ctx
				else:
					frame[4] = nctx
				if hasattr(i, 'children'):
					for c in reversed(i.children):
						stack.append([True, c, frame,
							[], nctx])
			else:
				nres = call(i, res, ctx)
				if to is None:
					assert not stack
					return nres
				to[3].append(nres)

class RootNode(Node):
	def to_html(self, children, ctx):
		return ''.join(children)
	def to_LaTeX(self, children, ctx):
		c_text = ''.join(children)
		text = r"""
		\documentclass{article}
		\usepackage[dutch]{babel}
		\usepackage{amsthm}
		\usepackage{eurosym}
		\usepackage{makeidx}

                \date{}
		\makeindex
		\newcommand{\noun}[1]{\textsc{#1}}

		\newcommand{\comment}[1]{
		\begin{enumerate}
		\footnotesize
		\item[//] \emph{#1}
		\end{enumerate}}
		\newcommand{\stub}[1]{\comment{Nog te herschrijven.}}
		\newcommand{\stref}[1]{ST#1}
		\newcommand{\defn}[1]{\textbf{#1}\index{#1}}

		\newtheoremstyle{comment}%%
			{3pt}       %% Space Above
			{3pt}       %% Space below
			{\footnotesize\hangindent=\parindent}    %% Body font
			{\parindent}          %% Indent amount 1
			{\bfseries} %% Theorem head font
			{.}         %% Punctuation after theorem head
			{.5em}      %% Space after theorem head
			{}          %% Theorem head space


		\begin{document}

		%s

		\maketitle
		
		\printindex

		\end{document} """ % c_text
		for c, r in six.iteritems(conf.LaTeXCharMap):
		    text = text.replace(c, r)
		return text


class TextNode(Node):
	def __init__(self, document, text):
		super(TextNode, self).__init__(document)
		self.text = text
		self.re_keyword = re.compile(r'\*((?:\w\s?)*)\*')
		self.re_quote = re.compile(r'"([^"]*)"')
	
	def to_html(self, children, ctx):
		assert not children
		return "<p>%s</p>" % self.text

	def to_LaTeX(self, children, ctx):
		assert not children
		text = self.re_keyword.sub(r'\\defn{\1}', self.text)
		text = self.re_quote.sub(r"``\1''", text)
		return text

class NilItemNode(Node):
	def to_html(self, children, ctx):
		return ''.join(children)

	def to_LaTeX(self, children, ctx):
		return ''.join(children)

class SectionNode(Node):
	def __init__(self, document, title):
		super(SectionNode, self).__init__(document)
		self.title = title
	
	def pre_to_html(self, ctx):
		ctx = dict(ctx)
		if not 'section-depth' in ctx:
			ctx['section-depth'] = 0
		ctx['section-depth'] += 1
		return ctx

	pre_to_LaTeX = pre_to_html

	def to_html(self, children, ctx):
		c_text = '' if children is None else ''.join(children)
		return """ <h%s>%s</h%s>
			   <div class='section section%s'>%s</div> """ % (
			ctx['section-depth'], self.title,
			ctx['section-depth'],
			ctx['section-depth'], c_text)
	
	def to_LaTeX(self, children, ctx):
		depth = ctx['section-depth']
		if children is None:
			children = ()
		if depth == 1:
			templ = r"""\title{%s}
				     \maketitle
				     %s"""
			c_text = ''.join(children)
		elif depth == 2:
			templ = r"""\section*{%s}
				     %s """
			c_text = ''.join(children)
		elif depth == 3:
			templ = r"""\subsection*{%s}
				     %s """
			c_text = ''.join(children)
		elif depth == 4:
			templ = r"""\begin{enumerate}
				    \item[%s] %s 
		  		    \end{enumerate} """
			c_text = ''.join(children)
		elif depth == 5:
			templ = r"""\begin{enumerate}
				    \item[%s] %s 
		  		    \end{enumerate} """
			c_text = ''.join(children)
		elif depth == 6:
			templ = r"""\begin{enumerate}
				    \item[%s] %s 
		  		    \end{enumerate} """
			c_text = ''.join(children)
		else:
			templ = r"wur %s %s"
			c_text = ''.join(children)
		if self.title == '-':
			return c_text
		return templ % (self.title, c_text)

class ArticleNode(SectionNode):
	def pre_to_html(self, ctx):
		pass

	def to_html(self, children, ctx):
		c_text = '' if children is None else ''.join(children)
		return """ <div class="articleTitle">%s</div>
			   <div class='article'>%s</div> """ % (
				self.title, c_text)

	def to_LaTeX(self, children, ctx):
		c_text = '' if children is None else ''.join(children)
		title = self.title
		return r"""
			\theoremstyle{definition}
				\newtheorem*{%(title)s}{%(title)s}
			\begin{%(title)s}
			   %(text)s
			   \end{%(title)s} """ % {"title": title,
			   			  "text": c_text}

class NBNode(SectionNode):
	def pre_to_html(self, ctx):
		pass

	def to_html(self, children, ctx):
		c_text = '' if children is None else ''.join(children)
		return """ <div class="NBTitle">%s</div>
			   <div class='NB'>%s</div> """ % (
				self.title, c_text)

	def to_LaTeX(self, children, ctx):
		c_text = '' if children is None else ''.join(children)
		title = self.title
		return r"""
			\theoremstyle{comment}
				\newtheorem*{%(title)s}{%(title)s}
			\begin{%(title)s}
			   %(text)s
			   \end{%(title)s} """ % {"title": title,
			   			  "text": c_text}

if __name__ == '__main__':
	import codecs
	with codecs.open('test.regl', 'r', 'utf-8') as f:
		doc = Document.from_parseTree(regl.parseString(
				''.join(ReglLexer(f)))[0])
		with codecs.open('test.tex', 'w', 'utf-8') as f2:
			f2.write(doc.to_LaTeX())

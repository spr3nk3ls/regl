# Tree iteration module
#
# A finite tree whose nodes childs are totally ordered from, say, 
# left to right, can be iterated depth-first, see Wikipedia.
# 	To be able to reconstruct the tree-structure after iteration,
# one may pass either the current depth or the change in depth from 
# the previous node (called step) during iteration.
# E.g. Python uses indentation to indicate a blocks depth, while C uses
# the delimiters "{" and "}" to indicate a change in depth.
# 	The functions depth2step and step2depth translate between those
# two representations.

def depth2step(it, bot=0, le=lambda x,y: x<=y):
	return depth2step_Ctx(it, bot, le).main()

class depth2step_Ctx:
	def __init__(self, it, bot, le):
		self.it = it; self.le = le; self.bot = bot
		self.stack = [bot]
	
	def main(self):
		for depth in self.it:
			yield self.getStep(depth)
	
	def getStep(self, depth):
		if self.stack[-1] == depth:
			return 0
		if self.le(self.stack[-1], depth):
			self.stack.append(depth)
			return 1
		d = 0
		while not self.le(self.stack[-1], depth):
			self.stack.pop()
			d -= 1
		if self.stack[-1] == depth:
			return d
		raise UpDownError()


def step2depth(it):
	depth = 0
	for step in it:
		depth += step
		yield depth


class UpDownError(Exception):
	pass


if __name__=="__main__":
	print("Testing module treeit")
	d = (1, 2, 3, 2, 2, 3, 1, 0)
	s = (1, 1, 1, -1, 0, 1, -2, -1)
	assert tuple(depth2step(d)) == s
	assert tuple(step2depth(s)) == d

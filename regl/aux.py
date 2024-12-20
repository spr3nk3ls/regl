import six
import functools

id = lambda x: x 

def const(x):
	return lambda *args, **kwargs: x

def comp2(f,g):
	return lambda *args, **kwargs: f(g(*args, **kwargs))

def comp(*funcs):
	return compit(funcs)

def compit(it):
	return functools.reduce(comp2, it, id)

def dict_invert(d):
	return dict([(v,k) for (k,v) in six.iteritems(d)])

def regions_satisfying(pred, lst):
	"""Returns the minimal amount of pairs (x_i,y_i) such that
	pred(x) iff x in lst[x_i:y_i] for some i."""
	epred = lambda i: (False if i in [-1,len(lst)] else pred(lst[i]))
	switches = [i for i in range(0,len(lst)+1) if epred(i-1)^epred(i)]
	assert len(switches) % 2 == 0
	it = iter(switches)
	for start in it:
		stop = six.next(it)
		yield (start,stop)

def string_regions_replace(str, regions, replacement):
	p = (0,)+functools.reduce(lambda x,y: x+y, regions, ())+(len(str),)
	return ''.join([str[p[i]:p[i+1]] if i%2==0 
		else replacement(p[i],p[i+1]) 
		for i in range(len(p)-1)])

def chop(str, size=30):
	return str if len(str) < size else str[0:size] + "..."

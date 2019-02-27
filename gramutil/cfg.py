import re, sys
from collections import defaultdict
from math import log, ceil
from queue import Queue

EPS = 'ε'
UNDERFLOW = 'Δ'
START = 'Start'
END = 'End'
HUB = 'B'
PUSH = 'PUSH'
POP = 'POP'
NONTERMINAL = re.compile(r'[A-Z][_A-Za-z0-9]*')
TERMINAL = re.compile(r'[Δε_a-z0-9]*')


# Raises an error at a specific line
def error(message: str, line: int):
	raise Exception(f'{message} (line {line})')


class StateCounter:
	"""
	A class for easily generating a next state
	"""
	def __init__(self, n: int = 0):
		self.idx = n - 1
		self.invalid = [self.stateIndex(s.lower()) for s in [START, END]]

	def get(self):
		self.idx += 1
		while self.idx in self.invalid:
			self.idx += 1
		return self.stateName(self.idx)

	def invalidate(self, s: str):
		self.invalid.append(self.stateIndex(s.lower()))

	def stateName(self, n: int):
		if n == 0:
			return 'A'
		res = []
		while n:
			res.append(chr(ord('a') + (n % 26)))
			n //= 26
		return ''.join(res[::-1]).capitalize()

	def stateIndex(self, s: str):
		res, val = 0, 1
		for c in s[::-1]:
			res += val * (ord(c) - ord('a'))
			val *= 26
		return res


class ContextFreeGrammar:
	"""
	A class representing a context free grammar.
	When created, the grammar must be productions
	separated by newlines. Start state must be 'S'.
	States (nonterminals) must be uppercase characters followed by
	a normal variable regex, while a terminals is an all lowercase variable regex.
	Be sure to space-separate terminals and non-terminals.
	"""
	def __init__(self, grammar: str = None):
		self.productions = defaultdict(list)
		self.terminals = set()
		if grammar == None: return

		name = ''
		for idx, line in enumerate(grammar.split('\n')):
			line = line.strip().replace('$', 'ε')
			if not line or line.startswith('#'): continue
			if '->' not in line:
				error(f'Not a valid production: "{line}"', idx + 1)
			if line.startswith('->'):
				line = name + line
			name, rest = line.split('->')
			prods = rest.split('|')
			for prod in prods:
				self.production(name.strip(), prod.split(), idx + 1)

	def production(self, name: str, prod: list, line: int = 0):
		if not NONTERMINAL.fullmatch(name):
			error(f'Invalid production state name: "{name}"', line + 1)
		for term in prod:
			if TERMINAL.fullmatch(term):
				self.terminals.add(term)
			elif not NONTERMINAL.fullmatch(term):
				error(f'Invalid production item: "{term}"', line + 1)

		self.productions[name].append(Production(prod))

	def simplify(self):
		# Merge the start state - it will always be S -> AB
		self.productions[START + END] = self.productions['AB']
		del self.productions['AB']

		# Main simplification - delete epsilons and single terminals
		remove = {'start'}
		replace = {'start'}
		while len(remove) or len(replace):
			remove.clear()
			replace.clear()

			self.removeDuplicates()
			for name, prodlist in self.productions.items():
				if len(prodlist) == 1 and prodlist[0].empty():
					remove.add(name)
				elif len(prodlist) == 1 and prodlist[0].terminal():
					replace.add(name)
			for name, prodlist in self.productions.items():
				for prod in prodlist:
					idx = 0
					while idx < len(prod.terms):
						term = prod.terms[idx]
						if term in remove:
							del prod.terms[idx]
						elif term in replace:
							prod.terms[idx] = self.productions[term][0].terms[0]
							idx += 1
						else:
							idx += 1
					prod.verify()
			for name in remove | replace:
				del self.productions[name]

		# Secondary simplification - Clean up state names
		counter = StateCounter()
		counter.invalidate('S')
		mapping = {}
		mapping[START + END] = 'S'
		for name in self.productions:
			if name not in mapping:
				mapping[name] = counter.get()
		for name, newName in mapping.items():
			self.productions[newName] = self.productions[name]
			del self.productions[name]
			for prod in self.productions[newName]:
				prod.rename(mapping)

	def removeDuplicates(self):
		for name, prodlist in self.productions.items():
			found = set()
			res = []
			for prod in prodlist:
				sprod = str(prod)
				if sprod not in found and sprod != name:
					found.add(sprod)
					res.append(prod)
			self.productions[name] = sorted(res)

	# Name Copyright: Carlos Santana
	def chomskify(self):
		nullable = set()
		for name, prodlist in self.productions.items():
			for prod in prodlist:
				if prod.empty():
					nullable.add(name)

	def toPDA(self):
		return PushdownAutomata(self)

	def __repr__(self):
		nameWidth = max([len(name) for name in self.productions])
		res = []
		for name, prodlist in self.productions.items():
			res.append(f'{name:<{nameWidth}} -> {" | ".join([str(p) for p in prodlist])}')
		return '\n'.join(res)


class Production:
	"""
	A class representing a production in a ContextFreeGrammar.
	Contains the state (nonterminal) name and the rule.
	"""
	def __init__(self, terms: list):
		self.terms = []
		for term in terms:
			if term == UNDERFLOW:
				term = EPS
			if term != EPS:
				self.terms.append(term)
		self.verify()

	def verify(self):
		if len(self.terms) == 0:
			self.terms = [EPS]

	def empty(self):
		return self.terms == [EPS]

	def terminal(self):
		return len(self.terms) == 1 and TERMINAL.fullmatch(self.terms[0])

	def rename(self, mapping: map):
		for i, term in enumerate(self.terms):
			if term in mapping:
				self.terms[i] = mapping[term]

	def __lt__(self, other):
		return str(self) < str(other)

	def __repr__(self):
		return ' '.join(self.terms)


class PushdownAutomata:
	"""
	A class representing a pushdown automata. Generates a graph-like
	structure with transitions as pushes and pops.
	"""
	def __init__(self, grammar: ContextFreeGrammar):
		self.stackSymbols = defaultdict(lambda: defaultdict(list))
		self.names = StateCounter(2)
		self.states = defaultdict(list)
		self.stateNames = set()

		self.transition(START, 'A', EPS, PUSH, UNDERFLOW)
		self.transition('A', HUB, EPS, PUSH, 'S')
		for c in grammar.terminals:
			self.transition(HUB, HUB, c, POP, c)
		self.transition(HUB, END, UNDERFLOW, POP, UNDERFLOW)

		for name, prodlist in grammar.productions.items():
			for prod in prodlist:
				terminal = bool(TERMINAL.fullmatch(prod.terms[0]))

				cur = HUB
				next = HUB if len(prod.terms) == 1 else self.names.get()
				if not terminal:
					self.transition(cur, next, EPS, POP, name)
				else:
					self.transition(cur, next, prod.terms[0], POP, name)
				rest = prod.terms[int(terminal):][::-1]
				for i, term in enumerate(rest):
					if term == EPS: continue
					cur = next
					next = HUB if i == len(rest) - 1 else self.names.get()
					self.transition(cur, next, EPS, PUSH, term)

	def transition(self, cur, next, read, action, value):
		self.stackSymbols[value][action].append([cur, next, read])
		self.states[cur].append(Transition(next, read, action, value))
		self.stateNames.update([cur, next])

	def pathHelper(self, x, y):
		if x == y: return True
		vis = set()
		bfs = Queue()
		bfs.put(x)
		while bfs.qsize():
			cur = bfs.get()
			for trans in self.states[cur]:
				if trans.next in vis: continue
				if trans.next == y:
					return True
				vis.add(trans.next)
				bfs.put(trans.next)
		return False

	def pathExists(self, x, y, z):
		return self.pathHelper(x, y) and self.pathHelper(y, z)

	def toCFG(self):
		cfg = ContextFreeGrammar()
		main = set()

		for sym, value in self.stackSymbols.items():
			for push in value[PUSH]:
				for pop in value[POP]:
					first = f'{push[0]}{pop[1]}'
					second = f'{push[1]}{pop[0]}'
					main.update([first, second])
					cfg.production(first, [push[2], second, pop[2]])

		for x in self.stateNames:
			for y in self.stateNames:
				for z in self.stateNames:
					path, begin, end = x + z, x + y, y + z
					if self.pathExists(x, y, z) and all([x in main for x in [path, begin, end]]):
						if x == z:
							cfg.production(path, [])
						elif x != y and y != z:
							cfg.production(path, [begin, end])

		return cfg

	def __repr__(self):
		nameWidth = max([len(name) for name in self.states])
		return '\n'.join([f'{k:<{nameWidth}} -> {v}' for k, v in self.states.items()])


class Transition:
	"""
	A class representing a transition in a pushdown automata.
	Contains next state, read character, push/pop action, and value to push/pop.
	"""
	def __init__(self, next, read, action, value):
		self.next = next
		self.read = read
		self.action = action
		self.value = value

	def __repr__(self):
		return f'{{{self.next}, {self.read}, {self.action} {self.value}}}'


if __name__ == '__main__':
	if len(sys.argv) > 1:
		with open(sys.argv[1], 'r') as file:
			cfg = ContextFreeGrammar(file.read())
	else:
		cfg = ContextFreeGrammar(sys.stdin.read())
	print('<Grammar>')
	print(cfg, end='\n\n')

	pda = cfg.toPDA()
	print('<Pushdown Automata>')
	print(pda, end='\n\n')

	cfg = pda.toCFG()
	print('<New Grammar>')
	print(cfg, end='\n\n')

	cfg.simplify()
	print('<Simplified Grammar>')
	print(cfg)
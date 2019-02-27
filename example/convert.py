from gramutil.cfg import ContextFreeGrammar, PushdownAutomata

grammarString = """
S -> 0 S 0
  -> T
T -> 1 T 1
  -> 0
  -> $
"""

grammar = ContextFreeGrammar(grammarString)
print('<CFG>')
print(grammar, end='\n\n')

pda = grammar.toPDA()
print('<PDA>')
print(pda, end='\n\n')

grammar = pda.toCFG()
print('<Converted CFG>')
print(grammar, end='\n\n')

grammar.simplify()
print('<Simplified CFG>')
print(grammar, end='\n\n')
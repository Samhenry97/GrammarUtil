# gramutil

GramUtil is a utility for grammars in computer science. Currently, context-free grammars (CFG) and pushdown automatas (PDA) are supported.

## Installation

```
pip install gramutil
```

## Overview

### ContextFreeGrammar

This class provides initialization and methods for a context free grammar. Common operations are demonstrated below:

```python
from gramutil import cfg

grammarString = """
S -> 0 S 0 | T
T -> 1 T 1
  -> $
"""

# Create the grammar from the string
grammar = cfg.ContextFreeGrammar(grammarString)

# Simplify the grammar (simplifies using basic rules)
grammar.simplify()

# Removes any duplicate productions from any state
grammar.removeDuplicates()

# Converts the grammar to a pushdown automata object
pda = grammar.toPDA()

# Prints a textual representation of the grammar
print(grammar)
```

The rules for a grammar string are as follows:
* Start state must be `S`
* Multiple productions for one state may be separated by the `|` character
* Multiple productions for one state may also be on multiple lines, as shown above
* The epsilon (empty string) character is signified with a `$`
* Terminals may be an underscore or lowercase alphanumeric
* Nonterminals have the same rules, but must start with an uppercase character and allow uppercase throughout
* All terms (terminals and nonterminals) must be space-separated

### PushdownAutomata

This class provides initialization and method for a pushdown automata. Currently, creation is only supported from a `ContextFreeGrammar`.

```python
from gramutil import cfg

grammar = cfg.ContextFreeGrammar('S -> 0 S 0 | $')

# Two options for creating the PDA
pda = cfg.PushdownAutomata(grammar)
pda = grammar.toPDA()

# Prints a textual representation of the PDA
print(pda)

# Converts the PDA back to a CFG
grammar = pda.toCFG()
grammar.simplify()
print(grammar)
```

## Examples

Check out `examples/convert.py` for an example use
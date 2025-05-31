"""
Use this file to implement your solution. You can use the `main.py` file to test your implementation.
"""
from helpers import tree_to_string, read_inputs,get_all_subtrees, is_nt
from itertools import product
import re
import random
from collections import defaultdict
from fuzzingbook.Parser import EarleyParser
from fuzzingbook.GrammarFuzzer import GrammarFuzzer

def instantiate_with_nonterminals(constraint_pattern: str, nonterminals: list[str]) -> set[str]:
    instantiated_constraints =set()
    for nonterminal_one in nonterminals:
        for nonterminal_two in nonterminals:
            instantiated_constraint=constraint_pattern.replace("{}",nonterminal_one,1)
            instantiated_constraint=instantiated_constraint.replace("{}",nonterminal_two,1)
            instantiated_constraints.add(instantiated_constraint)
    #print(instantiated_constraints)
    return instantiated_constraints

def instantiate_with_subtrees(abstract_constraint: str, nts_to_subtrees: dict) -> set[str]:
    instantiated_constraints =set()
    nonterminals = re.findall(r'<(.*?)>', abstract_constraint)
    subtrees_list=[nts_to_subtrees.get(f"<{nt}>",[])for nt in nonterminals]
    subtree_combinations=[[]]
    for subtrees_l in subtrees_list:
        new_combinations=[]
        for subtree in subtrees_l:
            for combination in subtree_combinations:
                new_combinations.append(combination+[subtree])
        subtree_combinations=new_combinations
    for combination in subtree_combinations:
        instantiated_constraint=abstract_constraint
        for nonterminal,subtree in zip(nonterminals,combination):
            instantiated_constraint=instantiated_constraint.replace(f"<{nonterminal}>", tree_to_string(subtree))
        instantiated_constraints.add(instantiated_constraint)
    return instantiated_constraints

def check(abstract_constraints: set[str], derivation_tree) -> bool:
    # Perform necessary preprocessing
    subtrees_by_nt = get_all_subtrees(derivation_tree)
    
    # Evaluate each abstract constraint
    for constraint in abstract_constraints:
        # Collect subtrees for each non-terminal
        tree_with_terminals = defaultdict(set)
        for nt, subtrees in subtrees_by_nt.items():
            tree_with_terminals[nt].add((tree_to_string(subtrees[0]), ""))

        # Instantiate concrete constraints and evaluate
        try:
            instantiated_constraints = instantiate_with_subtrees(constraint, tree_with_terminals)
            if not eval(list(instantiated_constraints)[0]):
                return False
        except Exception as e:
            print("Error evaluating constraint:", e)
            return False
    return True

def learn(constraint_patterns: list[str], derivation_trees: list) -> set[str]:
# Function to extract all nonterminals occurring in the derivation trees
    def extract_nonterminals(tree):
        nonterminals=set()     
        if isinstance(tree,tuple):
            nonterminals_with_symbol=tree[0]
            if nonterminals_with_symbol.startswith('<') and nonterminals_with_symbol.endswith('>'):
                nonterminals.add(nonterminals_with_symbol)
            #print("Nonterminals:",nonterminals)
            for subtree in tree[1]:
                nonterminals.update(extract_nonterminals(subtree))
        return nonterminals

    def check_constraints(concrete_constraint,tree):
        try:
            result=eval(concrete_constraint)
            return result
        except Exception as e:
            return False

    all_nonterminals=set()
    for tree in derivation_trees:
        all_nonterminals.update(extract_nonterminals(tree))

    abstract_constraints=set()
    for pattern in constraint_patterns:
        abstract_constraints.update(instantiate_with_nonterminals(pattern,all_nonterminals))

    valid_constraints=set()
    for constraint in abstract_constraints:
        satisfied =True
        for tree in derivation_trees:
            concrete_constraints= instantiate_with_subtrees(constraint,get_all_subtrees(tree))
            for concrete_constraint in concrete_constraints:
                if not check_constraints(concrete_constraint,tree):
                    satisfied =False
                    break
            if not satisfied:
                break
        if satisfied:
            valid_constraints.add(constraint)
    return valid_constraints

def generate(abstract_constraints: set[str], grammar: dict, produce_valid_sample: True) -> str:
    fuzzed_input=GrammarFuzzer(grammar).fuzz()
    parser=EarleyParser(grammar)
    parse_trees=parser.parse(fuzzed_input)
    parse_tree=next(parse_trees,None)
    if parse_tree is None:
        return generate(abstract_constraints,grammar,produce_valid_sample)
    satisfied=check(abstract_constraints,parse_tree)
    if produce_valid_sample and satisfied:
        return fuzzed_input
    elif not produce_valid_sample and not satisfied:
        return fuzzed_input
    else:
        return generate(abstract_constraints,grammar,produce_valid_sample)
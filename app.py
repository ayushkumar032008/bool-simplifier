import streamlit as st
import re
from itertools import product


def count_ones(binary_str):
    return binary_str.count('1')

def diff_by_one_bit(term1, term2):
    diff_count = 0
    res = []
    for c1, c2 in zip(term1, term2):
        if c1 == c2:
            res.append(c1)
        else:
            diff_count += 1
            res.append('-')
    if diff_count == 1:
        return True, "".join(res)
    return False, None

def get_prime_implicants(minterms, num_vars):
    if not minterms:
        return []
    
    current_terms = {format(m, f'0{num_vars}b'): {m} for m in minterms}
    prime_implicants = set()
    
    while current_terms:
        next_terms = {}
        used = set()
        keys = list(current_terms.keys())
        n = len(keys)
        
        for i in range(n):
            for j in range(i + 1, n):
                match, combined = diff_by_one_bit(keys[i], keys[j])
                if match:
                    used.add(keys[i])
                    used.add(keys[j])
                    combined_minterms = current_terms[keys[i]].union(current_terms[keys[j]])
                    next_terms[combined] = combined_minterms
                    
        for term in keys:
            if term not in used:
                prime_implicants.add((term, frozenset(current_terms[term])))
                
        current_terms = next_terms

    return prime_implicants

def get_essential_prime_implicants(prime_implicants, minterms):
    if not minterms:
        return "0"
    
    for term, covered in prime_implicants:
        if term == '-' * len(term):
            return "1"

    chart = {m: [] for m in minterms}
    for term, covered in prime_implicants:
        for m in covered:
            if m in chart:
                chart[m].append(term)
                
    selected = set()
    uncovered_minterms = set(minterms)
    
    for m, terms in chart.items():
        if len(terms) == 1:
            term = terms[0]
            selected.add(term)
            uncovered_minterms.difference_update({k for k, v in chart.items() if term in v})
            
    while uncovered_minterms:
        best_term = None
        max_cover = 0
        for term, covered in prime_implicants:
            cover_count = len(uncovered_minterms.intersection(covered))
            if cover_count > max_cover:
                max_cover = cover_count
                best_term = term
        if best_term:
            selected.add(best_term)
            uncovered_minterms.difference_update({k for k, v in chart.items() if best_term in v})
        else:
            break
            
    return selected

def term_to_expression(term, var_names):
    literals = []
    for bit, var in zip(term, var_names):
        if bit == '1':
            literals.append(var)
        elif bit == '0':
            literals.append(f"{var}'")
    return "".join(literals)


def clean_expression(expr):
    expr = expr.upper()
    
    # XNOR conversion: (A XNOR B) -> not (A ^ B)
    pattern_xnor = r'(\b\w+\b)\s+XNOR\s+(\b\w+\b)'
    while re.search(pattern_xnor, expr):
        expr = re.sub(pattern_xnor, r'(not (\1 ^ \2))', expr)
        
    expr = re.sub(r'\bXOR\b', '^', expr)
    expr = re.sub(r'\bAND\b', ' and ', expr)
    expr = re.sub(r'\bOR\b', ' or ', expr)
    expr = re.sub(r'\bNOT\b', ' not ', expr)
    return expr

def find_minterms(user_expr, var_names):
    py_expr = clean_expression(user_expr)
    num_vars = len(var_names)
    minterms = []
    
    for values in product([0, 1], repeat=num_vars):
        env = dict(zip(var_names, values))
        try:
            val = eval(py_expr, {}, env)
            if bool(val):
                minterm_val = sum(bit * (2 ** (num_vars - 1 - idx)) for idx, bit in enumerate(values))
                minterms.append(minterm_val)
        except Exception as e:
            raise ValueError(f"Error evaluating expression: {e}")
            
    return minterms


st.title("Boolean Simplifier")
st.write("Enter variables and a logic expression to get the simplified SOP form.")

variables_input = st.text_input("Variables (comma-separated, in order):", "A, B, C")
expr_input = st.text_input("Boolean Expression:", "A AND B OR (NOT A AND C) XOR B")

st.caption("Supported operators: AND, OR, NOT, XOR, XNOR and parentheses ().")

if st.button("Simplify"):
    var_list = [v.strip().upper() for v in variables_input.split(",") if v.strip()]
    
    if not var_list:
        st.error("Please enter at least one variable.")
    elif not expr_input.strip():
        st.error("Please enter an expression.")
    else:
        try:
            minterms = find_minterms(expr_input, var_list)
            
            st.subheader("Simplified Expression:")
            
            if not minterms:
                st.latex("0")
            elif len(minterms) == 2 ** len(var_list):
                st.latex("1")
            else:
                prime_implicants = get_prime_implicants(minterms, len(var_list))
                selected_terms = get_essential_prime_implicants(prime_implicants, minterms)
                
                sop_terms = [term_to_expression(t, var_list) for t in sorted(selected_terms)]
                simplified_expr = " + ".join(sop_terms) if sop_terms else "0"
                
                st.latex(simplified_expr)
                
        except Exception as err:
            st.error(f"Invalid input: {err}")
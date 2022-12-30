import math
import operator as op


# Types

Symbol = str
Number = (int, float)
Atom   = (Symbol, Number)
List   = list
Exp    = (Atom, List)
Env    = dict



# Environment

class Env(dict):
    def __init__(self, parms=(), args=(), outer=None):
        self.update(zip(parms, args))
        self.outer = outer

    def find(self, var):
        env = self.find_env(var)
        return env[var] if env else None

    def find_env(self, var):
        if (var in self):
            return self
        else:
            if self.outer == None:
                return None
            return self.outer.find_env(var)


def setup_env():
    env = Env()
    env.update(vars(math))
    # Add any builtins to include here
    env.update({
        "+": op.add,
        "-": op.sub,
        "*": op.mul,
        "/": op.truediv,
        "%": op.mod,
        ">": op.gt,
        ">=": op.ge,
        "<": op.lt,
        "<=": op.le,
        "=": op.eq,
        "eq?": op.eq,
        "begin": lambda *x: x[-1],
    })
    return env



global_env = setup_env()


# Parsing = Lexical Analysis + Syntactic Analysis

# Tokenization 
def tokenize(code: str) -> list:
    return code.replace("(", "( ").replace(")", " )").split()

def parse(code: str) -> Exp:
    tokenized_list = tokenize(code)
    # print(f"tokenized_list : {tokenized_list} \n")
    return build_tree_from_tokens(tokenized_list)

# tokens to AST
def build_tree_from_tokens(tokenized_list: list) -> Exp:

    if len(tokenized_list) == 0:
        raise SyntaxError("Unexpected EOF")
    
    stack = []
    
    for token in tokenized_list:
        
        if token == "(":
            stack.append("(")
        elif token == ")":

            new_token_list = []

            while True:
                top = None
                if stack:
                    top = stack.pop()
                else:
                    raise SyntaxError("Syntax Error")
                if top == "(":
                    stack.append(new_token_list[::-1])
                    break
                else:
                    new_token_list.append(top)
        else:
            stack.append(atom(token))

    if len(stack) != 1:
        raise SyntaxError("Syntax Error")
            
    return stack[0]

def atom(token: str) -> Atom:
    try: 
        return int(token)
    except ValueError:
        try: 
            return float(token)
        except ValueError:
            return Symbol(token)



# Type Checks


def is_number(exp):
    return type(exp) in Number

def is_symbol(exp):
    return type(exp)==Symbol
    
def is_conditional(exp):
    return type(exp)==List and exp[0]=="if"

def is_definition(exp):
    return type(exp)==List and exp[0]=="define"

def is_application(exp, env):
    return type(exp)==List

def is_lambda(exp, env):
    return type(exp)==List and exp[0]=="lambda"

def is_set(exp, env):
    return type(exp)==List and exp[0]=="set!"


# number

def eval_number(exp):
    return exp

# symbol

def eval_symbol(exp, env):
    val = env.find(exp)
    if val:
        return eval_symbol(val, env)
    return exp

# condition

def get_if_cond(exp: Exp) -> Exp:
    return exp[1]
def get_if_consequence(exp: Exp) -> Exp:
    return exp[2]
def get_if_alternative(exp: Exp) -> Exp:
    return exp[3]

def eval_condition(exp, env):
    cond = get_if_cond(exp)
    consequence = get_if_consequence(exp)
    alternative = get_if_alternative(exp)
    return eval(consequence, env) if eval(cond, env) else eval(alternative, env)

# definition

def get_operator(exp):
    return exp[0]

def get_operands(exp):
    return exp[1:]

def eval_definition(exp, env):
    (_, symbol, rem) = exp

    if is_symbol(symbol):
        env[symbol] = eval(rem, env)
    else:
        proc_name = symbol[0]
        params = symbol[1:]
        env[proc_name] = Procedure(params, rem, env)

# procedure


class Procedure:
    def __init__(self, params, body, env):
        self.params = params
        self.body = body
        self.env = env
    def __call__(self, *args):
        return eval(self.body, Env(self.params, args, self.env))


def eval_procedure(exp: Exp, env) -> Procedure:
    (_, params, body) = exp
    return Procedure(params, body, env)

# set!

def eval_set(exp: Exp, env) -> Procedure:
    (_, symbol, body) = exp
    env.find_env(symbol)[symbol] = eval(body, env)


# apply

def apply(exp: Exp, env: Env):

    # print(f"apply exp {exp} env {env}")

    proc = eval(get_operator(exp), env)

    args = get_operands(exp)

    eval_args = [eval(arg, env) for arg in args]

    return proc(*eval_args)
    
# eval

def eval(exp, env=global_env) -> Exp:

    if is_number(exp):
        return eval_number(exp)
    elif is_symbol(exp):
        return eval_symbol(exp, env)
    elif is_conditional(exp):
        return eval_condition(exp, env)
    elif is_definition(exp):
        return eval_definition(exp, env)
    elif is_set(exp, env):
        return eval_set(exp, env)
    elif is_lambda(exp, env):
        return eval_procedure(exp, env)
    elif is_application(exp, env):
        return apply(exp, env)
    else:
        raise SyntaxError("Unexpected Format")


def run(code):
    val = eval(parse(code))
    if val is not None:
        print(schemestr(val))

def schemestr(exp):
    if isinstance(exp, List):
        return '(' + ' '.join(map(schemestr, exp)) + ')' 
    else:
        return str(exp)

def repl(prompt='> '):
    while True:
        code = input(prompt)
        if len(code) == 0:
            continue
        elif code=="exit()":
            return

        exp = parse(code)
        # print(f"ast: {exp}")
        val = eval(exp)
        if val is not None:
            print(schemestr(val))

def try_eval(code):
    val = eval(parse(code))
    print(f"> {code}")
    if val is not None:
        print(schemestr(val))


def main():
    import sys
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        code = open(filename).read()
        run(code)
    else:
        repl()

if __name__ == "__main__":
    main()

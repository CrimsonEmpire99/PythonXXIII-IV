cmd_lines = []
variables = {}
python_keywords = ["False", "None", "True", "and", "as", "assert", "async", "await", "break","class", "continue", "def", "del", "elif", "else", "except", "finally","for", "from", "global", "if", "import", "in", "is", "lambda", "nonlocal","not", "or", "pass", "raise", "return", "try", "while", "with", "yield"]
aug_ops = ['+=', '-=', '*=', '/=', '%=']

def collection_elements(collection):
    elements = []
    select = ''
    depth = 0
    in_quote = False
    quote_ch = ''

    for ch in collection:
        if ch == '"' or ch == "'":
            if not in_quote:
                in_quote = True
                quote_ch = ch
            elif quote_ch == ch:
                in_quote = False
            select += ch
        elif ch == '[' and not in_quote:
            depth += 1
            select += ch
        elif ch == ']' and not in_quote:
            depth -= 1
            select += ch
        elif ch == ',' and depth == 0 and not in_quote:
            elements.append(select.strip())
            select = ''
        else:
            select += ch
    if select !='':
        elements.append(select.strip())

    return elements

def find_keyword(expression, keyword):
    in_quote = False
    quote_ch = ''
    for i in range(len(expression) - len(keyword) + 1):
        ch = expression[i]
        if ch in ("'", '"'):
            if not in_quote:
                in_quote = True
                quote_ch = ch
            elif quote_ch == ch:
                in_quote = False
        if not in_quote and expression[i:i+len(keyword)] == keyword:
            return i
    return -1

def evaluate_expr_string(expr_str, variables):
    expr = expr_str.strip()

    previous = None
    while expr != previous:  # loop until expression stops changing
        previous = expr

        # 1. Arithmetic
        if expr.find('"') == -1 and expr.find("'") == -1 and expr.find('[') == -1 and expr.find('{') == -1:
            if '+' in expr or '-' in expr or '*' in expr or '/' in expr or '%' in expr:
                expr_dict = {'expr': expr}
                arithmetic_expression(expr_dict, 'expr', variables)
                expr = str(expr_dict['expr'])

        # 2. Relational
        for op in ['==', '!=', '<=', '>=', '<', '>']:
            if op in expr:
                expr_dict = {'expr': expr}
                relational_expression(expr_dict, 'expr', variables)
                expr = str(expr_dict['expr'])
                break  # re-loop to catch multiple or mixed operators

        # 3. Logical
        if (' is not ' in expr or ' not in ' in expr or ' is ' in expr or ' in ' in expr or ' not ' in expr or ' and ' in expr or ' or ' in expr):
            expr_dict = {'expr': expr}
            logical_expression(expr_dict, 'expr', variables)
            expr = str(expr_dict['expr'])

    return data_conversion(expr, variables)

def get_indentation(line):
    """Return number of leading spaces (indentation level)."""
    return len(line) - len(line.lstrip(" "))


def collect_block(lines, start_index, base_indent):
    """Collects all lines indented beyond base_indent as part of a block."""
    block = []
    i = start_index
    while i < len(lines):
        line = lines[i]
        if not line.strip():  # skip blank lines
            i += 1
            continue
        indent = get_indentation(line)
        if indent <= base_indent:  # stop when indentation returns to base
            break
        block.append(line)
        i += 1
    return block, i

def data_conversion(data, variables):
    if isinstance(data, (int, float, bool, list, tuple, set, dict, range)):
        return data
    data = str(data).strip()

    if data in variables:
        return variables[data]
    
    # Handle range() function
    if data.startswith('range(') and data.endswith(')'):
        return handle_range(data, variables)
    
    # Handle input() function
    if data.startswith('input(') and data.endswith(')'):
        return handle_input_function(data, variables)
    
    # I. Implicit Data Conversion:-
    if (data.startswith("'") and data.endswith("'")) or (data.startswith('"') and data.endswith('"')):
        data = data[1:-1]
    elif data.isdigit() or (data.startswith("-") and data[1:].isdigit()):
        data = int(data)
    elif (data.startswith('-') and data[1:].count('.')==1 and data[1:].replace('.','').isdigit()) or (not data.startswith('-') and data.count('.')==1 and data.replace('.','').isdigit()):
        data = float(data)
    elif data.startswith('[') and data.endswith(']'):
        inner = data[1:-1].strip()
        if inner == "":
            data = []
        else:
            elements = collection_elements(inner)
            new_elements = []
            for part in elements:
                part_value = evaluate_expr_string(part, variables)
                new_elements.append(part_value)
            data = new_elements
    elif data.startswith('(') and data.endswith(')'):
        inner = data[1:-1].strip()
        if inner == "":
            data = ()
        else:
            elements = collection_elements(inner)
            new_elements = []
            for part in elements:
                part_value = evaluate_expr_string(part, variables)
                new_elements.append(part_value)
            data = tuple(new_elements)
    elif data.startswith('{') and data.endswith('}'):
        inner = data[1:-1].strip()
        if inner == "":
            data = {}  
        elif ':' in inner:
            data = {}
            elements = collection_elements(inner)
            for element in elements:
                key,_,val = element.partition(':')
                key = data_conversion(key.strip(), variables)
                val = evaluate_expr_string(val.strip(), variables)
                data[key] = val
        else:
            elements = collection_elements(inner)
            new_elements = []
            for part in elements:
                part_value = evaluate_expr_string(part, variables)
                new_elements.append(part_value)
            data = set(new_elements) 

    # 7. Keywords:
    if data == "True":
        data = True
    elif data == "False":
        data = False
    elif data == "None":
        data = None

    # II. Explicit Data Conversion:-
    if isinstance(data, str): 
        if data.startswith("int(") and data.endswith(")"):
            inner = data[4:-1].strip()
            data = int(data_conversion(inner, variables))
        elif data.startswith("float(") and data.endswith(")"):
            inner = data[6:-1].strip()
            data = float(data_conversion(inner, variables))
        elif data.startswith("str(") and data.endswith(")"):
            inner = data[4:-1].strip()
            data = str(data_conversion(inner, variables))
        elif data.startswith("list(") and data.endswith(")"):
            inner = data[5:-1].strip()
            data = list(data_conversion(inner, variables))
        elif data.startswith("tuple(") and data.endswith(")"):
            inner = data[6:-1].strip()
            data = tuple(data_conversion(inner, variables))
        elif data.startswith("set(") and data.endswith(")"):
            inner = data[4:-1].strip()
            data = set(data_conversion(inner, variables))    
        elif data.startswith("dict(") and data.endswith(")"):
            inner = data[5:-1].strip()
            data = dict(data_conversion(inner, variables))
        elif data.startswith("bool(") and data.endswith(")"):
            inner = data[5:-1].strip()
            data = bool(data_conversion(inner, variables))

    return data

def arithmetic_expression(expr_dict, key, variables):
    expr = expr_dict[key].strip()

    # 1. Parentheses "()":
    while '(' in expr:
        start = expr.rfind('(')
        end = expr.find(')', start)
        inner = expr[start+1:end]
        # Using evaluate_expr_string to handle nested expressions correctly
        evaluated_inner = evaluate_expr_string(inner, variables)
        expr = expr[:start] + str(evaluated_inner) + expr[end+1:]

    # 2. Exponentiation "**"
    if '**' in expr:
        parts = expr.split('**')
        # Evaluate each part of the exponentiation
        evaluated_parts = [evaluate_expr_string(p, variables) for p in parts]
        result = float(evaluated_parts[-1])
        for i in range(len(evaluated_parts)-2, -1, -1):
            result = float(evaluated_parts[i]) ** result
        expr_dict[key] = result
        return

    # 3. Multiplication, division, modulus
    for op in ['*', '/', '%']:
        while op in expr:
            # A simplified way to handle this is needed as the current logic is complex
            # For now, we will assume simple cases
            try:
                idx = expr.find(op)
                left_start = idx - 1
                while left_start >= 0 and (expr[left_start].isalnum() or expr[left_start] in '._-'):
                    left_start -= 1
                left_start += 1
                left = expr[left_start:idx].strip()

                right_end = idx + 1
                while right_end < len(expr) and (expr[right_end].isalnum() or expr[right_end] in '._-'):
                    right_end += 1
                right = expr[idx + 1:right_end].strip()

                left_val = data_conversion(left, variables)
                right_val = data_conversion(right, variables)

                if op == '*': res = left_val * right_val
                elif op == '/': res = left_val / right_val
                elif op == '%': res = left_val % right_val
                expr = expr[:left_start] + str(res) + expr[right_end:]
            except (ValueError, TypeError):
                break # Break if conversion fails, means expression is more complex

    # 4. Addition and subtraction
    expr = expr.replace('+-','-').replace('--','+')
    if expr.startswith('+'):
        expr = expr[1:]

    total = 0
    num = ''
    last_op = '+'
    i = 0
    # Handle leading negative sign
    if expr.startswith('-'):
        last_op = '-'
        expr = expr[1:]

    for ch in expr:
        if ch in '+-':
            if num:
                val = data_conversion(num, variables)
                total = total + val if last_op == '+' else total - val
                num = ''
            last_op = ch
        else:
            num += ch
    
    if num:
        val = data_conversion(num, variables)
        total = total + val if last_op == '+' else total - val
        
    expr_dict[key] = total

def relational_expression(expr_dict, key, variables):
    expr = expr_dict[key]
    Relational_Operators = ['==', '!=', '<=', '>=', '<', '>']
    found = ''
    pos = -1

    for select in Relational_Operators:
        pos = find_keyword(expr, select)
        if pos != -1:
            found = select
            break

    lside, _, rside = expr.partition(found)
    lside = lside.strip()
    rside = rside.strip()

    l = evaluate_expr_string(lside, variables)
    r = evaluate_expr_string(rside, variables)

    if found == '==': result = l == r
    elif found == '!=': result = l != r
    elif found == '<': result = l < r
    elif found == '>': result = l > r
    elif found == '<=': result = l <= r
    elif found == '>=': result = l >= r
    else: result = expr

    expr_dict[key] = result

def logical_expression(expr_dict, key, variables):
    expr = expr_dict[key].strip()

    # 1. not
    pos = find_keyword(expr, 'not ')
    while pos != -1:
        before = expr[:pos]
        after = expr[pos+4:].strip()
        part = after.split(' ', 1)
        target = part[0]
        rest = part[1] if len(part) > 1 else ''
        result = not data_conversion(target, variables)
        expr = (before + str(result) + ' ' + rest).strip()
        pos = find_keyword(expr, 'not ')

    # 2. 'is' and 'is not'
    pos = find_keyword(expr, ' is not ')
    if pos != -1:
        lside, _, rside = expr.partition(' is not ')
        l = data_conversion(lside.strip(), variables)
        r = data_conversion(rside.strip(), variables)
        expr = str(l is not r)
    else:
        pos = find_keyword(expr, ' is ')
        if pos != -1:
            lside, _, rside = expr.partition(' is ')
            l = data_conversion(lside.strip(), variables)
            r = data_conversion(rside.strip(), variables)
            expr = str(l is r)

    # 3. 'in' and 'not in'
    pos = find_keyword(expr, ' not in ')
    if pos != -1:
        lside, _, rside = expr.partition(' not in ')
        l = data_conversion(lside.strip(), variables)
        r = data_conversion(rside.strip(), variables)
        expr = str(l not in r)
    else:
        pos = find_keyword(expr, ' in ')
        if pos != -1:
            lside, _, rside = expr.partition(' in ')
            l = data_conversion(lside.strip(), variables)
            r = data_conversion(rside.strip(), variables)
            expr = str(l in r)

    # 4. and
    pos = find_keyword(expr, ' and ')
    if pos != -1:
        parts = expr.split(' and ')
        final_val = True
        for part in parts:
            val = data_conversion(part.strip(), variables)
            if not val:
                final_val = False
                break
        expr = str(final_val)

    # 5. or
    pos = find_keyword(expr, ' or ')
    if pos != -1:
        parts = expr.split(' or ')
        final_val = False
        for part in parts:
            val = data_conversion(part.strip(), variables)
            if val:
                final_val = True
                break
        expr = str(final_val)

    expr_dict[key] = data_conversion(expr, variables)

def assignment(line, variables, python_keywords):
    aug_ops = ['+=', '-=', '*=', '/=', '%=']
    augment = False

    # Arithmetic augmented assignment:
    for op in aug_ops:
        if op in line:
            lhs, _, rhs = line.partition(op)
            lhs = lhs.strip()
            rhs_expr = rhs.strip()

            if not (lhs.isidentifier() and lhs not in python_keywords):
                print("Invalid variable name:", lhs)
            elif lhs not in variables:
                print(f"Variable {lhs} not defined for {op}")
            else:
                rhs_val = evaluate_expr_string(rhs_expr, variables)
                if op == '+=':
                    variables[lhs] += rhs_val
                elif op == '-=':
                    variables[lhs] -= rhs_val
                elif op == '*=':
                    variables[lhs] *= rhs_val
                elif op == '/=':
                    variables[lhs] /= rhs_val
                elif op == '%=':
                    variables[lhs] %= rhs_val
            augment = True
            break  

    # Normal assignment '=':
    if not augment and '=' in line and '==' not in line:
        lhs, _, rhs = line.partition('=')
        lhs = lhs.strip()
        rhs_expr = rhs.strip()

        if not (lhs.isidentifier() and lhs not in python_keywords):
            print("Invalid variable name:", lhs)
        else:
            variables[lhs] = evaluate_expr_string(rhs_expr, variables)


def execute_line(line, lines, index, variables, python_keywords):
    """Execute a single line - handles all statement types."""
    stripped = line.strip()
    
    # Check for control structures first
    if stripped.startswith('if '):
        return conditional_statement(lines, index, variables, python_keywords)
    elif stripped.startswith('while '):
        return while_loop(lines, index, variables, python_keywords)
    elif stripped.startswith('for '):
        return for_loop(lines, index, variables, python_keywords)
    elif stripped.startswith('print('):
        print_statement(line, variables)
        return index + 1
    else:
        # Regular assignment
        assignment(line, variables, python_keywords)
        return index + 1

def conditional_statement(lines, start_index, variables, python_keywords):
    """
    Process if/elif/else statements recursively.
    Supports nesting and multiple branches.
    Returns the index to resume execution from.
    """
    i = start_index
    base_indent = get_indentation(lines[i])
    executed_block = False  # whether one branch has already executed

    while i < len(lines):
        stripped = lines[i].strip()

        # --- IF ---
        if stripped.startswith('if '):
            condition = stripped[3:].rstrip(':').strip()
            condition_value = evaluate_expr_string(condition, variables)
            block, next_i = collect_block(lines, i + 1, base_indent)

            if condition_value and not executed_block:
                j = 0
                block_index = i + 1
                while j < len(block):
                    subline = block[j]
                    next_block_index = execute_line(subline, lines, block_index, variables, python_keywords)
                    j += (next_block_index - block_index)
                    block_index = next_block_index
                executed_block = True

            i = next_i
            continue

        # --- ELIF ---
        elif stripped.startswith('elif '):
            condition = stripped[5:].rstrip(':').strip()
            condition_value = evaluate_expr_string(condition, variables)
            block, next_i = collect_block(lines, i + 1, base_indent)

            if condition_value and not executed_block:
                j = 0
                block_index = i + 1
                while j < len(block):
                    subline = block[j]
                    next_block_index = execute_line(subline, lines, block_index, variables, python_keywords)
                    j += (next_block_index - block_index)
                    block_index = next_block_index
                executed_block = True

            i = next_i
            continue

        # --- ELSE ---
        elif stripped.startswith('else:'):
            block, next_i = collect_block(lines, i + 1, base_indent)

            if not executed_block:
                j = 0
                block_index = i + 1
                while j < len(block):
                    subline = block[j]
                    next_block_index = execute_line(subline, lines, block_index, variables, python_keywords)
                    j += (next_block_index - block_index)
                    block_index = next_block_index
                executed_block = True

            i = next_i
            continue

        else:
            break  # chain finished

    return i

def while_loop(lines, start_index, variables, python_keywords):
    """
    Process while loops.
    Returns the index to resume execution from.
    """
    i = start_index
    stripped = lines[i].strip()
    base_indent = get_indentation(lines[i])
    
    # Extract condition
    condition = stripped[6:].rstrip(':').strip()
    
    # Collect the loop block
    block, next_i = collect_block(lines, i + 1, base_indent)
    
    # Execute while loop
    while evaluate_expr_string(condition, variables):
        j = 0
        block_index = i + 1
        while j < len(block):
            subline = block[j]
            next_block_index = execute_line(subline, lines, block_index, variables, python_keywords)
            j += (next_block_index - block_index)
            block_index = next_block_index
    
    return next_i

def for_loop(lines, start_index, variables, python_keywords):
    """
    Process for loops.
    Returns the index to resume execution from.
    """
    i = start_index
    stripped = lines[i].strip()
    base_indent = get_indentation(lines[i])
    
    # Extract loop variable and iterable
    # Format: for var in iterable:
    loop_def = stripped[4:].rstrip(':').strip()
    
    # Split by ' in '
    parts = loop_def.split(' in ', 1)
    if len(parts) != 2:
        print("Invalid for loop syntax")
        block, next_i = collect_block(lines, i + 1, base_indent)
        return next_i
    
    loop_var = parts[0].strip()
    iterable_expr = parts[1].strip()
    
    # Evaluate the iterable
    iterable = evaluate_expr_string(iterable_expr, variables)
    
    # Collect the loop block
    block, next_i = collect_block(lines, i + 1, base_indent)
    
    # Execute for loop
    for value in iterable:
        variables[loop_var] = value
        j = 0
        block_index = i + 1
        while j < len(block):
            subline = block[j]
            next_block_index = execute_line(subline, lines, block_index, variables, python_keywords)
            j += (next_block_index - block_index)
            block_index = next_block_index
    
    return next_i

def handle_range(expr, variables):
    """Handle range() function calls."""
    expr = expr.strip()
    
    if not (expr.startswith('range(') and expr.endswith(')')):
        return None
    
    # Extract arguments
    args_str = expr[6:-1].strip()
    
    if not args_str:
        return range(0)
    
    # Split arguments
    args = []
    current_arg = ''
    depth = 0
    
    for ch in args_str:
        if ch == ',' and depth == 0:
            args.append(current_arg.strip())
            current_arg = ''
        else:
            if ch in '([{':
                depth += 1
            elif ch in ')]}':
                depth -= 1
            current_arg += ch
    
    if current_arg:
        args.append(current_arg.strip())
    
    # Evaluate arguments
    evaluated_args = []
    for arg in args:
        evaluated_args.append(int(evaluate_expr_string(arg, variables)))
    
    # Create range based on number of arguments
    if len(evaluated_args) == 1:
        return range(evaluated_args[0])
    elif len(evaluated_args) == 2:
        return range(evaluated_args[0], evaluated_args[1])
    elif len(evaluated_args) == 3:
        return range(evaluated_args[0], evaluated_args[1], evaluated_args[2])
    
    return range(0)

def print_statement(line, variables):
    """Handle print() statements."""
    stripped = line.strip()
    
    if not (stripped.startswith('print(') and stripped.endswith(')')):
        return
    
    # Extract what's inside print()
    content = stripped[6:-1].strip()
    
    if not content:
        print()
        return
    
    # Split by commas (respecting quotes and brackets)
    items = []
    current = ''
    depth = 0
    in_quote = False
    quote_ch = ''
    
    for ch in content:
        if ch in ('"', "'") and (not in_quote or quote_ch == ch):
            if not in_quote:
                in_quote = True
                quote_ch = ch
            elif quote_ch == ch:
                in_quote = False
            current += ch
        elif ch in '([{' and not in_quote:
            depth += 1
            current += ch
        elif ch in ')]}' and not in_quote:
            depth -= 1
            current += ch
        elif ch == ',' and depth == 0 and not in_quote:
            items.append(current.strip())
            current = ''
        else:
            current += ch
    
    if current:
        items.append(current.strip())
    
    # Evaluate and print each item
    output = []
    for item in items:
        value = evaluate_expr_string(item, variables)
        output.append(str(value))
    
    print(' '.join(output))

def handle_input_function(expr, variables):
    """Handle input() function calls and return the user input."""
    expr = expr.strip()
    
    if not (expr.startswith('input(') and expr.endswith(')')):
        return None
    
    # Extract the prompt message
    prompt_str = expr[6:-1].strip()
    
    if not prompt_str:
        # No prompt provided
        user_input = input()
    else:
        # Evaluate the prompt (it might be a variable or expression)
        prompt = evaluate_expr_string(prompt_str, variables)
        user_input = input(str(prompt))
    
    return user_input

#=======================================================================================================

while True:
    inp = input('')
    cmd_lines.append(inp)
    if inp.endswith('/run'):
        # Remove the /run command from the lines to execute
        cmd_lines = cmd_lines[:-1]
        
        # Process all lines, handling conditionals, loops, and print
        i = 0
        while i < len(cmd_lines):
            line = cmd_lines[i]
            if line.strip():
                i = execute_line(line, cmd_lines, i, variables, python_keywords)
            else:
                i += 1
        
        break
    
#=======================================================================================================

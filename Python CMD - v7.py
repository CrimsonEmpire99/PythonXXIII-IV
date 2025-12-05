cmd_lines = []
variables = {}
python_keywords = ["False", "None", "True", "and", "as", "assert", "async", "await", "break","class", "continue", "def", "del", "elif", "else", "except", "finally","for", "from", "global", "if", "import", "in", "is", "lambda", "nonlocal","not", "or", "pass", "raise", "return", "try", "while", "with", "yield"]
aug_ops = ['+=', '-=', '*=', '/=', '%=']

def remove_comment(line):
    """Removes comments starting with #, unless inside quotes."""
    in_quote = False
    quote_ch = ''
    for i, ch in enumerate(line):
        if ch in ('"', "'"):
            if not in_quote:
                in_quote = True
                quote_ch = ch
            elif quote_ch == ch:
                in_quote = False
        elif ch == '#' and not in_quote:
            return line[:i]
    return line

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
    while expr != previous:
        previous = expr
        
        # 1. Logical
        found_logical = False
        for kw in [' is not ', ' not in ', ' is ', ' in ', ' not ', ' and ', ' or ']:
            if find_keyword(expr, kw) != -1:
                found_logical = True
                break
        
        if found_logical:
            expr_dict = {'expr': expr}
            logical_expression(expr_dict, 'expr', variables)
            expr = str(expr_dict['expr'])
            continue

        # 2. Relational
        found_relational = False
        for op in ['==', '!=', '<=', '>=', '<', '>']:
            if find_keyword(expr, op) != -1:
                found_relational = True
                break
                
        if found_relational:
            expr_dict = {'expr': expr}
            relational_expression(expr_dict, 'expr', variables)
            expr = str(expr_dict['expr'])
            continue

        # 3. Arithmetic
        if expr.find('"') == -1 and expr.find("'") == -1 and expr.find('[') == -1 and expr.find('{') == -1:
            if '+' in expr or '-' in expr or '*' in expr or '/' in expr or '%' in expr:
                expr_dict = {'expr': expr}
                arithmetic_expression(expr_dict, 'expr', variables)
                expr = str(expr_dict['expr'])

    return data_conversion(expr, variables)

def get_indentation(line):
    return len(line) - len(line.lstrip(" "))

def collect_block(lines, start_index, base_indent):
    block = []
    i = start_index
    while i < len(lines):
        line = lines[i]
        # Skip empty lines inside blocks
        if not line.strip():
            i += 1
            continue
        indent = get_indentation(line)
        if indent <= base_indent:
            break
        block.append(line)
        i += 1
    return block, i

def data_conversion(data, variables):
    if isinstance(data, (int, float, bool, list, tuple, set, dict, range)):
        return data
    data = str(data).strip()
    
    # Check functions first
    if data.startswith('range(') and data.endswith(')'):
        return handle_range(data, variables)
    if data.startswith('input(') and data.endswith(')'):
        return handle_input_function(data, variables)
    
    # Strings
    if (data.startswith("'") and data.endswith("'")) or (data.startswith('"') and data.endswith('"')):
        val = data[1:-1]
        val = val.replace('\\n', '\n').replace('\\t', '\t')
        return val

    # Numbers
    if data.isdigit() or (data.startswith("-") and data[1:].isdigit()):
        return int(data)
    elif (data.startswith('-') and data[1:].count('.')==1 and data[1:].replace('.','').isdigit()) or (not data.startswith('-') and data.count('.')==1 and data.replace('.','').isdigit()):
        return float(data)
    
    # Collections
    elif data.startswith('[') and data.endswith(']'):
        inner = data[1:-1].strip()
        if inner == "":
            data = []
        else:
            elements = collection_elements(inner)
            new_elements = []
            for part in elements:
                new_elements.append(evaluate_expr_string(part, variables))
            data = new_elements
        return data
    elif data.startswith('(') and data.endswith(')'):
        inner = data[1:-1].strip()
        if inner == "":
            data = ()
        else:
            elements = collection_elements(inner)
            new_elements = []
            for part in elements:
                new_elements.append(evaluate_expr_string(part, variables))
            data = tuple(new_elements)
        return data
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
                new_elements.append(evaluate_expr_string(part, variables))
            data = set(new_elements) 
        return data

    # Keywords
    if data == "True": return True
    elif data == "False": return False
    elif data == "None": return None
    
    # Check Variable
    if isinstance(data, str) and data in variables:
        return variables[data]

    # Explicit Data Conversion
    if isinstance(data, str): 
        if data.startswith("int(") and data.endswith(")"):
            inner = data[4:-1].strip()
            return int(data_conversion(inner, variables))
        elif data.startswith("float(") and data.endswith(")"):
            inner = data[6:-1].strip()
            return float(data_conversion(inner, variables))
        elif data.startswith("str(") and data.endswith(")"):
            inner = data[4:-1].strip()
            return str(data_conversion(inner, variables))
        elif data.startswith("list(") and data.endswith(")"):
            inner = data[5:-1].strip()
            return list(data_conversion(inner, variables))
        elif data.startswith("tuple(") and data.endswith(")"):
            inner = data[6:-1].strip()
            return tuple(data_conversion(inner, variables))
        elif data.startswith("set(") and data.endswith(")"):
            inner = data[4:-1].strip()
            return set(data_conversion(inner, variables))    
        elif data.startswith("dict(") and data.endswith(")"):
            inner = data[5:-1].strip()
            return dict(data_conversion(inner, variables))
        elif data.startswith("bool(") and data.endswith(")"):
            inner = data[5:-1].strip()
            return bool(data_conversion(inner, variables))
        elif data.isidentifier() and data not in python_keywords:
            print(f"NameError: name '{data}' is not defined")
            return 0

    return data

def arithmetic_expression(expr_dict, key, variables):
    expr = expr_dict[key].strip()

    # 1. Parentheses
    while '(' in expr:
        start = expr.rfind('(')
        end = expr.find(')', start)
        inner = expr[start+1:end]
        evaluated_inner = evaluate_expr_string(inner, variables)
        expr = expr[:start] + str(evaluated_inner) + expr[end+1:]

    # 2. Exponentiation
    if '**' in expr:
        parts = expr.split('**')
        evaluated_parts = [evaluate_expr_string(p, variables) for p in parts]
        result = float(evaluated_parts[-1])
        for i in range(len(evaluated_parts)-2, -1, -1):
            result = float(evaluated_parts[i]) ** result
        expr_dict[key] = result
        return

    # 3. Mul/Div/Mod
    for op in ['*', '/', '%']:
        while op in expr:
            try:
                idx = expr.find(op)
                
                # Scan LEFT (ignore spaces)
                i = idx - 1
                while i >= 0 and expr[i] == ' ': i -= 1
                end_left = i + 1
                while i >= 0 and (expr[i].isalnum() or expr[i] in '._-'): i -= 1
                start_left = i + 1
                left_str = expr[start_left:end_left]

                # Scan RIGHT (ignore spaces)
                i = idx + 1
                while i < len(expr) and expr[i] == ' ': i += 1
                start_right = i
                while i < len(expr) and (expr[i].isalnum() or expr[i] in '._-'): i += 1
                end_right = i
                right_str = expr[start_right:end_right]

                left_val = data_conversion(left_str, variables)
                right_val = data_conversion(right_str, variables)

                if op == '*': res = left_val * right_val
                elif op == '/': res = left_val / right_val
                elif op == '%': res = left_val % right_val
                
                expr = expr[:start_left] + str(res) + expr[end_right:]
            except (ValueError, TypeError, ZeroDivisionError):
                break 

    # 4. Add/Sub
    expr = expr.replace('+-','-').replace('--','+')
    if expr.startswith('+'): expr = expr[1:]

    total = 0
    num = ''
    last_op = '+'
    if expr.startswith('-'):
        last_op = '-'
        expr = expr[1:]

    for ch in expr:
        if ch in '+-':
            if num:
                val = data_conversion(num, variables)
                if not isinstance(val, (int, float)):
                    try: val = float(val) if '.' in str(val) else int(val)
                    except: pass
                total = total + val if last_op == '+' else total - val
                num = ''
            last_op = ch
        else:
            num += ch
    
    if num:
        val = data_conversion(num, variables)
        if not isinstance(val, (int, float)):
            try: val = float(val) if '.' in str(val) else int(val)
            except: pass
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

    if pos == -1: return 

    lside = expr[:pos].strip()
    rside = expr[pos+len(found):].strip()

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

    # 2. 'is' / 'is not'
    pos = find_keyword(expr, ' is not ')
    if pos != -1:
        lside = expr[:pos]
        rside = expr[pos+8:]
        l = data_conversion(lside.strip(), variables)
        r = data_conversion(rside.strip(), variables)
        expr = str(l is not r)
    else:
        pos = find_keyword(expr, ' is ')
        if pos != -1:
            lside = expr[:pos]
            rside = expr[pos+4:]
            l = data_conversion(lside.strip(), variables)
            r = data_conversion(rside.strip(), variables)
            expr = str(l is r)

    # 3. 'in' / 'not in'
    pos = find_keyword(expr, ' not in ')
    if pos != -1:
        lside = expr[:pos]
        rside = expr[pos+8:]
        l = data_conversion(lside.strip(), variables)
        r = data_conversion(rside.strip(), variables)
        expr = str(l not in r)
    else:
        pos = find_keyword(expr, ' in ')
        if pos != -1:
            lside = expr[:pos]
            rside = expr[pos+4:]
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
                if op == '+=': variables[lhs] += rhs_val
                elif op == '-=': variables[lhs] -= rhs_val
                elif op == '*=': variables[lhs] *= rhs_val
                elif op == '/=': variables[lhs] /= rhs_val
                elif op == '%=': variables[lhs] %= rhs_val
            augment = True
            break  

    if not augment and '=' in line:
        if find_keyword(line, '=') != -1: 
             pos = find_keyword(line, '=')
             lhs = line[:pos].strip()
             rhs_expr = line[pos+1:].strip()
             
             if not (lhs.isidentifier() and lhs not in python_keywords):
                print("Invalid variable name:", lhs)
             else:
                variables[lhs] = evaluate_expr_string(rhs_expr, variables)

def execute_line(line, lines, index, variables, python_keywords):
    # Remove comments first
    line_no_comment = remove_comment(line)
    stripped = line_no_comment.strip()
    
    # Ignore empty lines (or lines that were just comments)
    if not stripped:
        return index + 1
    
    if stripped.startswith('if '):
        return conditional_statement(lines, index, variables, python_keywords)
    elif stripped.startswith('while '):
        return while_loop(lines, index, variables, python_keywords)
    elif stripped.startswith('for '):
        return for_loop(lines, index, variables, python_keywords)
    elif stripped.startswith('print('):
        print_statement(line_no_comment, variables)
        return index + 1
    else:
        assignment(line_no_comment, variables, python_keywords)
        return index + 1

def conditional_statement(lines, start_index, variables, python_keywords):
    i = start_index
    base_indent = get_indentation(lines[i])
    executed_block = False

    while i < len(lines):
        line_clean = remove_comment(lines[i])
        stripped = line_clean.strip()
        indent = get_indentation(lines[i])

        # If it's empty/comment only, skip it but stay in loop
        if not stripped:
            i += 1
            continue

        if i > start_index and indent <= base_indent and not (stripped.startswith('elif') or stripped.startswith('else')):
             break

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
                    skip = next_block_index - block_index
                    j += skip
                    block_index = next_block_index
                executed_block = True
            i = next_i
            continue

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
                    skip = next_block_index - block_index
                    j += skip
                    block_index = next_block_index
                executed_block = True
            i = next_i
            continue

        elif stripped.startswith('else:'):
            block, next_i = collect_block(lines, i + 1, base_indent)
            if not executed_block:
                j = 0
                block_index = i + 1
                while j < len(block):
                    subline = block[j]
                    next_block_index = execute_line(subline, lines, block_index, variables, python_keywords)
                    skip = next_block_index - block_index
                    j += skip
                    block_index = next_block_index
                executed_block = True
            i = next_i
            continue

        else:
            break 

    return i

def while_loop(lines, start_index, variables, python_keywords):
    i = start_index
    stripped = remove_comment(lines[i]).strip()
    base_indent = get_indentation(lines[i])
    condition = stripped[6:].rstrip(':').strip()
    block, next_i = collect_block(lines, i + 1, base_indent)
    
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
    i = start_index
    stripped = remove_comment(lines[i]).strip()
    base_indent = get_indentation(lines[i])
    loop_def = stripped[4:].rstrip(':').strip()
    parts = loop_def.split(' in ', 1)
    if len(parts) != 2:
        block, next_i = collect_block(lines, i + 1, base_indent)
        return next_i
    
    loop_var = parts[0].strip()
    iterable_expr = parts[1].strip()
    iterable = evaluate_expr_string(iterable_expr, variables)
    block, next_i = collect_block(lines, i + 1, base_indent)
    
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
    expr = expr.strip()
    args_str = expr[6:-1].strip()
    if not args_str: return range(0)
    
    args = []
    current_arg = ''
    depth = 0
    for ch in args_str:
        if ch == ',' and depth == 0:
            args.append(current_arg.strip())
            current_arg = ''
        else:
            if ch in '([{': depth += 1
            elif ch in ')]}': depth -= 1
            current_arg += ch
    if current_arg: args.append(current_arg.strip())
    
    evaluated_args = [int(evaluate_expr_string(arg, variables)) for arg in args]
    
    if len(evaluated_args) == 1: return range(evaluated_args[0])
    elif len(evaluated_args) == 2: return range(evaluated_args[0], evaluated_args[1])
    elif len(evaluated_args) == 3: return range(evaluated_args[0], evaluated_args[1], evaluated_args[2])
    return range(0)

def print_statement(line, variables):
    stripped = line.strip()
    content = stripped[6:-1].strip()
    if not content:
        print()
        return
    
    items = []
    current = ''
    depth = 0
    in_quote = False
    quote_ch = ''
    escape_next = False
    
    for ch in content:
        if escape_next:
            current += ch
            escape_next = False
            continue
        if ch == '\\' and in_quote:
            escape_next = True
            current += ch
            continue
        if ch in ('"', "'"):
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
    
    output = []
    for item in items:
        value = evaluate_expr_string(item, variables)
        output.append(str(value))
    print(' '.join(output))

def handle_input_function(expr, variables):
    expr = expr.strip()
    prompt_str = expr[6:-1].strip()
    if not prompt_str:
        user_input = input()
    else:
        prompt = evaluate_expr_string(prompt_str, variables)
        user_input = input(str(prompt))
    return user_input

#=======================================================================================================
while True:
    inp = input('')
    cmd_lines.append(inp)
    if inp.endswith('/run'):
        cmd_lines = cmd_lines[:-1]
        print('Python 3.12.1 (Bedrock Edition) [MSC v.1937 64 bit (AMD64)] on win32')
        print('Type "help", "copyright", "credits" or "license()" for more information.')
        print('>>>')
        print('') 
        
        i = 0
        while i < len(cmd_lines):
            line = cmd_lines[i]
            if line.strip():
                i = execute_line(line, cmd_lines, i, variables, python_keywords)
            else:
                i += 1
        
        cmd_lines = []
        break
#=======================================================================================================

from intbase import InterpreterBase, ErrorType
from bparser import BParser, StringWithLineNumber
import sys


class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(
            console_output, inp
        )  # call InterpreterBase’s constructor
        self.classes_dict = {}

    def interpret_statement(self, statement, line_num):
        print(f"{line_num}: {statement}")

    def run(self, program):
        # parse the program into a more easily processed form
        result, parsed_program = BParser.parse(program)
        if not result:
            return SyntaxError
        self.parsed_program = parsed_program
        self.__discover_all_classes_and_track_them()
        class_def = self.__find_definition_for_class("main")
        obj = class_def.instantiate_object(self.classes_dict, super())
        obj.call_method("main")
        return

    def __discover_all_classes_and_track_them(self):
        for class_def in self.parsed_program:
            if class_def[1] in self.classes_dict:
                super().error(ErrorType(1))
                sys.exit()
            class_dict = {'fields': {}, 'methods': {}}
            for item in class_def:
                if item[0] == super().FIELD_DEF:
                    if item[1] in class_dict['fields']:
                        super().error(ErrorType(2))
                        sys.exit()
                    class_dict['fields'][item[1]] = item[2]
                    # handle a field
                elif item[0] == super().METHOD_DEF:
                    if item[1] in class_dict['methods']:
                        super().error(ErrorType(2))
                        sys.exit()
                    class_dict['methods'][item[1]] = Method(item[2], item[3])
                    # handle a method
            self.classes_dict[class_def[1]] = class_dict

    def __find_definition_for_class(self, c):
        if c not in self.classes_dict:
            super().error(ErrorType(1))
            sys.exit()
        return ClassDefinition(self.classes_dict[c])

    def print_line_nums(parsed_program):
        for item in parsed_program:
            if type(item) is not list:
                print(f'{item} was found on line {item.line_num}')


class ClassDefinition:
    # constructor for a ClassDefinition
    def __init__(self, class_dict):
        self.my_methods = class_dict['methods']
        self.my_fields = class_dict['fields']

    # uses the definition of a class to create and return an instance of it
    def instantiate_object(self, classes_dict, base):
        obj = ObjectDefinition(classes_dict, base)
        for method_name, method in self.my_methods.items():
            obj.add_method(method_name, method)
        for f_name, f_value in self.my_fields.items():
            obj.add_field(str(f_name), f_value)
        return obj


class Method:
    def __init__(self, parameters, top_statement):
        self.parameters = parameters
        self.top_statement = top_statement

    def get_top_level_statement(self):
        return self.top_statement

    def get_parameters(self):
        return self.parameters


class ObjectDefinition:
    def __init__(self, classes_dict, base):
        self.super = base
        self.fields = {}
        self.methods = {}
        self.params = []
        self.classes_dict = classes_dict

    # Interpret the specified method using the provided parameters
    def call_method(self, method_name, parameters=[]):
        method = self.__find_method(method_name)
        params = method.get_parameters()
        if len(params) != len(parameters):
            self.super.error(ErrorType(1))
            sys.exit()
        new_params = {}
        for i in range(len(parameters)):
            new_params[params[i]] = parameters[i]
        self.params.append(new_params)
        statement = method.get_top_level_statement()
        result = self.__run_statement(statement)[0]
        self.params.pop()
        return result

    def add_field(self, f_name, f_value):
        val = self.__convert_string_with_line_number_to_type(f_value)
        self.fields[f_name] = val

    def add_method(self, method_name, method):
        self.methods[method_name] = method

    def __find_method(self, method_name):
        if method_name not in self.methods:
            self.super.error(ErrorType(2))
            sys.exit()
        return self.methods[method_name]

    # runs/interprets the passed-in statement until completion and
    # gets the result, if any
    def __run_statement(self, statement):
        result = None
        returned = False
        if statement[0] == self.super.PRINT_DEF:
            self.__execute_print_statement(statement)
        elif (
            statement[0] == self.super.INPUT_STRING_DEF
            or statement[0] == self.super.INPUT_INT_DEF
        ):
            self.__execute_input_statement(statement)
        elif statement[0] == self.super.SET_DEF:
            self.__execute_set_statement(statement)
        elif statement[0] == self.super.CALL_DEF:
            self.__execute_call_statement(statement)
        elif statement[0] == self.super.WHILE_DEF:
            result, returned = self.__execute_while_statement(statement)
        elif statement[0] == self.super.IF_DEF:
            result, returned = self.__execute_if_statement(statement)
        elif statement[0] == self.super.RETURN_DEF:
            result, returned = self.__execute_return_statement(statement)
        elif statement[0] == self.super.BEGIN_DEF:
            (
                result,
                returned,
            ) = self.__execute_all_sub_statements_of_begin_statement(statement)
        return result, returned

    def __execute_all_sub_statements_of_begin_statement(self, statement):
        for state in statement:
            if state == self.super.BEGIN_DEF:
                continue
            res, returned = self.__run_statement(state)
            if res is not None or returned:
                return res, returned
        return None, None

    def __execute_print_statement(self, statement):
        output = ''
        for term in statement:
            if term == self.super.PRINT_DEF:
                continue
            raw_txt = term
            txt = self.__evaluate_expression(raw_txt)
            if (
                isinstance(txt, str)
                and txt.startswith('"')
                and txt.endswith('"')
            ):
                txt = txt[1:-1]
            elif isinstance(txt, bool):
                if txt:
                    txt = self.super.TRUE_DEF
                else:
                    txt = self.super.FALSE_DEF
            output += str(txt)
        self.super.output(output)

    def __execute_input_statement(self, statement):
        input = self.super.get_input()
        if statement[1] in self.params[-1]:
            self.params[-1][statement[1]] = (
                int(input)
                if statement[0] == self.super.INPUT_INT_DEF
                else str(input)
            )
        elif statement[1] in self.fields:
            self.fields[statement[1]] = (
                int(input)
                if statement[0] == self.super.INPUT_INT_DEF
                else str(input)
            )
        else:
            self.super.error(ErrorType(2))
            sys.exit()

    def __execute_call_statement(self, statement):
        params = [self.__evaluate_expression(param) for param in statement[3:]]
        if statement[1] == self.super.ME_DEF:
            return self.call_method(statement[2], params)
        obj = self.__evaluate_expression(statement[1])
        if type(obj) is Nothing:
            self.super.error(ErrorType(4))
        res = obj.call_method(statement[2], params)
        return res

    def __execute_while_statement(self, statement):
        condition = self.__evaluate_expression(statement[1])
        if type(condition) is not bool:
            self.super.error(ErrorType(1))
            sys.exit()
        while condition:
            res, returned = self.__run_statement(statement[2])
            if res is not None or returned:
                return res, returned
            condition = self.__evaluate_expression(statement[1])
            if type(condition) is not bool:
                self.super.error(ErrorType(1))
                sys.exit()
        return None, None

    def __execute_if_statement(self, statement):
        condition = self.__evaluate_expression(statement[1])
        # print(condition, type(condition), type(condition) is not bool)
        if type(condition) is not bool:
            self.super.error(ErrorType(1))
            sys.exit()
        if condition:
            return self.__run_statement(statement[2])
        elif len(statement) == 4:
            return self.__run_statement(statement[3])
        return None, None

    def __execute_return_statement(self, statement):
        if len(statement) == 2:
            return self.__evaluate_expression(statement[1]), True
        return None, True

    def __execute_set_statement(self, statement):
        val = self.__evaluate_expression(statement[2])
        if statement[1] in self.params[-1]:
            self.params[-1][statement[1]] = val
        elif statement[1] in self.fields:
            self.fields[statement[1]] = val
        else:
            self.super.error(ErrorType(2))
            sys.exit()

    def __convert_string_with_line_number_to_type(self, value):
        if type(value) != StringWithLineNumber:
            return value
        if value.startswith('"'):
            return str(value)
        elif value == self.super.TRUE_DEF:
            return True
        elif value == self.super.FALSE_DEF:
            return False
        elif value == self.super.NULL_DEF:
            return Nothing()
        try:
            return int(value)
        except ValueError:
            if str(value) in self.classes_dict:
                return str(value)
            self.super.error(ErrorType(2))
            sys.exit()

    def __evaluate_expression(self, expression):
        if type(expression) != list:
            expr = expression
            if expression in self.fields:
                expr = self.fields[expression]
            if self.params and expression in self.params[-1]:
                expr = self.params[-1][expression]
            return self.__convert_string_with_line_number_to_type(expr)
        operator = expression[0]
        if operator == self.super.CALL_DEF:
            return self.__execute_call_statement(expression)
        elif operator == self.super.NEW_DEF:
            if expression[1] not in self.classes_dict:
                self.super.error(ErrorType(1))
                sys.exit()
            class_def = ClassDefinition(self.classes_dict[expression[1]])
            obj = class_def.instantiate_object(self.classes_dict, self.super)
            return obj
        op1 = self.__evaluate_expression(expression[1])
        op1 = self.__convert_string_with_line_number_to_type(op1)
        t1 = type(op1)
        if operator == '!':
            if t1 is not bool:
                self.super.error(ErrorType(1))
                sys.exit()
            return not t1
        op2 = self.__evaluate_expression(expression[2])
        op2 = self.__convert_string_with_line_number_to_type(op2)
        t2 = type(op2)
        # print(operator, op1, t1, op2, t2)
        if operator == '+':
            if (
                t1 is not t2
                or not isinstance(op1, int)
                and not isinstance(op1, str)
            ):
                self.super.error(ErrorType(1))
                sys.exit()
            if isinstance(op1, int):
                return op1 + op2
            if op1.endswith('"'):
                op1 = op1[:-1]
            if op2.startswith('"'):
                op2 = op2[1:]
            return op1 + op2
        elif operator == '-':
            if not isinstance(op1, int) or not isinstance(op2, int):
                self.super.error(ErrorType(1))
                sys.exit()
            return op1 - op2
        elif operator == '%':
            if not isinstance(op1, int) or not isinstance(op2, int):
                self.super.error(ErrorType(1))
                sys.exit()
            return op1 % op2
        elif operator == '*':
            if not isinstance(op1, int) or not isinstance(op2, int):
                self.super.error(ErrorType(1))
                sys.exit()
            return op1 * op2
        elif operator == '/':
            if not isinstance(op1, int) or not isinstance(op2, int):
                self.super.error(ErrorType(1))
                sys.exit()
            return op1 // op2
        elif operator == '==':
            if (
                t1 is not t2
                and (t1 is not Nothing or t2 is not ObjectDefinition)
                and (t1 is not ObjectDefinition or t2 is not Nothing)
            ):
                self.super.error(ErrorType(1))
                sys.exit()
            if t1 is Nothing or t2 is Nothing:
                return t1 == t2
            return op1 == op2
        elif operator == '!=':
            if (
                t1 is not t2
                and (t1 is not Nothing or t2 is not ObjectDefinition)
                and (t1 is not ObjectDefinition or t2 is not Nothing)
            ):
                self.super.error(ErrorType(1))
                sys.exit()
            if t1 is Nothing or t2 is Nothing:
                return t1 != t2
            return op1 != op2
        elif operator == '>=':
            if (
                t1 is not t2
                or not isinstance(op1, int)
                and not isinstance(op1, str)
            ):
                self.super.error(ErrorType(1))
                sys.exit()
            return op1 >= op2
        elif operator == '<=':
            if (
                t1 is not t2
                or not isinstance(op1, int)
                and not isinstance(op1, str)
            ):
                self.super.error(ErrorType(1))
                sys.exit()
            return op1 <= op2
        elif operator == '>':
            if (
                t1 is not t2
                or not isinstance(op1, int)
                and not isinstance(op1, str)
            ):
                self.super.error(ErrorType(1))
                sys.exit()
            return op1 > op2
        elif operator == '<':
            if (
                t1 is not t2
                or not isinstance(op1, int)
                and not isinstance(op1, str)
            ):
                self.super.error(ErrorType(1))
                sys.exit()
            return op1 < op2
        elif operator == '&':
            if t1 is not bool or t2 is not bool:
                self.super.error(ErrorType(1))
                sys.exit()
            return op1 and op2
        elif operator == '|':
            if t1 is not bool or t2 is not bool:
                self.super.error(ErrorType(1))
                sys.exit()
            return op1 or op2


class Nothing:
    def __init__(self):
        pass


def main():
    program = """(class main
  (field num 0)
  (field result 1)
  (method main ()
    (begin
      (print "Enter a number: ")
      (inputi num)
      (print num "factorial is " (call me factorial num))))

  (method factorial (n)
    (begin
      (set result 1)
      (while (> n 0)
        (begin
          (set result (* n result))
          (set n (- n 1))))
      (return result))))""".splitlines()

    interpreter = Interpreter()
    interpreter.run(program)


if __name__ == '__main__':
    main()

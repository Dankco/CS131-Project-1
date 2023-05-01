from intbase import InterpreterBase
from bparser import BParser


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
        self.__discover_all_classes_and_track_them(parsed_program)
        class_def = self.__find_definition_for_class("main")
        obj = class_def.instantiate_object()
        result = obj.call_method("main")
        super().output(result)
        return

    def __discover_all_classes_and_track_them(self, parsed_program):
        for class_def in self.parsed_program:
            class_dict = {'fields': {}, 'methods': {}}
            for item in class_def:
                if item[0] == 'field':
                    class_dict['fields'][item[1]] = item[2]
                    # handle a field
                elif item[0] == 'method':
                    class_dict['methods'][item[1]] = Method(item[2], item[3])
                    # handle a method
            self.classes_dict[class_def[1]] = class_dict

    def __find_definition_for_class(self, c):
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
    def instantiate_object(self):
        obj = ObjectDefinition()
        for method_name, method in self.my_methods.items():
            obj.add_method(method_name, method)
        for f_name, f_value in self.my_fields.items():
            obj.add_field(f_name, f_value)
        return obj


class ObjectDefinition:
    def __init__(self):
        self.fields = {}
        self.methods = {}

    # Interpret the specified method using the provided parameters
    def call_method(self, method_name, parameters=None):
        method = self.__find_method(method_name)
        statement = method.get_top_level_statement()
        result = self.__run_statement(statement)
        return result

    def add_field(self, f_name, f_value):
        self.fields[f_name] = f_value

    def add_method(self, method_name, method):
        self.methods[method_name] = method

    def __find_method(self, method_name):
        return self.methods[method_name]

    # runs/interprets the passed-in statement until completion and
    # gets the result, if any
    def __run_statement(self, statement):
        result = ''
        if self.is_a_print_statement(statement):
            result = self.__execute_print_statement(statement)
        elif self.is_a_begin_statement(statement):
            result = self.__execute_all_sub_statements_of_begin_statement(
                statement
            )
        return result
        """ elif is_an_input_statement(statement):
            result = self.__execute_input_statement(statement)
        elif is_a_call_statement(statement):
            result = self.__execute_call_statement(statement)
        elif is_a_while_statement(statement):
            result = self.__execute_while_statement(statement)
        elif is_an_if_statement(statement):
            result = self.__execute_if_statement(statement)
        elif is_a_return_statement(statement):
            result = self.__execute_return_statement(statement) """

    def is_a_print_statement(self, statement):
        return statement[0] == 'print'

    def is_a_begin_statement(self, statement):
        return statement[0] == 'begin'

    def __execute_all_sub_statements_of_begin_statement(self, statement):
        result = ''
        for state in statement[1]:
            result += self.__run_statement(state)
        return result

    def __execute_print_statement(self, statement):
        return statement[1].strip("\"")


class Method:
    def __init__(self, parameters, statements):
        self.parameters = parameters
        self.statements = statements

    def get_top_level_statement(self):
        return self.statements

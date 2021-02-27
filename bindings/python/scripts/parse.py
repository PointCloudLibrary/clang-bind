import clang.cindex as clang

from context import scripts
import scripts.utils as utils
from scripts.clang_utils import ClangUtils


class Parse:
    """
    Class containing functions to generate an AST of a file and parse it to retrieve relevant information.
    """

    def __init__(self, file, compiler_arguments):
        index = clang.Index.create()

        """
        - Why parse using the option `PARSE_DETAILED_PROCESSING_RECORD`?
            - Indicates that the parser should construct a detailed preprocessing record, 
            including all macro definitions and instantiations
            - Required to retrieve `CursorKind.INCLUSION_DIRECTIVE`
        """

        source_ast = index.parse(
            path=file,
            args=compiler_arguments,
            options=clang.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD,
        )

        self.root_node = {
            "cursor": source_ast.cursor,
            "filename": source_ast.spelling,
            "depth": 0,
        }

    @staticmethod
    def is_valid_child(parent_node, child_node):
        child = child_node.get("cursor")
        parent_filename = parent_node.get("filename")

        if child.location.file and child.location.file.name == parent_filename:
            return True
        return False

    @staticmethod
    def get_parsed_node(node):
        cursor = node.get("cursor")

        # Objects to get various kinds of checks available in cindex.py via clang_utils.py
        cursor_kind_utils = ClangUtils(cursor.kind)
        cursor_utils = ClangUtils(cursor)
        cursor_type_utils = ClangUtils(cursor.type)

        parsed_node = {
            "depth": node.get("depth"),
            "line": cursor.location.line,
            "column": cursor.location.column,
            "tokens": [x.spelling for x in cursor.get_tokens()],
            "cursor_kind": {
                **cursor_kind_utils.get_check_functions_dict(),  # Functions that begin with "is_" i.e., checking functions
                **cursor_kind_utils.get_get_functions_dict(),  # Functions that begin with "get_" i.e., getter functions
                **cursor_kind_utils.get_properties_dict(),  # Properties
            },
            "cursor": {
                **cursor_utils.get_check_functions_dict(),
                **cursor_utils.get_get_functions_dict(),
                **cursor_utils.get_properties_dict(),
            },
            "type": {
                **cursor_type_utils.get_check_functions_dict(),
                **cursor_type_utils.get_get_functions_dict(),
                **cursor_type_utils.get_properties_dict(),
            },
            "members": [],
        }

        # HACKY FIXES
        # get spelling from object
        parsed_node["cursor"]["result_type"] = parsed_node["cursor"][
            "result_type"
        ].spelling
        # replace `AccessSpecifier.value` with just `value`
        parsed_node["cursor"]["access_specifier"] = parsed_node["cursor"][
            "access_specifier"
        ].name
        # replace `TypeKind.value` with just `value`
        parsed_node["type"]["kind"] = parsed_node["type"]["kind"].name

        return parsed_node

    @classmethod
    def parse_node_recursive(cls, node):
        """
        Generates parsed information by recursively traversing the AST

        Parameters:
            - node (dict):
                - The node in the AST
                - Keys:
                    - cursor: The cursor pointing to a node
                    - filename:
                        - The file's name to check if the node belongs to it
                        - Needed to ensure that only symbols belonging to the file gets parsed, not the included files' symbols
                    - depth: The depth of the node (root=0)

        Returns:
            - parsed_info (dict):
                - Contains key-value pairs of various traits of a node
                - The key 'members' contains the node's children's `parsed_info`
        """

        cursor = node.get("cursor")
        filename = node.get("filename")
        depth = node.get("depth")

        parsed_info = cls.get_parsed_node(node)

        # Get cursor's children and recursively add their info to a dictionary, as members of the parent
        for child in cursor.get_children():
            child_node = {"cursor": child, "filename": filename, "depth": depth + 1}
            if cls.is_valid_child(node, child_node):
                child_parsed_info = cls.parse_node_recursive(child_node)
                parsed_info["members"].append(child_parsed_info)

        return parsed_info

    def get_parsed_info(self):
        """
        Returns the parsed information for a file by recursively traversing the AST

        Returns:
            - parsed_info (dict):
                - Contains key-value pairs of various traits of a node
                - The key 'members' contains the node's children's `parsed_info`
        """
        return self.parse_node_recursive(self.root_node)

    # @TODO: Move the function out of this file in a separate PR
    @staticmethod
    def get_compilation_arguments(compilation_database_path, filename):
        """
        Yields the compilation commands extracted from the compilation database

        Parameters:
            - compilation_database_path: The path to `compile_commands.json`
            - filename: The file's name to get its compilation commands

        Yields:
            - compilation commands (list): The arguments passed to the compiler
        """

        # Build a compilation database found in the given directory
        compilation_database = clang.CompilationDatabase.fromDirectory(
            buildDir=compilation_database_path
        )
        # Get compilation commands from the compilation database for the given file
        compilation_commands = compilation_database.getCompileCommands(
            filename=filename
        )

        for compilation_command in compilation_commands:
            # Extract compiler arguments, excluding compiler and filename
            yield list(compilation_command.arguments)[1:-1]

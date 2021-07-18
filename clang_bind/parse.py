import clang.cindex as clang
from treelib import Tree

from clang_bind.clang_utils import ClangUtils


class Node:
    def __init__(self, cursor, verbose=False):
        self.cursor = cursor
        if verbose:
            # Add additional information about the cursor
            # Get values from the classes in cindex.py: `is_` methods, `get_` methods, @property values
            self.cursor_kind = ClangUtils(cursor.kind).get_all_functions_dict()
            self.cursor = ClangUtils(cursor).get_all_functions_dict()
            self.type = ClangUtils(cursor.type).get_all_functions_dict()

    def __repr__(self) -> str:
        return f"{self.cursor.kind.name}:'{self.cursor.spelling}'"


class Parse:
    """
    Class to parse a file and generate an AST from it.
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
        self.filename = source_ast.spelling
        self.tree = Tree()
        self.root_node = self.tree.create_node(
            identifier=Node(source_ast.cursor), tag=repr(Node(source_ast.cursor))
        )

    @staticmethod
    def is_node_from_file(node, filename):
        """
        Check if the node belongs in the file.
        """
        return node.location.file and node.location.file.name == filename

    def _is_valid_child(self, child_cursor):
        """
        Check if the child is valid (child should be in the same file as the parent).
        """
        return self.is_node_from_file(child_cursor, self.filename)

    def _construct_tree(self, node):
        """
        Recursively generates tree by traversing the AST of the node.
        """
        cursor = node.identifier.cursor
        for child_cursor in cursor.get_children():
            if self._is_valid_child(child_cursor):
                child_node = self.tree.create_node(
                    identifier=Node(child_cursor),
                    parent=node,
                    tag=repr(Node(child_cursor)),
                )
                self._construct_tree(child_node)

    def get_tree(self):
        """
        Returns the constructed tree.
        """
        self._construct_tree(self.root_node)
        return self.tree

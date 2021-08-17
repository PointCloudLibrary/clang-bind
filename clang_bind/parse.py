import clang.cindex as clang
from treelib import Tree

from clang_bind.clang_utils import ClangUtils


class ParsedInfo:
    """This is a data holder class containing parsed info, to be used while constructing the tree.

    :param cursor: An object of :class:`clang.cindex.Cursor`
    :type cursor: class:`clang.cindex.Cursor`
    :param verbose: Add additional information about the cursor, defaults to False
    :type verbose: bool, optional
    """

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
    """This is a class which parses a file and generate an abstract syntax tree from it.

    :param file: File to parse
    :type file: str
    :param compiler_arguments: Compiler arguments to use while parsing
    :type compiler_arguments: list, optional
    """

    def __init__(self, file, inclusion_sources=[], compiler_arguments=[]):
        self.inclusion_sources = inclusion_sources
        self._parsed_info_map = {}
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
        parsed_info = ParsedInfo(source_ast.cursor)
        self.root_node = self.tree.create_node(tag=repr(parsed_info))
        self._parsed_info_map[self.root_node.identifier] = parsed_info
        self._construct_tree(self.root_node)

    @staticmethod
    def is_cursor_in_files(cursor, files):
        """Checks if the cursor belongs in the files.

        :param cursor: An object of :class:`clang.cindex.Cursor`
        :type cursor: class:`clang.cindex.Cursor`
        :param files: Filepaths to search the cursor
        :type files: list
        :return: `True` if cursor in files, else `False`
        :rtype: bool
        """
        return cursor.location.file and cursor.location.file.name in files

    def _is_valid_child(self, child_cursor):
        """Checks if the child is valid:
        - Either child should be in the same file as the parent or,
        - the child should be in the list of valid inclusion sources

        :param child_cursor: The child cursor to check, an object of :class:`clang.cindex.Cursor`
        :type child_cursor: class:`clang.cindex.Cursor`
        :return: `True` if child cursor in file, else `False`
        :rtype: bool
        """
        return self.is_cursor_in_files(
            child_cursor, [self.filename, *self.inclusion_sources]
        )

    def _construct_tree(self, node):
        """Recursively generates tree by traversing the AST of the node.

        :param node: An object of :class:`treelib.Node`
        :type node: class:`treelib.Node`
        """
        cursor = self.get_parsed_info_from_node_id(node.identifier).cursor
        for child_cursor in cursor.get_children():
            if self._is_valid_child(child_cursor):
                parsed_info = ParsedInfo(child_cursor)
                child_node = self.tree.create_node(
                    parent=node,
                    tag=repr(parsed_info),
                )
                self._parsed_info_map[child_node.identifier] = parsed_info
                self._construct_tree(child_node)

    def get_tree(self):
        """Returns the constructed AST.

        :return: Constructed AST
        :rtype: class:`treelib.Tree`
        """
        return self.tree

    def get_node_id_from_parsed_info(self, parsed_info):
        """Returns node identifier by performing a value based search of `_parsed_info_map`.

        :param parsed_info: An object of :class:`clang_bind.parse.ParsedInfo`
        , the value to get the corresponding key from `_parsed_info_map`
        :type parsed_info`: class:`clang_bind.parse.ParsedInfo`
        :return node_id: Node identifier corresponding to `parsed_info`
        :rtype: `treelib.Tree.identifier`
        """
        for node_id, parsed_info_ in self._parsed_info_map.items():
            if parsed_info_ == parsed_info:
                return node_id

    def get_children_nodes_from_parent_parsed_info(self, parent_parsed_info):
        """Returns a list of children nodes from parent parsed infos.

        :param parent_parsed_info: The parent object of :class:`clang_bind.parse.ParsedInfo`
        :type parent_parsed_info: class:`clang_bind.parse.ParsedInfo`
        :return: Children nodes of :class:`treelib.Node`
        :rtype: list
        """
        return self.tree.children(self.get_node_id_from_parsed_info(parent_parsed_info))

    def get_parsed_infos_from_node_ids(self, node_ids):
        """Returns a list of parsed infos from a list of node identifiers
        , by getting the values from `_parsed_info_map`

        :param node_ids: Node identifiers of :class:`treelib.Node`
        :type node_ids: list
        :return: Parsed infos of :class:`clang_bind.parse.ParsedInfo`
        :rtype: list
        """
        return list(map(lambda node_id: self._parsed_info_map.get(node_id), node_ids))

    def get_parsed_info_from_node_id(self, node_id):
        """Returns parsed info from node identifier, by getting the value from `_parsed_info_map`

        :param node_id: Node identifier
        :type node_id: class:`treelib.Node`
        :return: Parsed info corresponding to `node_id`
        :rtype: class:`clang_bind.parse.ParsedInfo`
        """
        return self.get_parsed_infos_from_node_ids([node_id])[0]

    @staticmethod
    def get_node_ids_from_nodes(nodes):
        """Returns a list of node identifiers from a list of nodes.

        :param nodes: A list of objects of :class:`treelib.Node`
        :type nodes: class:`treelib.Node`
        :return: A list of node identifiers of `treelib.Tree.identifier`
        :rtype: list
        """
        return list(map(lambda node: node.identifier, nodes))

    def get_children_parsed_infos_from_parent_parsed_info(self, parent_parsed_info):
        """Returns children parsed infos from parent parsed infos.

        :param parent_parsed_info: The parent object of :class:`clang_bind.parse.ParsedInfo`
        :type parent_parsed_info: class:`clang_bind.parse.ParsedInfo`
        :return: Children parsed infos of :class:`clang_bind.parse.ParsedInfo`
        :rtype: list
        """
        return self.get_parsed_infos_from_node_ids(
            self.get_node_ids_from_nodes(
                self.get_children_nodes_from_parent_parsed_info(parent_parsed_info)
            )
        )

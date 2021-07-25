import tempfile

import clang.cindex as clang
from clang_bind.parse import Parse


class TestParse:
    parser, tree, tree_paths = None, None, None
    file = tempfile.NamedTemporaryFile(suffix=".cpp")

    def _parse(self, file_contents):
        self.file.write(bytes(file_contents, "utf-8"))  # write to temp file
        self.file.seek(0)

        self.parser = Parse(self.file.name)
        self.tree = self.parser.get_tree()  # parse the file to get an AST
        self.tree_paths = [
            self.parser.get_parsed_infos_from_node_ids(path)
            for path in self.tree.paths_to_leaves()
        ]  # a list of list of parsed infos, representing paths from the root node to each leaf

    def _debug_print(self):
        print("Tree:")
        self.tree.show()
        print(f"No. of paths: {len(self.tree_paths)}")
        for i, x in enumerate(self.tree_paths):
            print(f"Path {i}: {x}")

    def test_anonymous_decls(self):
        self._parse(
            """
        union {
            struct {
                enum {};
            };
        };
        """
        )

        union_decl = self.tree_paths[0][1]
        assert union_decl.cursor.kind == clang.CursorKind.UNION_DECL
        assert union_decl.cursor.is_anonymous()
        assert union_decl.cursor.spelling == ""

        struct_decl = self.tree_paths[0][2]
        assert struct_decl.cursor.kind == clang.CursorKind.STRUCT_DECL
        assert union_decl.cursor.is_anonymous()
        assert union_decl.cursor.spelling == ""

        enum_decl = self.tree_paths[0][3]
        assert enum_decl.cursor.kind == clang.CursorKind.ENUM_DECL
        assert union_decl.cursor.is_anonymous()
        assert union_decl.cursor.spelling == ""

    def test_translation_unit(self):
        self._parse("")

        tranlation_unit = self.tree_paths[0][0]
        assert tranlation_unit.cursor.kind == clang.CursorKind.TRANSLATION_UNIT
        assert tranlation_unit.cursor.spelling == self.file.name

    def test_namespace(self):
        self._parse("namespace a_namespace {}")

        namespace = self.tree_paths[0][1]
        assert namespace.cursor.kind == clang.CursorKind.NAMESPACE
        assert namespace.cursor.spelling == "a_namespace"

    def test_namespace_ref(self):
        self._parse(
            """
        #include <ostream>
        std::ostream anOstream;
        """
        )

        inclusion_directive = self.tree_paths[0][1]
        assert inclusion_directive.cursor.kind == clang.CursorKind.INCLUSION_DIRECTIVE
        assert inclusion_directive.cursor.spelling == "ostream"

        namespace_ref = self.tree_paths[1][2]
        assert namespace_ref.cursor.kind == clang.CursorKind.NAMESPACE_REF
        assert namespace_ref.cursor.spelling == "std"

    def test_var_decl(self):
        self._parse("int anInt = 1;")

        var_decl = self.tree_paths[0][1]
        assert var_decl.cursor.kind == clang.CursorKind.VAR_DECL
        assert var_decl.cursor.type.kind == clang.TypeKind.INT
        assert var_decl.cursor.spelling == "anInt"

    def test_field_decl(self):
        self._parse(
            """
        struct AStruct {
            int aClassMember;
        };
        """
        )

        field_decl = self.tree_paths[0][2]
        assert field_decl.cursor.kind == clang.CursorKind.FIELD_DECL
        assert field_decl.cursor.type.kind == clang.TypeKind.INT
        assert field_decl.cursor.spelling == "aClassMember"

    def test_function_decl_without_parameters(self):
        self._parse(
            """
        int aFunction();
        """
        )

        function_decl = self.tree_paths[0][1]
        assert function_decl.cursor.kind == clang.CursorKind.FUNCTION_DECL
        assert function_decl.cursor.spelling == "aFunction"
        assert function_decl.cursor.result_type.kind == clang.TypeKind.INT

    def test_function_decl_with_parameters(self):
        self._parse(
            """
        int aFunction(int firstParam, double secondParam);
        """
        )

        function_decl = self.tree_paths[0][1]
        assert function_decl.cursor.kind == clang.CursorKind.FUNCTION_DECL
        assert function_decl.cursor.spelling == "aFunction"
        assert function_decl.cursor.result_type.kind == clang.TypeKind.INT

        function_decl_children = self.parser.get_parsed_infos_from_node_ids(
            self.parser.get_node_ids_from_nodes(
                self.parser.get_children_nodes_from_parent_parsed_info(function_decl)
            )
        )

        first_param = function_decl_children[0]
        assert first_param.cursor.spelling == "firstParam"
        assert first_param.cursor.type.kind == clang.TypeKind.INT

        second_param = function_decl_children[1]
        assert second_param.cursor.spelling == "secondParam"
        assert second_param.cursor.type.kind == clang.TypeKind.DOUBLE

    def test_simple_call_expr(self):
        self._parse(
            """
        int aFunction() {
            return 1;
        }
        int anInt = aFunction();
        """
        )

        call_expr = self.tree_paths[1][2]
        assert call_expr.cursor.kind == clang.CursorKind.CALL_EXPR
        assert call_expr.cursor.spelling == "aFunction"

    def test_struct_decl(self):
        self._parse("struct AStruct {};")

        struct_decl = self.tree_paths[0][1]
        assert struct_decl.cursor.kind == clang.CursorKind.STRUCT_DECL
        assert struct_decl.cursor.spelling == "AStruct"

    def test_public_inheritance(self):
        self._parse(
            """
        struct BaseStruct {};
        struct DerivedStruct: public BaseStruct {};
        """
        )

        cxx_base_specifier = self.tree_paths[1][2]
        assert cxx_base_specifier.cursor.kind == clang.CursorKind.CXX_BASE_SPECIFIER
        assert (
            cxx_base_specifier.cursor.access_specifier == clang.AccessSpecifier.PUBLIC
        )
        assert cxx_base_specifier.cursor.spelling == "struct BaseStruct"

    def test_member_function(self):
        self._parse(
            """
        struct AStruct {
            void aMethod() {}
        };
        """
        )

        cxx_method = self.tree_paths[0][2]
        assert cxx_method.cursor.kind == clang.CursorKind.CXX_METHOD
        assert cxx_method.cursor.result_type.kind == clang.TypeKind.VOID
        assert cxx_method.cursor.spelling == "aMethod"

    def test_type_ref(self):
        self._parse(
            """
        struct SomeUsefulType {};

        class AClass {
            void aMethod(SomeUsefulType aParameter) {};
        };
        """
        )

        parm_decl = self.tree_paths[1][3]
        assert parm_decl.cursor.kind == clang.CursorKind.PARM_DECL
        assert parm_decl.cursor.spelling == "aParameter"

        type_ref = self.tree_paths[1][4]
        assert type_ref.cursor.kind == clang.CursorKind.TYPE_REF
        assert type_ref.cursor.spelling == "struct SomeUsefulType"

    def test_simple_constructor(self):
        self._parse(
            """
        struct AStruct {
            AStruct() {}
        };
        """
        )

        constructor = self.tree_paths[0][2]
        assert constructor.cursor.kind == clang.CursorKind.CONSTRUCTOR
        assert constructor.cursor.access_specifier == clang.AccessSpecifier.PUBLIC
        assert constructor.cursor.spelling == "AStruct"

    def test_unexposed_expr(self):
        self._parse(
            """
        class SimpleClassWithConstructor {
            int aClassMember;
            SimpleClassWithConstructor(int aConstructorParameter) : aClassMember(aConstructorParameter) {};
        };
        """
        )

        member_ref = self.tree_paths[2][3]
        assert member_ref.cursor.kind == clang.CursorKind.MEMBER_REF
        assert member_ref.cursor.spelling == "aClassMember"

        unexposed_expr = self.tree_paths[3][3]
        assert unexposed_expr.cursor.kind == clang.CursorKind.UNEXPOSED_EXPR
        assert unexposed_expr.cursor.spelling == "aConstructorParameter"

    def test_decl_ref_expr(self):
        self._parse(
            """
        struct AStruct {
            int firstMember, secondMember;
            AStruct(int firstFunctionParameter, int secondFunctionParameter)
            : firstMember(secondFunctionParameter), secondMember(firstFunctionParameter)
            {}
        };
        """
        )

        decl_ref_expr_1 = self.tree_paths[5][4]
        assert decl_ref_expr_1.cursor.kind == clang.CursorKind.DECL_REF_EXPR
        assert decl_ref_expr_1.cursor.spelling == "secondFunctionParameter"

        decl_ref_expr_2 = self.tree_paths[7][4]
        assert decl_ref_expr_2.cursor.kind == clang.CursorKind.DECL_REF_EXPR
        assert decl_ref_expr_2.cursor.spelling == "firstFunctionParameter"

    def test_member_ref(self):
        self._parse(
            """
        struct AStruct {
            int firstMember, secondMember;
            AStruct(int firstFunctionParameter, int secondFunctionParameter)
            : firstMember(secondFunctionParameter), secondMember(firstFunctionParameter)
            {}
        };
        """
        )

        member_ref_1 = self.tree_paths[4][3]
        assert member_ref_1.cursor.kind == clang.CursorKind.MEMBER_REF
        assert member_ref_1.cursor.type.kind == clang.TypeKind.INT
        assert member_ref_1.cursor.spelling == "firstMember"

        member_ref_2 = self.tree_paths[6][3]
        assert member_ref_2.cursor.kind == clang.CursorKind.MEMBER_REF
        assert member_ref_2.cursor.type.kind == clang.TypeKind.INT
        assert member_ref_2.cursor.spelling == "secondMember"

    def test_class_template(self):
        self._parse(
            """
        template <typename T>
        struct AStruct {};
        """
        )

        class_template = self.tree_paths[0][1]
        assert class_template.cursor.kind == clang.CursorKind.CLASS_TEMPLATE
        assert class_template.cursor.spelling == "AStruct"

        template_type_parameter = self.tree_paths[0][2]
        assert (
            template_type_parameter.cursor.kind
            == clang.CursorKind.TEMPLATE_TYPE_PARAMETER
        )
        assert template_type_parameter.cursor.spelling == "T"
        assert (
            template_type_parameter.cursor.access_specifier
            == clang.AccessSpecifier.PUBLIC
        )

    def test_template_non_type_parameter(self):
        self._parse(
            """
        template <int N>
        struct AStruct {};
        """
        )

        class_template = self.tree_paths[0][1]
        assert class_template.cursor.kind == clang.CursorKind.CLASS_TEMPLATE
        assert class_template.cursor.spelling == "AStruct"

        template_non_type_parameter = self.tree_paths[0][2]
        assert (
            template_non_type_parameter.cursor.kind
            == clang.CursorKind.TEMPLATE_NON_TYPE_PARAMETER
        )
        assert template_non_type_parameter.cursor.type.kind == clang.TypeKind.INT
        assert template_non_type_parameter.cursor.spelling == "N"

    def test_function_template(self):
        self._parse(
            """
        template <typename T>
        void aFunction() {}
        """
        )

        function_template = self.tree_paths[0][1]
        assert function_template.cursor.kind == clang.CursorKind.FUNCTION_TEMPLATE
        assert function_template.cursor.result_type.kind == clang.TypeKind.VOID
        assert function_template.cursor.spelling == "aFunction"

        template_type_parameter = self.tree_paths[0][2]
        assert (
            template_type_parameter.cursor.kind
            == clang.CursorKind.TEMPLATE_TYPE_PARAMETER
        )
        assert template_type_parameter.cursor.spelling == "T"
        assert (
            template_type_parameter.cursor.access_specifier
            == clang.AccessSpecifier.PUBLIC
        )

    def test_template_type_parameter(self):
        self._parse(
            """
        template <typename T>
        struct AStruct {};

        template <typename P>
        void aFunction() {}
        """
        )

        template_type_parameter_1 = self.tree_paths[0][2]
        assert (
            template_type_parameter_1.cursor.kind
            == clang.CursorKind.TEMPLATE_TYPE_PARAMETER
        )
        assert template_type_parameter_1.cursor.type.kind == clang.TypeKind.UNEXPOSED
        assert template_type_parameter_1.cursor.spelling == "T"

        template_type_parameter_2 = self.tree_paths[1][2]
        assert (
            template_type_parameter_2.cursor.kind
            == clang.CursorKind.TEMPLATE_TYPE_PARAMETER
        )
        assert template_type_parameter_2.cursor.type.kind == clang.TypeKind.UNEXPOSED
        assert template_type_parameter_2.cursor.spelling == "P"

    def test_default_delete_constructor(self):
        self._parse(
            """
        class aClass {
            aClass() = default;

            // disable the copy constructor
            aClass(double) = delete;
        };
        """
        )

        default_constructor = self.tree_paths[0][2]
        assert default_constructor.cursor.kind == clang.CursorKind.CONSTRUCTOR
        assert default_constructor.cursor.spelling == "aClass"
        assert default_constructor.cursor.result_type.kind == clang.TypeKind.VOID
        assert default_constructor.cursor.is_default_constructor()

        delete_constructor = self.tree_paths[1][2]
        assert delete_constructor.cursor.kind == clang.CursorKind.CONSTRUCTOR
        assert delete_constructor.cursor.spelling == "aClass"
        assert delete_constructor.cursor.result_type.kind == clang.TypeKind.VOID
        # no check available for deleted ctor analogous to `is_default_constructor`

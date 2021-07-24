import clang.cindex as clang
from clang_bind.parse import Parse

FILE = "file.cpp"


def parse(tmp_path, file_contents):
    source_path = tmp_path / FILE
    with open(source_path, "w") as f:
        f.write(str(file_contents))

    parser = Parse(source_path)
    tree = parser.get_tree()  # parse the file into an AST
    tree_paths = [
        parser.get_parsed_infos_from_node_ids(path) for path in tree.paths_to_leaves()
    ]  # a list of list of parsed infos, representing paths from the root node to each leaf
    return parser, tree_paths


def debug_print(tree, tree_paths):
    print("Tree:")
    tree.show()
    print(f"No. of paths: {len(tree_paths)}")
    for i, x in enumerate(tree_paths):
        print(f"Path {i}: {x}")


def test_anonymous_decls(tmp_path):
    file_contents = """
    union {
        struct {
            enum {};
        };
    };
    """
    _, tree_paths = parse(tmp_path=tmp_path, file_contents=file_contents)

    union_decl = tree_paths[0][1]
    assert union_decl.cursor.kind == clang.CursorKind.UNION_DECL
    assert union_decl.cursor.is_anonymous()
    assert union_decl.cursor.spelling == ""

    struct_decl = tree_paths[0][2]
    assert struct_decl.cursor.kind == clang.CursorKind.STRUCT_DECL
    assert union_decl.cursor.is_anonymous()
    assert union_decl.cursor.spelling == ""

    enum_decl = tree_paths[0][3]
    assert enum_decl.cursor.kind == clang.CursorKind.ENUM_DECL
    assert union_decl.cursor.is_anonymous()
    assert union_decl.cursor.spelling == ""


def test_translation_unit(tmp_path):
    file_contents = ""
    _, tree_paths = parse(tmp_path=tmp_path, file_contents=file_contents)

    tranlation_unit = tree_paths[0][0]
    assert tranlation_unit.cursor.kind == clang.CursorKind.TRANSLATION_UNIT
    assert tranlation_unit.cursor.spelling == str(tmp_path / FILE)


def test_namespace(tmp_path):
    file_contents = "namespace a_namespace {}"
    _, tree_paths = parse(tmp_path=tmp_path, file_contents=file_contents)

    namespace = tree_paths[0][1]
    assert namespace.cursor.kind == clang.CursorKind.NAMESPACE
    assert namespace.cursor.spelling == "a_namespace"


def test_namespace_ref(tmp_path):
    file_contents = """
    #include <ostream>
    std::ostream anOstream;
    """
    _, tree_paths = parse(tmp_path=tmp_path, file_contents=file_contents)

    inclusion_directive = tree_paths[0][1]
    assert inclusion_directive.cursor.kind == clang.CursorKind.INCLUSION_DIRECTIVE
    assert inclusion_directive.cursor.spelling == "ostream"

    namespace_ref = tree_paths[1][2]
    assert namespace_ref.cursor.kind == clang.CursorKind.NAMESPACE_REF
    assert namespace_ref.cursor.spelling == "std"


def test_var_decl(tmp_path):
    file_contents = "int anInt = 1;"
    _, tree_paths = parse(tmp_path=tmp_path, file_contents=file_contents)

    var_decl = tree_paths[0][1]
    assert var_decl.cursor.kind == clang.CursorKind.VAR_DECL
    assert var_decl.cursor.type.kind == clang.TypeKind.INT
    assert var_decl.cursor.spelling == "anInt"


def test_field_decl(tmp_path):
    file_contents = """
    struct AStruct {
        int aClassMember;
    };
    """
    _, tree_paths = parse(tmp_path=tmp_path, file_contents=file_contents)

    field_decl = tree_paths[0][2]
    assert field_decl.cursor.kind == clang.CursorKind.FIELD_DECL
    assert field_decl.cursor.type.kind == clang.TypeKind.INT
    assert field_decl.cursor.spelling == "aClassMember"


def test_function_decl_without_parameters(tmp_path):
    file_contents = """
    int aFunction();
    """
    _, tree_paths = parse(tmp_path=tmp_path, file_contents=file_contents)

    function_decl = tree_paths[0][1]
    assert function_decl.cursor.kind == clang.CursorKind.FUNCTION_DECL
    assert function_decl.cursor.spelling == "aFunction"
    assert function_decl.cursor.result_type.kind == clang.TypeKind.INT


def test_function_decl_with_parameters(tmp_path):
    file_contents = """
    int aFunction(int firstParam, double secondParam);
    """
    parser, tree_paths = parse(tmp_path=tmp_path, file_contents=file_contents)

    function_decl = tree_paths[0][1]
    assert function_decl.cursor.kind == clang.CursorKind.FUNCTION_DECL
    assert function_decl.cursor.spelling == "aFunction"
    assert function_decl.cursor.result_type.kind == clang.TypeKind.INT

    function_decl_children = parser.get_parsed_infos_from_node_ids(
        parser.get_node_ids_from_nodes(
            parser.get_children_nodes_from_parent_parsed_info(function_decl)
        )
    )

    first_param = function_decl_children[0]
    assert first_param.cursor.spelling == "firstParam"
    assert first_param.cursor.type.kind == clang.TypeKind.INT

    second_param = function_decl_children[1]
    assert second_param.cursor.spelling == "secondParam"
    assert second_param.cursor.type.kind == clang.TypeKind.DOUBLE


def test_simple_call_expr(tmp_path):
    file_contents = """
    int aFunction() {
        return 1;
    }
    int anInt = aFunction();
    """
    _, tree_paths = parse(tmp_path=tmp_path, file_contents=file_contents)

    call_expr = tree_paths[1][2]
    assert call_expr.cursor.kind == clang.CursorKind.CALL_EXPR
    assert call_expr.cursor.spelling == "aFunction"


def test_struct_decl(tmp_path):
    file_contents = "struct AStruct {};"
    _, tree_paths = parse(tmp_path=tmp_path, file_contents=file_contents)

    struct_decl = tree_paths[0][1]
    assert struct_decl.cursor.kind == clang.CursorKind.STRUCT_DECL
    assert struct_decl.cursor.spelling == "AStruct"


def test_public_inheritance(tmp_path):
    file_contents = """
    struct BaseStruct {};
    struct DerivedStruct: public BaseStruct {};
    """
    _, tree_paths = parse(tmp_path=tmp_path, file_contents=file_contents)

    cxx_base_specifier = tree_paths[1][2]
    assert cxx_base_specifier.cursor.kind == clang.CursorKind.CXX_BASE_SPECIFIER
    assert cxx_base_specifier.cursor.access_specifier == clang.AccessSpecifier.PUBLIC
    assert cxx_base_specifier.cursor.spelling == "struct BaseStruct"


def test_member_function(tmp_path):
    file_contents = """
    struct AStruct {
        void aMethod() {}
    };
    """
    _, tree_paths = parse(tmp_path=tmp_path, file_contents=file_contents)

    cxx_method = tree_paths[0][2]
    assert cxx_method.cursor.kind == clang.CursorKind.CXX_METHOD
    assert cxx_method.cursor.result_type.kind == clang.TypeKind.VOID
    assert cxx_method.cursor.spelling == "aMethod"


def test_type_ref(tmp_path):
    file_contents = """
    struct SomeUsefulType {};

    class AClass {
        void aMethod(SomeUsefulType aParameter) {};
    };
    """
    _, tree_paths = parse(tmp_path=tmp_path, file_contents=file_contents)

    parm_decl = tree_paths[1][3]
    assert parm_decl.cursor.kind == clang.CursorKind.PARM_DECL
    assert parm_decl.cursor.spelling == "aParameter"

    type_ref = tree_paths[1][4]
    assert type_ref.cursor.kind == clang.CursorKind.TYPE_REF
    assert type_ref.cursor.spelling == "struct SomeUsefulType"


def test_simple_constructor(tmp_path):
    file_contents = """
    struct AStruct {
        AStruct() {}
    };
    """
    _, tree_paths = parse(tmp_path=tmp_path, file_contents=file_contents)

    constructor = tree_paths[0][2]
    assert constructor.cursor.kind == clang.CursorKind.CONSTRUCTOR
    assert constructor.cursor.access_specifier == clang.AccessSpecifier.PUBLIC
    assert constructor.cursor.spelling == "AStruct"


def test_unexposed_expr(tmp_path):
    file_contents = """
    class SimpleClassWithConstructor {
        int aClassMember;
        SimpleClassWithConstructor(int aConstructorParameter) : aClassMember(aConstructorParameter) {};
    };
    """
    _, tree_paths = parse(tmp_path=tmp_path, file_contents=file_contents)

    member_ref = tree_paths[2][3]
    assert member_ref.cursor.kind == clang.CursorKind.MEMBER_REF
    assert member_ref.cursor.spelling == "aClassMember"

    unexposed_expr = tree_paths[3][3]
    assert unexposed_expr.cursor.kind == clang.CursorKind.UNEXPOSED_EXPR
    assert unexposed_expr.cursor.spelling == "aConstructorParameter"


def test_decl_ref_expr(tmp_path):
    file_contents = """
    struct AStruct {
        int firstMember, secondMember;
        AStruct(int firstFunctionParameter, int secondFunctionParameter)
        : firstMember(secondFunctionParameter), secondMember(firstFunctionParameter)
        {}
    };
    """
    _, tree_paths = parse(tmp_path=tmp_path, file_contents=file_contents)

    decl_ref_expr_1 = tree_paths[5][4]
    assert decl_ref_expr_1.cursor.kind == clang.CursorKind.DECL_REF_EXPR
    assert decl_ref_expr_1.cursor.spelling == "secondFunctionParameter"

    decl_ref_expr_2 = tree_paths[7][4]
    assert decl_ref_expr_2.cursor.kind == clang.CursorKind.DECL_REF_EXPR
    assert decl_ref_expr_2.cursor.spelling == "firstFunctionParameter"


def test_member_ref(tmp_path):
    file_contents = """
    struct AStruct {
        int firstMember, secondMember;
        AStruct(int firstFunctionParameter, int secondFunctionParameter)
        : firstMember(secondFunctionParameter), secondMember(firstFunctionParameter)
        {}
    };
    """
    _, tree_paths = parse(tmp_path=tmp_path, file_contents=file_contents)

    member_ref_1 = tree_paths[4][3]
    assert member_ref_1.cursor.kind == clang.CursorKind.MEMBER_REF
    assert member_ref_1.cursor.type.kind == clang.TypeKind.INT
    assert member_ref_1.cursor.spelling == "firstMember"

    member_ref_2 = tree_paths[6][3]
    assert member_ref_2.cursor.kind == clang.CursorKind.MEMBER_REF
    assert member_ref_2.cursor.type.kind == clang.TypeKind.INT
    assert member_ref_2.cursor.spelling == "secondMember"


def test_class_template(tmp_path):
    file_contents = """
    template <typename T>
    struct AStruct {};
    """
    _, tree_paths = parse(tmp_path=tmp_path, file_contents=file_contents)

    class_template = tree_paths[0][1]
    assert class_template.cursor.kind == clang.CursorKind.CLASS_TEMPLATE
    assert class_template.cursor.spelling == "AStruct"

    template_type_parameter = tree_paths[0][2]
    assert (
        template_type_parameter.cursor.kind == clang.CursorKind.TEMPLATE_TYPE_PARAMETER
    )
    assert template_type_parameter.cursor.spelling == "T"
    assert (
        template_type_parameter.cursor.access_specifier == clang.AccessSpecifier.PUBLIC
    )


def test_template_non_type_parameter(tmp_path):
    file_contents = """
    template <int N>
    struct AStruct {};
    """
    _, tree_paths = parse(tmp_path=tmp_path, file_contents=file_contents)

    class_template = tree_paths[0][1]
    assert class_template.cursor.kind == clang.CursorKind.CLASS_TEMPLATE
    assert class_template.cursor.spelling == "AStruct"

    template_non_type_parameter = tree_paths[0][2]
    assert (
        template_non_type_parameter.cursor.kind
        == clang.CursorKind.TEMPLATE_NON_TYPE_PARAMETER
    )
    assert template_non_type_parameter.cursor.type.kind == clang.TypeKind.INT
    assert template_non_type_parameter.cursor.spelling == "N"


def test_function_template(tmp_path):
    file_contents = """
    template <typename T>
    void aFunction() {}
    """
    _, tree_paths = parse(tmp_path=tmp_path, file_contents=file_contents)

    function_template = tree_paths[0][1]
    assert function_template.cursor.kind == clang.CursorKind.FUNCTION_TEMPLATE
    assert function_template.cursor.result_type.kind == clang.TypeKind.VOID
    assert function_template.cursor.spelling == "aFunction"

    template_type_parameter = tree_paths[0][2]
    assert (
        template_type_parameter.cursor.kind == clang.CursorKind.TEMPLATE_TYPE_PARAMETER
    )
    assert template_type_parameter.cursor.spelling == "T"
    assert (
        template_type_parameter.cursor.access_specifier == clang.AccessSpecifier.PUBLIC
    )


def test_template_type_parameter(tmp_path):
    file_contents = """
    template <typename T>
    struct AStruct {};

    template <typename P>
    void aFunction() {}
    """
    _, tree_paths = parse(tmp_path=tmp_path, file_contents=file_contents)

    template_type_parameter_1 = tree_paths[0][2]
    assert (
        template_type_parameter_1.cursor.kind
        == clang.CursorKind.TEMPLATE_TYPE_PARAMETER
    )
    assert template_type_parameter_1.cursor.type.kind == clang.TypeKind.UNEXPOSED
    assert template_type_parameter_1.cursor.spelling == "T"

    template_type_parameter_2 = tree_paths[1][2]
    assert (
        template_type_parameter_2.cursor.kind
        == clang.CursorKind.TEMPLATE_TYPE_PARAMETER
    )
    assert template_type_parameter_2.cursor.type.kind == clang.TypeKind.UNEXPOSED
    assert template_type_parameter_2.cursor.spelling == "P"


def test_default_delete_constructor(tmp_path):
    file_contents = """
    class aClass {
        aClass() = default;

        // disable the copy constructor
        aClass(double) = delete;
    };
    """
    _, tree_paths = parse(tmp_path=tmp_path, file_contents=file_contents)

    default_constructor = tree_paths[0][2]
    assert default_constructor.cursor.kind == clang.CursorKind.CONSTRUCTOR
    assert default_constructor.cursor.spelling == "aClass"
    assert default_constructor.cursor.result_type.kind == clang.TypeKind.VOID
    assert default_constructor.cursor.is_default_constructor()

    delete_constructor = tree_paths[1][2]
    assert delete_constructor.cursor.kind == clang.CursorKind.CONSTRUCTOR
    assert delete_constructor.cursor.spelling == "aClass"
    assert delete_constructor.cursor.result_type.kind == clang.TypeKind.VOID
    # no check available for deleted ctor analogous to `is_default_constructor`

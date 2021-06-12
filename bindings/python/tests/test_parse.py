from context import scripts
import clang.cindex as clang
from scripts.parse import Parse
from scripts.compilation_database import CompilationDatabase


def get_compilation_database_path(tmp_path, filepath):
    input = tmp_path / "compile_commands.json"
    x = [
        {
            "directory": f"{tmp_path}",
            "command": f"/usr/bin/clang++ -std=c++14 {filepath}",
            "file": f"{filepath}",
        }
    ]

    with open(input, "w") as f:
        f.write(str(x))

    return str(tmp_path)


def get_parsed_info(tmp_path, file_contents):
    source_path = tmp_path / "file.cpp"

    with open(source_path, "w") as f:
        f.write(str(file_contents))

        compilation_database_path = get_compilation_database_path(
            tmp_path=tmp_path, filepath=source_path
        )

        compilation_database = CompilationDatabase(
            compilation_database_path=compilation_database_path
        )

        compilation_arguments = compilation_database.get_compilation_arguments(
            filename=source_path
        )

        compiler_arguments = compilation_arguments.get(source_path)

    parsed_info = Parse(source_path, compiler_arguments).get_parsed_info()

    return parsed_info


def test_anonymous_decls(tmp_path):
    file_contents = """
    union {
        struct {
            enum {};
        };
    };
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    union_decl = parsed_info["members"][0]

    assert union_decl["cursor_kind"]["name"] == "UNION_DECL"
    assert union_decl["cursor"]["is_anonymous"] == True
    assert union_decl["cursor"]["spelling"] == ""

    struct_decl = union_decl["members"][0]

    assert struct_decl["cursor_kind"]["name"] == "STRUCT_DECL"
    assert union_decl["cursor"]["is_anonymous"] == True
    assert union_decl["cursor"]["spelling"] == ""

    enum_decl = struct_decl["members"][0]

    assert enum_decl["cursor_kind"]["name"] == "ENUM_DECL"
    assert union_decl["cursor"]["is_anonymous"] == True
    assert union_decl["cursor"]["spelling"] == ""


def test_translation_unit(tmp_path):
    file_contents = ""
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    assert parsed_info["cursor_kind"]["name"] == "TRANSLATION_UNIT"
    assert parsed_info["depth"] == 0
    assert parsed_info["cursor"]["spelling"] == str(tmp_path / "file.cpp")


def test_namespace(tmp_path):
    file_contents = "namespace a_namespace {}"
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    namespace = parsed_info["members"][0]

    assert namespace["cursor_kind"]["name"] == "NAMESPACE"
    assert namespace["cursor"]["spelling"] == "a_namespace"


def test_namespace_ref(tmp_path):
    file_contents = """
    #include <ostream>
    std::ostream anOstream;
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    inclusion_directive = parsed_info["members"][0]

    assert inclusion_directive["cursor_kind"]["name"] == "INCLUSION_DIRECTIVE"
    assert inclusion_directive["cursor"]["spelling"] == "ostream"

    var_decl = parsed_info["members"][1]
    namespace_ref = var_decl["members"][0]

    assert namespace_ref["cursor_kind"]["name"] == "NAMESPACE_REF"
    assert namespace_ref["cursor"]["spelling"] == "std"


def test_var_decl(tmp_path):
    file_contents = "int anInt = 1;"
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    var_decl = parsed_info["members"][0]

    assert var_decl["cursor_kind"]["name"] == "VAR_DECL"
    assert var_decl["type"]["kind"] == "INT"
    assert var_decl["cursor"]["spelling"] == "anInt"


def test_field_decl(tmp_path):
    file_contents = """
    struct AStruct {
        int aClassMember;
    };
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    struct_decl = parsed_info["members"][0]
    field_decl = struct_decl["members"][0]

    assert field_decl["cursor_kind"]["name"] == "FIELD_DECL"
    assert field_decl["type"]["kind"] == "INT"
    assert field_decl["cursor"]["spelling"] == "aClassMember"


def test_parsed_info_structure(tmp_path):
    file_contents = ""
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    assert type(parsed_info) is dict
    assert type(parsed_info["members"]) is list
    assert len(parsed_info["members"]) == 0


def test_function_decl_without_parameters(tmp_path):
    file_contents = """
    int aFunction();
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    func_decl = parsed_info["members"][0]

    assert func_decl["cursor_kind"]["name"] == "FUNCTION_DECL"
    assert func_decl["cursor"]["spelling"] == "aFunction"
    assert func_decl["cursor"]["result_type"] == "int"


def test_function_decl_with_parameters(tmp_path):
    file_contents = """
    int aFunction(int firstParam, double secondParam);
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    func_decl = parsed_info["members"][0]

    assert func_decl["cursor_kind"]["name"] == "FUNCTION_DECL"
    assert func_decl["cursor"]["spelling"] == "aFunction"
    assert func_decl["cursor"]["result_type"] == "int"

    first_param = func_decl["members"][0]
    second_param = func_decl["members"][1]

    assert first_param["cursor"]["spelling"] == "firstParam"
    assert first_param["type"]["kind"] == "INT"

    assert second_param["cursor"]["spelling"] == "secondParam"
    assert second_param["type"]["kind"] == "DOUBLE"


def test_simple_call_expr(tmp_path):
    file_contents = """
    int aFunction() {
        return 1;
    }
    int anInt = aFunction();
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    var_decl = parsed_info["members"][1]
    call_expr = var_decl["members"][0]

    assert call_expr["cursor_kind"]["name"] == "CALL_EXPR"
    assert call_expr["cursor"]["spelling"] == "aFunction"

    assert var_decl["cursor"]["spelling"] == "anInt"


def test_struct_decl(tmp_path):
    file_contents = "struct AStruct {};"
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    struct_decl = parsed_info["members"][0]

    assert struct_decl["cursor_kind"]["name"] == "STRUCT_DECL"
    assert struct_decl["cursor"]["spelling"] == "AStruct"


def test_public_inheritance(tmp_path):
    file_contents = """
    struct BaseStruct {};
    struct DerivedStruct: public BaseStruct {};
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    child_struct_decl = parsed_info["members"][1]
    cxx_base_specifier = child_struct_decl["members"][0]

    assert cxx_base_specifier["cursor_kind"]["name"] == "CXX_BASE_SPECIFIER"
    assert cxx_base_specifier["cursor"]["access_specifier"] == "PUBLIC"
    assert cxx_base_specifier["cursor"]["spelling"] == "struct BaseStruct"


def test_member_function(tmp_path):
    file_contents = """
    struct AStruct {
        void aMethod() {}
    };
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    struct_decl = parsed_info["members"][0]
    cxx_method = struct_decl["members"][0]

    assert cxx_method["cursor_kind"]["name"] == "CXX_METHOD"
    assert cxx_method["cursor"]["result_type"] == "void"
    assert cxx_method["cursor"]["spelling"] == "aMethod"


def test_type_ref(tmp_path):
    file_contents = """
    struct SomeUsefulType {};

    class AClass {
        void aMethod(SomeUsefulType aParameter) {};
    };
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    class_decl = parsed_info["members"][1]
    cxx_method = class_decl["members"][0]
    parm_decl = cxx_method["members"][0]

    assert parm_decl["cursor"]["spelling"] == "aParameter"

    type_ref = parm_decl["members"][0]

    assert type_ref["cursor_kind"]["name"] == "TYPE_REF"
    assert type_ref["cursor"]["spelling"] == "struct SomeUsefulType"


def test_simple_constructor(tmp_path):
    file_contents = """
    struct AStruct {
        AStruct() {}
    };
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    struct_decl = parsed_info["members"][0]
    constructor = struct_decl["members"][0]

    assert constructor["cursor_kind"]["name"] == "CONSTRUCTOR"
    assert constructor["cursor"]["access_specifier"] == "PUBLIC"
    assert constructor["cursor"]["spelling"] == "AStruct"


def test_unexposed_expr(tmp_path):
    file_contents = """
    class SimpleClassWithConstructor {
        int aClassMember;
        SimpleClassWithConstructor(int aConstructorParameter) : aClassMember(aConstructorParameter) {};
    };
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    struct_decl = parsed_info["members"][0]
    constructor = struct_decl["members"][1]
    member_ref = constructor["members"][1]

    assert member_ref["cursor"]["spelling"] == "aClassMember"

    unexposed_expr = constructor["members"][2]

    assert unexposed_expr["cursor_kind"]["name"] == "UNEXPOSED_EXPR"
    assert unexposed_expr["cursor"]["spelling"] == "aConstructorParameter"


# @TODO: Not sure how to reproduce. Maybe later.
# def test_member_ref_expr(tmp_path):


def test_decl_ref_expr(tmp_path):
    file_contents = """
    struct AStruct {
        int firstMember, secondMember;
        AStruct(int firstFunctionParameter, int secondFunctionParameter)
        : firstMember(secondFunctionParameter), secondMember(firstFunctionParameter)
        {}
    };
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    struct_decl = parsed_info["members"][0]
    constructor = struct_decl["members"][2]
    unexposed_expr_1 = constructor["members"][3]
    unexposed_expr_2 = constructor["members"][5]
    decl_ref_expr_1 = unexposed_expr_1["members"][0]
    decl_ref_expr_2 = unexposed_expr_2["members"][0]

    assert decl_ref_expr_1["cursor_kind"]["name"] == "DECL_REF_EXPR"
    assert decl_ref_expr_2["cursor_kind"]["name"] == "DECL_REF_EXPR"
    assert decl_ref_expr_1["cursor"]["spelling"] == "secondFunctionParameter"
    assert decl_ref_expr_2["cursor"]["spelling"] == "firstFunctionParameter"


def test_member_ref(tmp_path):
    file_contents = """
    struct AStruct {
        int firstMember, secondMember;
        AStruct(int firstFunctionParameter, int secondFunctionParameter)
        : firstMember(secondFunctionParameter), secondMember(firstFunctionParameter)
        {}
    };
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)
    struct_decl = parsed_info["members"][0]
    constructor = struct_decl["members"][2]
    member_ref_1 = constructor["members"][2]
    member_ref_2 = constructor["members"][4]

    assert member_ref_1["cursor_kind"]["name"] == "MEMBER_REF"
    assert member_ref_2["cursor_kind"]["name"] == "MEMBER_REF"
    assert member_ref_1["type"]["kind"] == "INT"
    assert member_ref_2["type"]["kind"] == "INT"
    assert member_ref_1["cursor"]["spelling"] == "firstMember"
    assert member_ref_2["cursor"]["spelling"] == "secondMember"


def test_class_template(tmp_path):
    file_contents = """
    template <typename T>
    struct AStruct {};
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    class_template = parsed_info["members"][0]

    assert class_template["cursor_kind"]["name"] == "CLASS_TEMPLATE"
    assert class_template["cursor"]["spelling"] == "AStruct"

    template_type_parameter = class_template["members"][0]

    assert template_type_parameter["cursor_kind"]["name"] == "TEMPLATE_TYPE_PARAMETER"
    assert template_type_parameter["cursor"]["spelling"] == "T"
    assert template_type_parameter["cursor"]["access_specifier"] == "PUBLIC"


def test_template_non_type_parameter(tmp_path):
    file_contents = """
    template <int N>
    struct AStruct {};
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    class_template = parsed_info["members"][0]

    assert class_template["cursor_kind"]["name"] == "CLASS_TEMPLATE"
    assert class_template["cursor"]["spelling"] == "AStruct"

    template_non_type_parameter = class_template["members"][0]

    assert (
        template_non_type_parameter["cursor_kind"]["name"]
        == "TEMPLATE_NON_TYPE_PARAMETER"
    )
    assert template_non_type_parameter["type"]["kind"] == "INT"
    assert template_non_type_parameter["cursor"]["spelling"] == "N"


def test_function_template(tmp_path):
    file_contents = """
    template <typename T>
    void aFunction() {}
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    function_template = parsed_info["members"][0]

    assert function_template["cursor_kind"]["name"] == "FUNCTION_TEMPLATE"
    assert function_template["cursor"]["result_type"] == "void"
    assert function_template["cursor"]["spelling"] == "aFunction"

    template_type_parameter = function_template["members"][0]

    assert template_type_parameter["cursor_kind"]["name"] == "TEMPLATE_TYPE_PARAMETER"
    assert template_type_parameter["cursor"]["spelling"] == "T"
    assert template_type_parameter["cursor"]["access_specifier"] == "PUBLIC"


def test_template_type_parameter(tmp_path):
    file_contents = """
    template <typename T>
    struct AStruct {};

    template <typename P>
    void aFunction() {}
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    class_template = parsed_info["members"][0]
    template_type_parameter = class_template["members"][0]

    assert template_type_parameter["cursor_kind"]["name"] == "TEMPLATE_TYPE_PARAMETER"
    assert template_type_parameter["type"]["kind"] == "UNEXPOSED"
    assert template_type_parameter["cursor"]["spelling"] == "T"

    function_template = parsed_info["members"][1]
    template_type_parameter = function_template["members"][0]

    assert template_type_parameter["cursor_kind"]["name"] == "TEMPLATE_TYPE_PARAMETER"
    assert template_type_parameter["type"]["kind"] == "UNEXPOSED"
    assert template_type_parameter["cursor"]["spelling"] == "P"


def test_default_delete_constructor(tmp_path):
    file_contents = """
    class aClass {
        aClass() = default;

        // disable the copy constructor
        aClass(double) = delete;
    };
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    class_decl = parsed_info["members"][0]

    default_constructor = class_decl["members"][0]

    assert default_constructor["cursor_kind"]["name"] == "CONSTRUCTOR"
    assert default_constructor["cursor"]["spelling"] == "aClass"
    assert default_constructor["cursor"]["result_type"] == "void"
    assert default_constructor["cursor"]["is_default_constructor"]

    delete_constructor = class_decl["members"][1]

    assert delete_constructor["cursor_kind"]["name"] == "CONSTRUCTOR"
    assert delete_constructor["cursor"]["spelling"] == "aClass"
    assert delete_constructor["cursor"]["result_type"] == "void"
    # no check available for deleted ctor analogous to `is_default_constructor`

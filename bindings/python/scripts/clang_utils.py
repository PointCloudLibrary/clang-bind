import inspect
import clang.cindex as clang


def getmembers_static(object, predicate=None):
    """
    Return all members of an object as (name, value) pairs sorted by name via `getattr_static`.
    Optionally, only return members that satisfy a given predicate.


    - A static version of `get_members` function at:
      https://github.com/python/cpython/blob/3.9/Lib/inspect.py#L326-L368
      https://github.com/python/cpython/blob/14ba761078b5ae83519e34d66ab883743912c45b/Lib/inspect.py#L444-L486
        - `getmembers` function (from the inspect module) triggers execution instead of doing static analysis.
        - This leads to errors, particularly on properties of classes in cindex.py, which causes segmentation errors or raises an Exception if a particular condition is not satisfied.
        - To curb this, we fetch the members statically. We define a custom function based on the one in the inspect module.
    """

    results = []
    names = dir(object)
    # :dd any DynamicClassAttributes to the list of names if object is a class;
    # this may result in duplicate entries if, for example, a virtual
    # attribute with the same name as a DynamicClassAttribute exists
    try:
        base_members = filter(
            lambda k, v: isinstance(v, types.DynamicClassAttribute),
            object.__bases__.__dict__.items(),
        )
        names.extend(base_members)
    except AttributeError:
        pass
    for key in names:
        value = inspect.getattr_static(object, key)
        if not predicate or predicate(value):
            results.append((key, value))
    results.sort(key=lambda pair: pair[0])
    return results


class ClangUtils:
    """
    Clang's cindex class utilities.

    Supports the following objects:
        CursorKind:
          https://github.com/llvm/llvm-project/blob/release/12.x/clang/bindings/python/clang/cindex.py#L657
          https://github.com/llvm/llvm-project/blob/1acd9a1a29ac30044ecefb6613485d5d168f66ca/clang/bindings/python/clang/cindex.py#L657
            - A CursorKind describes the kind of entity that a cursor points to.
        Cursor:
          https://github.com/llvm/llvm-project/blob/release/12.x/clang/bindings/python/clang/cindex.py#L1415
          https://github.com/llvm/llvm-project/blob/1acd9a1a29ac30044ecefb6613485d5d168f66ca/clang/bindings/python/clang/cindex.py#L1415
            - The Cursor class represents a reference to an element within the AST. It acts as a kind of iterator.
        Type:
          https://github.com/llvm/llvm-project/blob/release/12.x/clang/bindings/python/clang/cindex.py#L2180
          https://github.com/llvm/llvm-project/blob/1acd9a1a29ac30044ecefb6613485d5d168f66ca/clang/bindings/python/clang/cindex.py#L2180
            - The Type class represents the type of an element in the abstract syntax tree.
    """

    def __init__(self, object):
        if not (
            isinstance(object, clang.CursorKind)
            or isinstance(object, clang.Cursor)
            or isinstance(object, clang.Type)
        ):
            raise NotImplementedError(f"Not implemented for {object}")

        self.check_functions_dict = {}
        self.get_functions_dict = {}
        self.properties_dict = {}

        # A list to ignore the functions/properties that causes segmentation errors.
        ignore_list = [
            "mangled_name",
            "get_address_space",
            "get_typedef_name",
            "tls_kind",
        ]

        # populate dicts
        valid_entries = filter(
            lambda entry: entry[0] not in ignore_list, getmembers_static(object)
        )
        for name, func in valid_entries:
            if inspect.isfunction(func):  # if function
                try:  # cindex.py's functions raise exceptions internally
                    if name.startswith("is_"):
                        self.check_functions_dict[name] = func(object)
                    if name.startswith("get_"):
                        self.get_functions_dict[name] = func(object)
                except:
                    continue
            elif isinstance(func, property):  # else, property
                try:  # cindex.py's property functions raise exceptions internally
                    self.properties_dict[name] = getattr(object, name)
                except:
                    continue

    def get_check_functions_dict(self):
        """
        Returns: `check_functions_dict`:
            - functions that begin with "is_" i.e., checking functions
            - {function_name, function_result}
        """
        return self.check_functions_dict

    def get_get_functions_dict(self):
        """
        Returns: `get_functions_dict`:
            - functions that begin with "get_" i.e., getter functions
            - {function_name, function_result}
        """
        return self.get_functions_dict

    def get_properties_dict(self):
        """
        Returns: properties_dict
            - Properties
            - {property_name, property}
        """
        return self.properties_dict

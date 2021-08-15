from pathlib import Path

from clang_bind.cmake_frontend import CMakeFileAPI, CompilationDatabase
from clang_bind.parse import Parse


class Bind:
    """Class to bind cpp modules.

    :param source_dir: Source dir of cpp library.
    :type source_dir: str
    :param build_dir: CMake build dir of cpp library, containing .cmake dir or compile_commands.json
    :type build_dir: str
    :param output_dir: Output dir
    :type output_dir: str
    :param output_module_name: Module name in python
    :type output_module_name: str
    :param cpp_modules: List of cpp modules to bind, defaults to []: bind all.
    :type cpp_modules: list, optional
    :param allow_inclusions_from_other_modules: Allow inclusions from other modules, which are not specified in cpp_modules, defaults to True
    :type allow_inclusions_from_other_modules: bool, optional
    """

    def __init__(
        self,
        source_dir,
        build_dir,
        output_dir,
        output_module_name,
        cpp_modules=[],
        allow_inclusions_from_other_modules=True,
    ):
        all_cpp_modules = CMakeFileAPI(build_dir).get_library_targets()
        if not cpp_modules:
            cpp_modules = all_cpp_modules  # bind all cpp modules

        all_inclusion_sources = []
        for module in all_cpp_modules:  # for all cpp modules, populate the variable
            sources = CMakeFileAPI(build_dir).get_sources(module)  # module's sources
            cpp_sources = list(
                filter(lambda source: source.endswith(".cpp"), sources)
            )  # sources ending with .cpp
            all_inclusion_sources += list(
                set(sources) - set(cpp_sources)
            )  # other sources like .h and .hpp files

        self.binding_db = {}  # binding database
        for module in cpp_modules:
            sources = CMakeFileAPI(build_dir).get_sources(module)  # module's sources
            cpp_sources = list(
                filter(lambda source: source.endswith(".cpp"), sources)
            )  # sources ending with .cpp
            inclusion_sources = (
                all_inclusion_sources
                if allow_inclusions_from_other_modules
                else list(set(sources) - set(cpp_sources))
            )  # other sources like .h and .hpp files

            self.binding_db[module] = {
                "inclusion_sources": inclusion_sources,  # inclusions for the module
                "files": [  # list of files' information
                    {
                        "source_path": Path(source_dir, cpp_source),
                        "output_path": Path(output_dir, cpp_source),
                        "compiler_arguments": CompilationDatabase(
                            build_dir
                        ).get_compilation_arguments(cpp_source),
                    }
                    for cpp_source in cpp_sources
                ],
            }

    def _parse(self):
        """For all input files, get the parsed tree and update the db."""
        for module in self.binding_db.values():
            for file in module.get("files"):
                # for each file, update the db with the parsed tree
                file.update(
                    {
                        "parsed_tree": Parse(
                            file.get("source_path"),
                            module.get("inclusion_sources"),
                            file.get("compiler_arguments"),
                        ).get_tree()
                    }
                )

    def bind(self):
        """Function to bind the input files."""
        self._parse()

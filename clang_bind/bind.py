from pathlib import Path

from clang_bind.cmake_frontend import CMakeFileAPI, CompilationDatabase
from clang_bind.parse import Parse


class Bind:
    """Class to bind C++ targets.

    :param source_dir: Source dir of cpp library.
    :type source_dir: str
    :param build_dir: CMake build dir of cpp library, containing .cmake dir or compile_commands.json
    :type build_dir: str
    :param output_dir: Output dir
    :type output_dir: str
    :param output_module_name: Module name in python
    :type output_module_name: str
    :param cpp_targets: List of C++ targets to bind, defaults to []: bind all.
    :type cpp_targets: list, optional
    :param allow_inclusions_from_other_targets: Allow inclusions from other targets, which are not specified in cpp_targets, defaults to True
    :type allow_inclusions_from_other_targets: bool, optional
    """

    def __init__(
        self,
        source_dir,
        build_dir,
        output_dir,
        output_module_name,
        cpp_targets=[],
        allow_inclusions_from_other_targets=True,
    ):
        all_cpp_targets = CMakeFileAPI(build_dir).get_library_targets()
        if not cpp_targets:
            cpp_targets = all_cpp_targets  # bind all C++ targets

        all_inclusion_sources = []
        for target in all_cpp_targets:  # for all C++ targets, populate the variable
            sources = CMakeFileAPI(build_dir).get_sources(target)  # target's sources
            cpp_sources = list(
                filter(lambda source: source.endswith(".cpp"), sources)
            )  # sources ending with .cpp
            all_inclusion_sources += list(
                set(sources) - set(cpp_sources)
            )  # other sources like .h and .hpp files

        self.binding_db = {}  # binding database
        for target in cpp_targets:
            sources = CMakeFileAPI(build_dir).get_sources(target)  # target's sources
            cpp_sources = list(
                filter(lambda source: source.endswith(".cpp"), sources)
            )  # sources ending with .cpp
            inclusion_sources = (
                all_inclusion_sources
                if allow_inclusions_from_other_targets
                else list(set(sources) - set(cpp_sources))
            )  # other sources like .h and .hpp files

            self.binding_db[target] = {
                "source_dir": source_dir,  # source dir containing C++ targets
                "output_dir": output_dir,  # output dir
                "inclusion_sources": inclusion_sources,  # inclusions for the target
                "files": [  # list of files' information
                    {
                        "source": cpp_source,
                        "compiler_arguments": CompilationDatabase(
                            build_dir
                        ).get_compilation_arguments(cpp_source),
                    }
                    for cpp_source in cpp_sources
                ],
            }

    def _parse(self):
        """For all input files, get the parsed tree and update the db."""
        for target in self.binding_db.values():
            source_dir = target.get("source_dir")
            inclusion_sources = [
                str(Path(source_dir, inclusion_source))
                for inclusion_source in target.get("inclusion_sources")
            ]  # string full paths of inclusion sources

            for file in target.get("files"):
                parsed_tree = Parse(
                    Path(source_dir, file.get("source")),
                    inclusion_sources,
                    file.get("compiler_arguments"),
                ).get_tree()

                file.update({"parsed_tree": parsed_tree})  # update db

                # Debugging:
                #
                # - To print the trees:
                # parsed_tree.show()
                #
                # - To save the JSONs:
                # json_output_path = Path(
                #     target.get("output_dir"),
                #     "parsed",
                #     file.get("source").replace(".cpp", ".json"),
                # )
                # json_output_path.parent.mkdir(parents=True, exist_ok=True)
                # parsed_tree.save2file(json_output_path)

    def bind(self):
        """Function to bind the input files."""
        self._parse()

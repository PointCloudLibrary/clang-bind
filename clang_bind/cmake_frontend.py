import json
import clang.cindex as clang
from pathlib import Path


class CompilationDatabase:
    """Class to get information from a CMake compilation database.

    :param build_dir: Build directory path, where compile_commands.json is present.
    :type build_dir: str
    """

    def __init__(self, build_dir):
        self.compilation_database = clang.CompilationDatabase.fromDirectory(
            buildDir=build_dir
        )

    def get_compilation_arguments(self, filename=None):
        """Returns the compilation commands extracted from the compilation database

        :param filename: Get compilation arguments of the file, defaults to None: get for all files
        :type filename: str, optional
        :return: ilenames and their compiler arguments: {filename: compiler arguments}
        :rtype: dict
        """

        if filename:
            # Get compilation commands from the compilation database for the given file
            compilation_commands = self.compilation_database.getCompileCommands(
                filename=filename
            )
        else:
            # Get all compilation commands from the compilation database
            compilation_commands = self.compilation_database.getAllCompileCommands()

        return {
            command.filename: list(command.arguments)[1:-1]
            for command in compilation_commands
        }


class Target:
    """Class to get information about targets found from the CMake file API.

    :param target_file: Target file path.
    :type target_file: str
    """

    def __init__(self, target_file):
        with open(target_file) as f:
            self.target = json.load(f)

    def get_artifacts(self):
        """Get artifacts from the target.

        :return: Artifacts' paths
        :rtype: list
        """
        return [artifact.get("path") for artifact in self.target.get("artifacts", [])]

    def get_commands(self):
        """Get commands from the target.

        :return: Commands concerning the build system.
        :rtype: list
        """
        return self.target.get("backtraceGraph", {}).get("commands")

    def get_compile_groups(self):
        """Get compile groups from the target.

        :return: list of dictionaries of compile groups
        :rtype: list
        """
        return [
            {
                "fragments": [
                    compile_command_fragment.get("fragment")
                    for compile_command_fragment in compile_group.get(
                        "compileCommandFragments", []
                    )
                ],
                "defines": [
                    define.get("define") for define in compile_group.get("defines", [])
                ],
                "includes": [
                    include.get("path") for include in compile_group.get("includes", [])
                ],
                "language": compile_group.get("language"),
            }
            for compile_group in self.target.get("compileGroups", [])
        ]

    def get_dependencies(self):
        """Get dependencies from the target.

        :return: Dependencies ids' list
        :rtype: list
        """
        return [
            dependency.get("id") for dependency in self.target.get("dependencies", [])
        ]

    def get_files(self):
        """Get files from the target.

        :return: Files concerning the build system.
        :rtype: list
        """
        return self.target.get("backtraceGraph", {}).get("files")

    def get_folder(self):
        """Get folder from the target.

        :return: Folder of the target.
        :rtype: str
        """
        return self.target.get("folder", {}).get("name")

    def get_id(self):
        """Get id from the target.

        :return: ID of the target
        :rtype: str
        """
        return self.target.get("id")

    def get_install(self):
        """Get install info from the target.

        :return: Install info
        :rtype: dict
        """
        install = self.target.get("install", {})
        return {
            "destinations": [
                destination.get("path")
                for destination in install.get("destinations", [])
            ],
            "prefix": install.get("prefix", {}).get("path"),
        }

    def get_link(self):
        """Get link info from the target.

        :return: Link info
        :rtype: dict
        """
        link = self.target.get("link", {})
        command_fragments = link.get("commandFragments", [])
        return {
            "flags_fragments": [
                command_fragment.get("fragment")
                for command_fragment in command_fragments
                if command_fragment.get("role") == "flags"
            ],
            "libraries_fragments": [
                command_fragment.get("fragment")
                for command_fragment in command_fragments
                if command_fragment.get("role") == "libraries"
            ],
            "language": link.get("language"),
        }

    def get_name(self):
        """Get name from the target.

        :return: Name of the target
        :rtype: str
        """
        return self.target.get("name")

    def get_name_on_disk(self):
        """Get name on disk from the target.

        :return: Name on disk of the target
        :rtype: str
        """
        return self.target.get("nameOnDisk")

    def get_paths(self):
        """Get paths from the target.

        :return: Paths of the target.
        :rtype: dict
        """
        return self.target.get("paths")

    def get_sources(self):
        """Get sources from the target.

        :return: Sources of the target.
        :rtype: list
        """
        return [sources.get("path") for sources in self.target.get("sources", [])]

    def get_type(self):
        """Get type from the target.

        :return: Type of the target.
        :rtype: str
        """
        return self.target.get("type")


class CMakeFileAPI:
    """CMake File API front end.

    :param build_dir: Build directory path, where .cmake directory is present.
    :type build_dir: str
    """

    def __init__(self, build_dir):
        self.reply_dir = Path(build_dir, ".cmake", "api", "v1", "reply")
        self.targets = {}
        self._set_targets_from_codemodel()

    def _set_targets_from_codemodel(self):
        """Populate targets dict by accessing values in the codemodel file."""

        for file in Path(self.reply_dir).iterdir():  # iterate for all files
            if file.name.startswith("codemodel"):  # find the codemodel file
                codemodel_file = Path(self.reply_dir, file)
                with open(codemodel_file) as f:
                    codemodel = json.load(f)  # load the JSON codemodel

        for configuration in codemodel.get(
            "configurations", []
        ):  # for each configuration
            for target in configuration.get("targets", []):  # for each targets
                target_file = target["jsonFile"]  # get the target file
                target_obj = Target(Path(self.reply_dir, target_file))
                self.targets[target_obj.get_name()] = target_obj

    def get_library_targets(self):
        """Get all library targets' names.

        :return: Library targets.
        :rtype: list
        """
        library_targets_objs = filter(
            lambda target: target.get_type() == "SHARED_LIBRARY", self.targets.values()
        )
        return list(map(lambda target: target.get_name(), library_targets_objs))

    def get_dependencies(self, target):
        """Get dependencies of the target.

        :param target: Target to get the dependencies of.
        :type target: str
        :return: Dependencies of the target.
        :rtype: list
        """
        return list(
            map(lambda x: x.split("::")[0], self.targets.get(target).get_dependencies())
        )

    def get_sources(self, target):
        """Get sources of the target(s).

        :param target: Target to get the sources of.
        :type target: str
        :return: Sources of the target.
        :rtype: list
        """
        return self.targets.get(target).get_sources()

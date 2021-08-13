import json
import clang.cindex as clang
from pathlib import Path


class CompilationDatabase:
    """Class to get information from a CMake compilation database."""

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


class Codemodel:
    """Class to get information about the Codemodel generated by the CMake file API."""

    def __init__(self, reply_dir):
        self.reply_dir = reply_dir
        self.codemodel = {}
        self.codemodel_targets = {}

    def set_codemodel(self, codemodel_file=None):
        """Set the codemodel variable.

        :param codemodel_file: codemodel file to read from, defaults to None
        :type codemodel_file: str, optional
        """
        if not codemodel_file:
            for file in Path(self.reply_dir).iterdir():
                if file.name.startswith("codemodel"):
                    codemodel_file = Path(self.reply_dir, file)
        with open(codemodel_file) as f:
            self.codemodel = json.load(f)

    def get_codemodel(self):
        """Get the codemodel.

        :return: JSON codemodel object.
        :rtype: dict
        """
        if not self.codemodel:
            self.set_codemodel()
        return self.codemodel

    def set_codemodel_targets(self, codemodel=None):
        """Set targets variable.

        :param codemodel: Codemodel dict object, defaults to None
        :type codemodel: dict, optional
        """
        if not codemodel:
            codemodel = self.get_codemodel()
        configurations = codemodel.get("configurations", [])
        for configuration in configurations:
            targets = configuration.get("targets", [])
            for target in targets:
                self.codemodel_targets.update({target["name"]: target["jsonFile"]})

    def get_codemodel_targets(self):
        """Get codemodel targets.

        :return: dict of targets and the corresponding file
        :rtype: dict
        """
        if not self.codemodel_targets:
            self.set_codemodel_targets()
        return self.codemodel_targets


class Target:
    """Class to get information about targets found from the CMake file API."""

    def __init__(self, reply_dir, target_name):
        self.reply_dir = reply_dir
        self.target_file = Codemodel(reply_dir).get_codemodel_targets().get(target_name)
        self.target = {}

    def set_target(self, target_file=None):
        """Set target variable.

        :param target_file: File to get target from, defaults to None
        :type target_file: str, optional
        """
        if not target_file:
            target_file = self.target_file
        with open(Path(self.reply_dir, target_file)) as f:
            self.target = json.load(f)

    def get_target(self):
        """Get target.

        :return: JSON target
        :rtype: dict
        """
        if not self.target:
            self.set_target()
        return self.target

    def get_artifacts(self):
        """Get artifacts from the target.

        :return: Artifacts' paths
        :rtype: list
        """
        return [
            artifact.get("path") for artifact in self.get_target().get("artifacts", [])
        ]

    def get_commands(self):
        """Get commands from the target.

        :return: Commands concerning the build system.
        :rtype: list
        """
        return self.get_target().get("backtraceGraph", {}).get("commands")

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
            for compile_group in self.get_target().get("compileGroups", [])
        ]

    def get_dependencies(self):
        """Get dependencies from the target.

        :return: Dependencies ids' list
        :rtype: list
        """
        return [
            dependency.get("id")
            for dependency in self.get_target().get("dependencies", [])
        ]

    def get_files(self):
        """Get files from the target.

        :return: Files concerning the build system.
        :rtype: list
        """
        return self.get_target().get("backtraceGraph", {}).get("files")

    def get_folder(self):
        """Get folder from the target.

        :return: Folder of the target.
        :rtype: str
        """
        return self.get_target().get("folder", {}).get("name")

    def get_id(self):
        """Get id from the target.

        :return: ID of the target
        :rtype: str
        """
        return self.get_target().get("id")

    def get_install(self):
        """Get install info from the target.

        :return: Install info
        :rtype: dict
        """
        install = self.get_target().get("install", {})
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
        link = self.get_target().get("link", {})
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
        return self.get_target().get("name")

    def get_name_on_disk(self):
        """Get name on disk from the target.

        :return: Name on disk of the target
        :rtype: str
        """
        return self.get_target().get("nameOnDisk")

    def get_paths(self):
        """Get paths from the target.

        :return: Paths of the target.
        :rtype: dict
        """
        return self.get_target().get("paths")

    def get_sources(self):
        """Get sources from the target.

        :return: Sources of the target.
        :rtype: list
        """
        return [sources.get("path") for sources in self.get_target().get("sources", [])]

    def get_type(self):
        """Get type from the target.

        :return: Type of the target.
        :rtype: str
        """
        return self.get_target().get("type")


class CMakeFileAPI:
    """CMake File API front end."""

    def __init__(self, build_dir):
        reply_dir = Path(build_dir, ".cmake", "api", "v1", "reply")
        self.targets = {}
        for codemodel_target in Codemodel(reply_dir).get_codemodel_targets():
            target = Target(reply_dir, codemodel_target)
            self.targets[target.get_name()] = target

    def get_dependencies(self, target=None):
        """Get dependencies of the target(s).

        :param target: Target to get the dependencies, defaults to None
        :type target: str, optional
        :return: Dependencies of the target(s).
        :rtype: dict
        """
        targets = [self.targets.get(target)] if target else self.targets.values()
        return {
            target.get_name(): list(
                map(lambda x: x.split("::")[0], target.get_dependencies())
            )
            for target in targets
        }

    def get_sources(self, target=None):
        """Get sources of the target(s).

        :param target: Target to get the dependencies, defaults to None
        :type target: str, optional
        :return: Sources of the target(s).
        :rtype: dict
        """
        targets = [self.targets.get(target)] if target else self.targets.values()
        return {target.get_name(): target.get_sources() for target in targets}

import os
import json


class Codemodel:
    def __init__(self, reply_dir):
        self.reply_dir = reply_dir
        self.codemodel = {}
        self.codemodel_targets = {}

    def set_codemodel(self, codemodel_file=None):
        if not codemodel_file:
            for file in os.listdir(self.reply_dir):
                if file.startswith("codemodel"):
                    codemodel_file = os.path.join(self.reply_dir, file)
        with open(codemodel_file) as f:
            self.codemodel = json.load(f)

    def get_codemodel(self):
        if not self.codemodel:
            self.set_codemodel()
        return self.codemodel

    def set_codemodel_targets(self, codemodel=None):
        if not codemodel:
            codemodel = self.get_codemodel()
        configurations = codemodel.get("configurations", [])
        for configuration in configurations:
            targets = configuration.get("targets", [])
            for target in targets:
                self.codemodel_targets.update({target["name"]: target["jsonFile"]})

    def get_codemodel_targets(self):
        if not self.codemodel_targets:
            self.set_codemodel_targets()
        return self.codemodel_targets


class Target:
    def __init__(self, reply_dir, target_name):
        self.reply_dir = reply_dir
        self.target_file = Codemodel(reply_dir).get_codemodel_targets().get(target_name)
        self.target = {}

    def set_target(self, target_file=None):
        if not target_file:
            target_file = self.target_file
        with open(os.path.join(self.reply_dir, target_file)) as f:
            self.target = json.load(f)

    def get_target(self):
        if not self.target:
            self.set_target()
        return self.target

    def get_artifacts(self):
        return [
            artifact.get("path") for artifact in self.get_target().get("artifacts", [])
        ]

    def get_commands(self):
        return self.get_target().get("backtraceGraph", {}).get("commands")

    def get_compile_groups(self):
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
        return [
            dependency.get("id")
            for dependency in self.get_target().get("dependencies", [])
        ]

    def get_files(self):
        return self.get_target().get("backtraceGraph", {}).get("files")

    def get_folder(self):
        return self.get_target().get("folder", {}).get("name")

    def get_id(self):
        return self.get_target().get("id")

    def get_install(self):
        install = self.get_target().get("install", {})
        return {
            "destinations": [
                destination.get("path")
                for destination in install.get("destinations", [])
            ],
            "prefix": install.get("prefix", {}).get("path"),
        }

    def get_link(self):
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
        return self.get_target().get("name")

    def get_name_on_disk(self):
        return self.get_target().get("nameOnDisk")

    def get_paths(self):
        return self.get_target().get("paths")

    def get_sources(self):
        return [sources.get("path") for sources in self.get_target().get("sources", [])]

    def get_type(self):
        return self.get_target().get("type")


class CMakeFileAPI:
    def __init__(self, build_dir):
        reply_dir = os.path.join(build_dir, ".cmake", "api", "v1", "reply")
        self.targets = {}
        for codemodel_target in Codemodel(reply_dir).get_codemodel_targets():
            target = Target(reply_dir, codemodel_target)
            self.targets[target.get_name()] = target

    def get_dependencies(self, target=None):
        targets = [self.targets.get(target)] if target else self.targets.values()
        return {
            target.get_name(): list(
                map(lambda x: x.split("::")[0], target.get_dependencies())
            )
            for target in targets
        }

    def get_sources(self, target=None):
        targets = [self.targets.get(target)] if target else self.targets.values()
        return {target.get_name(): target.get_sources() for target in targets}


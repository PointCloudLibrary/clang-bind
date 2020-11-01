#! /usr/bin/env python

import argparse
from functools import lru_cache
import os

from mako.template import Template


def get_args(parser):
    args, _ = parser.parse_known_args()
    return args


def list_by_type(directory):
    from os.path import isfile, isdir, islink, join

    all_files = os.listdir(directory)
    categorized = {
        "file": [f for f in all_files if isfile(join(directory, f))],
        "directory": [d for d in all_files if isdir(join(directory, d))],
        "link": [l for l in all_files if islink(join(directory, l))],
    }
    return categorized


@lru_cache(maxsize=2)
def guess_build_dir(guess=os.getcwd()):
    ls = list_by_type(guess)
    if "compile_commands.json" in ls["file"]:
        return guess
    second_guess = os.path.join(guess, "build")
    if second_guess in ls["directory"]:
        return second_guess
    return None


def guess_project_dir():
    guess = os.getcwd()
    return guess


class CategorizedArgs:
    def __init__(self):
        self._internal_categories = ["cmake", "conan", "project", "pybind11"]
        self._parse_group = {}
        self._parser = None
        self._generate()
        self.args = self._get_args()
        self.categorized_args = {
            category: self._get_args(category) for category in self._internal_categories
        }

    def _cmake(self, parser=argparse.ArgumentParser()):
        parser.add_argument(
            "--cpp-standard",
            required=False,
            default="14",
            choices=["03", "11", "14", "17", "20"],
            help="C++ Standard used by your project",
        )
        parser.add_argument(
            "--no-conan",
            default=False,
            action="store_true",
            help="Use CMake's own package resolution instead of relying on conan",
        )
        return parser

    def _conan(self, parser=argparse.ArgumentParser()):
        parser.add_argument("--keep-rpaths", required=False, action="store_true")
        parser.add_argument("--no-output-dirs", required=False, action="store_true")
        parser.add_argument("--arch", required=False)
        parser.add_argument("--build-type", required=False)
        parser.add_argument("--profile", required=False)
        parser.add_argument("--profile-auto", required=False)
        return parser

    def _pybind11(self, parser=argparse.ArgumentParser()):
        parser.add_argument("--lib-type", required=False)
        parser.add_argument("--thin-lto", required=False, action="store_true")
        parser.add_argument("--optimise-for-size", required=False, action="store_true")
        return parser

    def _project(self, parser=argparse.ArgumentParser()):
        parser.add_argument("--name", required=True)
        return parser

    def _generate(self):
        parser = argparse.ArgumentParser(
            description="Generate bindings from C++",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        parser.add_argument(
            "--compile-commands",
            default=guess_build_dir(),
            required=guess_build_dir() is None,
            help="Path to compile_commands.json file or the directory containing it",
        )
        parser.add_argument(
            "--project-root",
            default=guess_project_dir(),
            help="Path to the project root to reduce name length of generated files",
        )
        parser.add_argument(
            "--out-dir",
            default=guess_build_dir(),
            required=guess_build_dir() is None,
            help="Output directory for intermediate json files",
        )
        parser.add_argument(
            "--select-files",
            nargs="*",
            metavar=("CHOSEN_FILE", "OTHER_CHOSEN_FILES"),
            default=None,
            help="Select only certain files from the compile database",
        )
        parser.add_argument(
            "--ignore-files",
            nargs="*",
            metavar=("IGNORED_FILE", "OTHER_IGNORED_FILES"),
            default=None,
            help="Ignore certain files from the compile database",
        )
        parser.add_argument(
            "--language",
            default="py",
            choices=["py"],
            help="Target language for the bindings",
        )
        parser.add_argument(
            "--use-latest-conan-cmake",
            default=False,
            action="store_true",
            help="Use the latest release of conan-cmake instead of the bundled release (0.15.0)",
        )

        for category in self._internal_categories:
            gp = parser.add_argument_group(title=f"arguments for {category}")
            getattr(self, f"_{category}")(gp)
            # also create categorized parser
            self._parse_group[category] = getattr(self, f"_{category}")()
        self._parser = parser
        return self._parser

    def _get_args(self, category=None):
        if category is None:
            args = get_args(self._parser)
            root, last_item = args.compile_commands.rsplit(os.path.sep, 1)
            if (last_item == "compile_commands.json") and os.path.isfile(
                args.compile_commands
            ):
                args.compile_commands = root
            return args
        elif category in self._internal_categories:
            return get_args(self._parse_group[category])


def main():
    cmake = Template(filename="CMakeLists.txt.in")
    cat = CategorizedArgs()
    all_args = cat.categorized_args
    data = cmake.render(files=[], **(all_args))
    print(data)


if __name__ == "__main__":
    main()

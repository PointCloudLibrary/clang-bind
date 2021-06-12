import clang.cindex as clang


class CompilationDatabase:
    """
    Build a compilation database from a given directory
    """

    def __init__(self, compilation_database_path):
        self.compilation_database = clang.CompilationDatabase.fromDirectory(
            buildDir=compilation_database_path
        )

    def get_compilation_arguments(self, filename=None):
        """
        Returns the compilation commands extracted from the compilation database

        Parameters:
            - compilation_database_path: The path to `compile_commands.json`
            - filename (optional): To get compilaton commands of a file

        Returns:
            - compilation_arguments (dict): {filename: compiler arguments}
        """

        if filename:
            # Get compilation commands from the compilation database for the given file
            compilation_commands = self.compilation_database.getCompileCommands(
                filename=filename
            )
        else:
            # Get all compilation commands from the compilation database
            compilation_commands = self.compilation_database.getAllCompileCommands()

        # {file: compiler arguments}
        compilation_arguments = {
            command.filename: list(command.arguments)[1:-1]
            for command in compilation_commands
        }
        return compilation_arguments

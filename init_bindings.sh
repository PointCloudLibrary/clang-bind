if [ -z "$1" ]; then # if `project_dir` not specified, exit
	echo "Sample usage: ./init_bindings.sh project_dir build_dir"
	echo "No project directory specified, exiting.."
	exit
else
	PROJECT_DIR=$1
fi

if [ -z "$2" ]; then # if `build_dir` not specified, create in `project_dir`
	BUILD_DIR=$PROJECT_DIR/build
	echo "Sample usage: ./init_bindings.sh project_dir build_dir"
	echo "No build directory supplied, creating in project directory.."
	mkdir -p $BUILD_DIR
	echo "Created directory: $BUILD_DIR"
else
	BUILD_DIR=$2
fi

cd $BUILD_DIR
mkdir -p .cmake/api/v1/query && touch .cmake/api/v1/query/codemodel-v2 # create the API directory and query file
cmake $PROJECT_DIR                                                     # CMake should have automatically created the directory ``.cmake/api/v1/reply` containing the replies to our query.

export PROJECT_BUILD_DIR=$BUILD_DIR

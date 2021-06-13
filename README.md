# Description

The clang-bind is a project to generate python bindings for C++ code using clang python bindings and pybind11. 

# Dependencies

**C++**

*libclang*

```
wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | sudo apt-key add -
echo 'deb http://apt.llvm.org/bionic/ llvm-toolchain-bionic-11 main' | sudo tee -a /etc/apt/sources.list
echo 'deb-src http://apt.llvm.org/bionic/ llvm-toolchain-bionic-11 main' | sudo tee -a /etc/apt/sources.list
sudo apt-get update
sudo apt-get install -y libclang-11-dev python3-clang-11
```

**Python**

`pip install -r requirements.txt`

# Demonstration

1. Go to `tests/test_project/` folder
2. Create a build folder
3. Run `cmake ..`
4. Run `make -j$(nproc)`
5. Run `python ../../../clang_bind/parse.py --com ./ ../src/simple.cpp`
6. Run `python ../../../clang_bind/generate.py --com json/src/simple.json`

The binding code will be available in `pybind11-gen/src` folder.


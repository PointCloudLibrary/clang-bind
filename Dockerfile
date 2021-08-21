FROM ubuntu:20.04

WORKDIR /clang-bind
COPY . .

RUN apt-get update -y && apt-get install -y python3-pip libclang-12-dev python3-clang-12

RUN pip install -r requirements.txt

ENTRYPOINT [ "bash" ]

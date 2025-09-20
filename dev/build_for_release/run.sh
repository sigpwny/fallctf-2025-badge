#!/usr/bin/env bash

mkdir -p src

cp ../*.py src
zip -r src.zip src

rm -r src

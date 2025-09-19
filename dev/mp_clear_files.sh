#!/usr/bin/env bash

# clear all files except for main.py and assets/ directory

files_to_keep=("main.py" "assets/")

files=$(mpremote ls : 2> /dev/null | cut -c14- | tr -d '\r')

for file in $files; do
    if [[ ! " ${files_to_keep[@]} " =~ " ${file} " ]]; then
        mpremote rm ":$file"
    fi
done

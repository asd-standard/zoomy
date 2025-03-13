#!/bin/bash


for file in $(ls *_PyQt5.py) ; do
    mv $file "${file:0:${#file}-9}.py"
done

@echo off
mkdir dist
del /F dist\*
python -m py2exe main.py -W setup.py
python setup.py py2exe
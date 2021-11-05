# BT3AnimationWorker
**Budokai Tenkaichi 3 tool to modify animations**

## Features
This tool can:
- Change the speed of an animation
- Join two animations together (one after the other)
- Mix two animations together (import single bone animations from one to another)

## Current state of the project
It is "work in progress"... Let's say a pre-beta... but it should work! :D<br />
Let me know if you find bugs.

## How to download it
You will found pre-packaged ".exe" files for Windows and the source code of major versions in the "release" section as soon as the first major release will be a thing. In the meanwhile, you can clone simply this repository (branch main).

## How to run it
You can run this tool on any platform that supports Python 3. The tool was tested with Python 3.7.<br />
It does not requires any library, but if you want to package it as a ".exe" file for Windows you need **py2exe**.

### How to package the tool as an ".exe" file for Windows using py2exe
This procedure was tested on Windows 10 21H1.<br />
1. Install **py2exe**. With pip3 you can do ```pip3 install py2exe```.
2. Run ```py2exe_script.bat``` in the project root.
3. The output is in the ```dist``` folder.

# Micro / Circuit Python Libraries to Compile

<br/><br/>

This directory contains scripts for compiling the libraries in the `libs_to_compile/lib` directory. Use `Bash` to run the scripts (`Git Bash` if you're on Windows).

<br/><br/>

> [!WARNING]
>
> Remember to make sure the script is executable by running
>
> `chmod +x mpy_compile_all_libs.sh`
>
> or `chmod +x compile_mpy.sh`
>
> (depending on which script you want to run).

<br/><br/>

> [!CAUTION]
>
> Before running any of the scripts, make sure you have the `mpy-cross` command installed.
>
> You can build it yourself following the instructions in the [`micropython/mpy-cross` repository](https://github.com/micropython/micropython/tree/master/mpy-cross) or run `pip install mpy-cross`.
>
> Afterward, update the `MPY_CROSS_PATH` variable in the scripts to point to the location of the `mpy-cross` command.

<br/><br/>

## Checking the CPU architecture

To check the CPU architecture, run the file [`../.BACKUP/architecture_check.py`](../.BACKUP/architecture_check.py) on the Pico. If the desired architecture is not `armv7emsp`, change it in the appropriate script.

<br/><br/>

## Compiling the libraries

<br/><br/>

1. To compile all the libraries included in this repository, run `./mpy_compile_all_libs.sh` in the `libs_to_compile/` directory. This will compile all of the libraries in the `libs_to_compile/lib` directory into `../lib/` (root of the project).

<br/><br/>

2. To compile a specific library / module, edit the `SRC_DIR` and `MPY_DIR` in the `compile_mpy.sh` script and run it `./compile_mpy.sh`.
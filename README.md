# dimacs-irp-verifier

This is a Python script to verify solutions for the IRP track
of the 12th DIMACS Implementation Challenge on Vehicle Routing Problems
http://dimacs.rutgers.edu/programs/challenge/vrp/irp/

Requirements:
 * Python 3

Usage:
 * first argument (required) is the (path to the) instance file
 * second argument (optional) is the directory containing the solution file;
   if omitted, the directory of the instance file is assumed

Examples:
```
$ python3 verify.py
Usage: verify.py <instance file> [<directory containing solution file>]
$ python3 verify.py instances/S_abs5n5_4_L3.dat
Failed to open instance file instances/out_S_abs5n5_4_L3.txt: No such file or directory
$ python3 verify.py instances/S_abs5n5_4_L3.dat solutions
$ # checked solutions/out_S_abs5n5_4_L3.txt based on instances/S_abs5n5_4_L3.dat
```

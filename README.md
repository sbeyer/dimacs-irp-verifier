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

Behavior notes:
 * PassMark data is fetched and saved into the file `processor.json` in the current
   directory whenever that file cannot be found (e.g., on the first run)
 * successful verification is indicated by a message on standard output
   and zero exit code
 * if reading or verification failed, the first error is printed to standard output
   and exit code is non-zero
 * standard error output is kept clean except in case of an unhandled exception

Examples:
```
[ ]$ python3 verify.py
Usage: verify.py <instance file> [<directory containing solution file>]
[✘]$ python3 verify.py instances/S_abs5n5_4_L3.dat
Failed to open solution file instances/out_S_abs5n5_4_L3.txt: No such file or directory
[✘]$ python3 verify.py instances/S_abs5n5_4_L3.dat solutions/algo1
Verification of solutions/algo1/out_S_abs5n5_4_L3.txt successful
[✔]$ python3 verify.py instances/S_abs5n5_4_L3.dat solutions/algo2
solutions/algo2/out_S_abs5n5_4_L3.txt: Time verification error: computation time of 1612.42 seconds exceeds time limit of 1524.13 seconds
[✘]$ python3 verify.py instances/S_abs5n5_4_L3.dat solutions/algo3
solutions/algo3/out_S_abs5n5_4_L3.txt: Solution verification error: Day 3: Route 1: inventory level of customer 4 too high; got 173, expected <= 162
```

Special mode:
 * intention: allow use informational output from a solver in development for
   verification; such a solver might output intermediate solutions
 * the mode is enabled if there is a line beginning with `#` in the solution file
 * `#` lines are printed by the verification tool, but ignored for verification
 * non-`#` lines before the first solution are ignored
 * every solution is checked

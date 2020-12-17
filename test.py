#!/usr/bin/env python3
#
# Tests for DIMACS IRP track solution verifier
#
# Written in 2020 by Stephan Beyer <sbeyer@slashwhy.de>, slashwhy GmbH & Co. KG
#
# To the extent possible under law, the author(s) have dedicated all copyright and
# related and neighboring rights to this software to the public domain worldwide. This
# software is distributed without any warranty.
#
# You should have received a copy of the CC0 Public Domain Dedication along with this
# software. If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.


import os
from verify import handle_arguments, verify

directory = "test"
instance_file = "S_abs5n5_4_L3.dat"
fail_prefix = "fail-"
pass_prefix = "pass-"

instance = os.path.join(directory, instance_file)

all_cases = os.listdir(directory)


def construct_cases(prefix):
    cases = [x for x in all_cases if x.startswith(prefix)]
    cases.sort()
    cases = [
        handle_arguments("verify.py", instance, os.path.join(directory, case))
        for case in cases
    ]
    return cases


fail_cases = construct_cases(fail_prefix)
pass_cases = construct_cases(pass_prefix)

for case in pass_cases:
    assert verify(*case) is True, f"Case {case} should pass"

for case in fail_cases:
    assert verify(*case) is False, f"Case {case} should fail"

print("All tests passed!")

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
from verify import handle_arguments, obtain_passmark_data, verify

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

processors_fetched = obtain_passmark_data()
assert processors_fetched is not None, "Failed to fetch CPU marks"

processors = obtain_passmark_data()
assert processors is not None, "Failed to read CPU marks"
assert (
    processors == processors_fetched
), "Fetched CPU marks differ from CPU marks loaded from file"

for case in pass_cases:
    assert verify(*case, processors) is True, f"Case {case} should pass"

for case in fail_cases:
    assert verify(*case, processors) is False, f"Case {case} should fail"

print("All tests passed!")

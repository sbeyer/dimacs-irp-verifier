#!/usr/bin/env python3
#
# DIMACS IRP track solution verifier
#
# Written in 2020 by Stephan Beyer <sbeyer@slashwhy.de>, slashwhy GmbH & Co. KG
#
# To the extent possible under law, the author(s) have dedicated all copyright and
# related and neighboring rights to this software to the public domain worldwide. This
# software is distributed without any warranty.
#
# You should have received a copy of the CC0 Public Domain Dedication along with this
# software. If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.


def read_instance(fn):
    lines = open(fn, "r").read().splitlines()

    meta_data = lines.pop(0).split()
    (num_nodes, num_days, capacity, num_vehicles) = [int(val) for val in meta_data]

    pos = []
    inventory_start = []
    inventory_change = []
    inventory_max = []
    inventory_min = []
    inventory_cost = []

    depot_data = lines.pop(0).split()
    (_, x, y, *depot_data) = depot_data
    pos.append((float(x), float(y)))
    inventory_start.append(int(depot_data.pop(0)))
    inventory_change.append(int(depot_data.pop(0)))
    inventory_cost.append(float(depot_data.pop(0)))
    inventory_max.append(inventory_start[0] + inventory_change[0] * num_days)
    inventory_min.append(0)

    for line in lines:
        customer_data = line.split()
        (_, x, y, *customer_data) = customer_data
        pos.append((float(x), float(y)))
        inventory_start.append(int(customer_data.pop(0)))
        inventory_max.append(int(customer_data.pop(0)))
        inventory_min.append(int(customer_data.pop(0)))
        inventory_change.append(-int(customer_data.pop(0)))
        inventory_cost.append(float(customer_data.pop(0)))

    print(f"Number of nodes: {num_nodes}")
    print(f"Number of days: {num_days}")
    print(f"Number of vehicles: {num_vehicles}")
    print(f"Vehicle capacity: {capacity}")
    print(f"Positions: {pos}")
    print(f"Inventory start levels: {inventory_start}")
    print(f"Inventory max levels: {inventory_max}")
    print(f"Inventory min levels: {inventory_min}")
    print(f"Inventory cost: {inventory_cost}")
    print(f"Daily level change: {inventory_change}")


fn_instance = "example/S_abs5n5_4_L3.dat"
fn_solution = "example/out_S_abs5n5_4_L3.txt"

read_instance(fn_instance)

print("Solution:")
lines_solution = open(fn_solution, "r").read().splitlines()
for line in lines_solution:
    print(line)

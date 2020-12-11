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


class Instance:
    """Representation of IRP instance data"""

    num_nodes = 0
    num_days = 0
    capacity = 0
    num_vehicles = 0
    pos = []
    inventory_start = []
    inventory_change = []
    inventory_max = []
    inventory_min = []
    inventory_cost = []

    def __init__(self, fn):
        lines = open(fn, "r").read().splitlines()

        meta_data = [int(val) for val in lines.pop(0).split()]
        (self.num_nodes, self.num_days, self.capacity, self.num_vehicles) = meta_data

        depot_data = lines.pop(0).split()
        (_, x, y, *depot_data) = depot_data
        depot_start = int(depot_data.pop(0))
        depot_change = int(depot_data.pop(0))
        self.pos.append((float(x), float(y)))
        self.inventory_start.append(depot_start)
        self.inventory_max.append(depot_start + depot_change * self.num_days)
        self.inventory_min.append(0)
        self.inventory_change.append(depot_change)
        self.inventory_cost.append(float(depot_data.pop(0)))

        for line in lines:
            customer_data = line.split()
            (_, x, y, *customer_data) = customer_data
            self.pos.append((float(x), float(y)))
            self.inventory_start.append(int(customer_data.pop(0)))
            self.inventory_max.append(int(customer_data.pop(0)))
            self.inventory_min.append(int(customer_data.pop(0)))
            self.inventory_change.append(-int(customer_data.pop(0)))
            self.inventory_cost.append(float(customer_data.pop(0)))


fn_instance = "example/S_abs5n5_4_L3.dat"
fn_solution = "example/out_S_abs5n5_4_L3.txt"

instance = Instance(fn_instance)

print(f"Number of nodes: {instance.num_nodes}")
print(f"Number of days: {instance.num_days}")
print(f"Number of vehicles: {instance.num_vehicles}")
print(f"Vehicle capacity: {instance.capacity}")
print(f"Positions: {instance.pos}")
print(f"Inventory start levels: {instance.inventory_start}")
print(f"Inventory max levels: {instance.inventory_max}")
print(f"Inventory min levels: {instance.inventory_min}")
print(f"Inventory cost: {instance.inventory_cost}")
print(f"Daily level change: {instance.inventory_change}")
print()
print("Solution:")
lines_solution = open(fn_solution, "r").read().splitlines()
for line in lines_solution:
    print(line)

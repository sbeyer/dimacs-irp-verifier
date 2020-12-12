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
        """Reads an instance file and initializes Instance members"""
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


class Solution:
    """Representation of IRP solution data"""

    routes = []
    cost_transportation = 0
    cost_inventory_customers = 0.0
    cost_inventory_depot = 0.0
    cost = 0.0
    processor = ""
    time = 0.0

    class ReadError(Exception):
        pass

    def __init__(self, instance, fn):
        """Reads a solution file and initializes Solution members"""
        self.instance = instance

        lines = open(fn_solution, "r").read().splitlines()
        lineno = 0

        for day_idx in range(instance.num_days):
            day = day_idx + 1
            lineno += 1
            line = lines.pop(0)
            data = line.split(" ")
            if len(data) != 2 or data[0] != "Day" or data[1] != str(day):
                raise self.ReadError(
                    f"{fn}:{lineno}: expected 'Day {day}', got '{line}'"
                )

            self.routes.append([])

            for route_idx in range(instance.num_vehicles):
                route = route_idx + 1
                lineno += 1
                line = lines.pop(0)
                data = line.split(": ")
                if len(data) != 2:
                    raise self.ReadError(
                        f"{fn}:{lineno}: expected 'Route {route}: <route>', got '{line}'"
                    )

                left = data[0].split(" ")
                if len(left) != 2 or left[0] != "Route" or left[1] != str(route):
                    raise self.ReadError(
                        f"{fn}:{lineno}: expected 'Route {route}: <route>', got '{line}'"
                    )

                right = data[1].split(" ")
                if len(right) < 3:
                    raise self.ReadError(
                        f"{fn}:{lineno}: route is too short to be valid; use '0 - 0' for an empty route"
                    )
                if right.pop(0) != "0":
                    raise self.ReadError(
                        f"{fn}:{lineno}: route does not start at depot"
                    )
                if right.pop() != "0":
                    raise self.ReadError(f"{fn}:{lineno}: route does not end at depot")
                if right.pop(0) != "-":
                    raise self.ReadError(
                        f"{fn}:{lineno}: expected first node delimiter '-' in route"
                    )

                self.routes[day_idx].append([])

                if len(right) > 0:
                    for idx, token in enumerate(right):
                        mod = idx % 5
                        if mod == 0:
                            try:
                                current = int(token)
                                if current >= instance.num_nodes:
                                    raise self.ReadError(
                                        f"{fn}:{lineno}: customer {current} does not exist"
                                    )
                            except ValueError:
                                raise self.ReadError(
                                    f"{fn}:{lineno}: expected customer in route, got '{token}'"
                                )
                        elif mod == 1:
                            if token != "(":
                                raise self.ReadError(
                                    f"{fn}:{lineno}: expected '(' in route"
                                )
                        elif mod == 2:
                            try:
                                current = (current, int(token))
                            except ValueError:
                                raise self.ReadError(
                                    f"{fn}:{lineno}: expected delivered quantity in route, got '{token}'"
                                )
                        elif mod == 3:
                            if token != ")":
                                raise self.ReadError(
                                    f"{fn}:{lineno}: expected ')' in route"
                                )
                        elif mod == 4:
                            if token != "-":
                                raise self.ReadError(
                                    f"{fn}:{lineno}: expected '-' delimiter in route"
                                )
                            self.routes[day_idx][route_idx].append(current)

                    if len(right) % 5 != 0:
                        raise self.ReadError(
                            f"{fn}:{lineno}: route is invalid, check format!"
                        )

        lineno += 1
        line = lines.pop(0)
        try:
            self.cost_transportation = int(line)
        except ValueError:
            raise self.ReadError(
                f"{fn}:{lineno}: expected total transportation cost, got '{line}'"
            )

        lineno += 1
        line = lines.pop(0)
        try:
            self.cost_inventory_customers = float(line)
        except ValueError:
            raise self.ReadError(
                f"{fn}:{lineno}: expected total inventory cost at customers, got '{line}'"
            )

        lineno += 1
        line = lines.pop(0)
        try:
            self.cost_inventory_depot = float(line)
        except ValueError:
            raise self.ReadError(
                f"{fn}:{lineno}: expected total inventory cost at depot, got '{line}'"
            )

        lineno += 1
        line = lines.pop(0)
        try:
            self.cost = float(line)
        except ValueError:
            raise self.ReadError(
                f"{fn}:{lineno}: expected total solution cost, got '{line}'"
            )

        lineno += 1
        self.processor = lines.pop(0)

        lineno += 1
        line = lines.pop(0)
        try:
            self.time = float(line)
        except ValueError:
            raise self.ReadError(
                f"{fn}:{lineno}: expected solution time in seconds, got '{line}'"
            )

        for line in lines:
            lineno += 1
            if line != "":
                raise self.ReadError(f"{fn} contains junk in line {lineno}")


fn_instance = "example/S_abs5n5_4_L3.dat"
fn_solution = "example/out_S_abs5n5_4_L3.txt"

print("Instance:")
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
solution = Solution(instance, fn_solution)
print(f"Routes: {solution.routes}")
print(f"Total transportation cost: {solution.cost_transportation}")
print(f"Total inventory cost at customers: {solution.cost_inventory_customers}")
print(f"Total inventory cost at depot: {solution.cost_inventory_depot}")
print(f"Total cost: {solution.cost}")
print(f"Used processor: {solution.processor}")
print(f"Time: {solution.time}")

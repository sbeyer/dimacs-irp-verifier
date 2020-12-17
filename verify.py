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

    def __init__(self, handle):
        """Reads an instance from handle and initializes Instance members"""
        self.__init_by_lines(*handle.read().splitlines())

    def __init_by_lines(self, meta_line, depot_line, *customer_lines):
        meta_data = [int(val) for val in meta_line.split()]
        self.num_nodes, self.num_days, self.capacity, self.num_vehicles = meta_data

        self.__init_node_lists_by_depot(*depot_line.split())

        for customer_line in customer_lines:
            self.__append_node_lists_by_customer(*customer_line.split())

    def __init_node_lists_by_depot(self, index, x, y, start, change, cost):
        self.pos = [(float(x), float(y))]
        self.inventory_start = [int(start)]
        self.inventory_max = [int(start) + int(change) * self.num_days]
        self.inventory_min = [0]
        self.inventory_change = [int(change)]
        self.inventory_cost = [float(cost)]

    def __append_node_lists_by_customer(self, index, x, y, start, u, l, change, cost):
        self.pos.append((float(x), float(y)))
        self.inventory_start.append(int(start))
        self.inventory_max.append(int(u))
        self.inventory_min.append(int(l))
        self.inventory_change.append(-int(change))
        self.inventory_cost.append(float(cost))


class Solution:
    """Representation of IRP solution data"""

    class ReadError(Exception):
        pass

    class VerificationError(Exception):
        pass

    def __init__(self, instance, handle):
        """Reads a solution from handle and initializes Solution members"""
        self.instance = instance

        lines = handle.read().splitlines()
        lineno = 0

        def err(error):
            raise self.ReadError(f"{handle.name}:{lineno}: {error}")

        def expect_int(description, value):
            try:
                return int(value)
            except ValueError:
                err(f"expected (integral) {description}, got '{value}'")

        def expect_float(description, value):
            try:
                return float(value)
            except ValueError:
                err(f"expected {description}, got '{value}'")

        def next_line(expected):
            nonlocal lineno
            lineno += 1
            if len(lines) == 0:
                err(f"missing line; expected {expected}")
            return lines.pop(0)

        self.routes = []

        for day_idx in range(instance.num_days):
            day = day_idx + 1
            line = next_line(f"'Day {day}'")
            data = line.split(" ")
            if len(data) != 2 or data[0] != "Day" or data[1] != str(day):
                err(f"expected 'Day {day}', got '{line}'")

            self.routes.append([])

            for route_idx in range(instance.num_vehicles):
                route = route_idx + 1
                line = next_line(f"'Route {route}: <route>'")
                data = line.split(": ")
                if len(data) != 2:
                    err(f"expected 'Route {route}: <route>', got '{line}'")

                left = data[0].split(" ")
                if len(left) != 2 or left[0] != "Route" or left[1] != str(route):
                    err(f"expected 'Route {route}: <route>', got '{line}'")

                right = data[1].split(" ")
                if len(right) < 3:
                    err(
                        "route is too short to be valid; use '0 - 0' for an empty route"
                    )
                if right.pop(0) != "0":
                    err("route does not start at depot")
                if right.pop() != "0":
                    err("route does not end at depot")
                if right.pop(0) != "-":
                    err("expected first node delimiter '-' in route")

                self.routes[day_idx].append([])

                if len(right) > 0:
                    for idx, token in enumerate(right):
                        mod = idx % 5
                        if mod == 0:
                            current = expect_int("customer in route", token)
                            if current >= instance.num_nodes:
                                err(f"customer {current} does not exist")
                        elif mod == 1:
                            if token != "(":
                                err("expected '(' in route")
                        elif mod == 2:
                            current = (
                                current,
                                expect_int("delivered quantity in route", token),
                            )
                        elif mod == 3:
                            if token != ")":
                                err("expected ')' in route")
                        elif mod == 4:
                            if token != "-":
                                err("expected '-' delimiter in route")
                            self.routes[day_idx][route_idx].append(current)

                    if len(right) % 5 != 0:
                        err("route is invalid, check format!")

        expected = "total transportation cost"
        line = next_line(expected)
        self.cost_transportation = expect_int(expected, line)

        expected = "total inventory cost at customers"
        line = next_line(expected)
        self.cost_inventory_customers = expect_float(expected, line)

        expected = "total inventory cost at depot"
        line = next_line(expected)
        self.cost_inventory_depot = expect_float(expected, line)

        expected = "total solution cost"
        line = next_line(expected)
        self.cost = expect_float(expected, line)

        self.processor = next_line("processor")

        expected = "solution time in seconds"
        line = next_line(expected)
        self.time = expect_float(expected, line)

        for line in lines:
            lineno += 1
            if line != "":
                err(f"line contains unexpected junk '{line}', no more data expected")

    def verify_solution(self):
        """Verifies the solution or raises a VerificationError"""

        def err(error):
            raise self.VerificationError(f"Solution verification error: {error}")

        def expect_equal(description, expected, actual):
            if expected != actual:
                err(f"{description}: expected {expected}, got {actual}")

        def expect_equal_float(description, expected, actual):
            """Compare expected and actual float by its string representation with 2 decimal places"""
            expected_formatted = "{:.2f}".format(expected)
            actual_formatted = "{:.2f}".format(actual)
            expect_equal(description, expected_formatted, actual_formatted)

        def rounded_distance(s, t):
            """Returns the Euclidean distance between s and t, rounded to integer"""
            import math

            s_x, s_y = self.instance.pos[s]
            t_x, t_y = self.instance.pos[t]
            return int(math.sqrt((s_x - t_x) ** 2 + (s_y - t_y) ** 2) + 0.5)

        inventory = self.instance.inventory_start.copy()
        cost_transportation = 0
        node_names = ["depot"] + [
            f"customer {i}" for i in range(1, self.instance.num_nodes + 1)
        ]
        cost_inventory = [0.0 for x in node_names]
        day_names = [f"Day {d + 1}" for d in range(self.instance.num_days)]
        route_names = [f"Route {r + 1}" for r in range(self.instance.num_vehicles)]

        # this should never happen, because it means the instance is invalid, not the solution
        # but we still check for it:
        for i, level in enumerate(inventory):
            if level < self.instance.inventory_min[i]:
                err(
                    f"Start inventory level of {node_names[i]} < minimum inventory level"
                )
            if level > self.instance.inventory_max[i]:
                err(
                    f"Start inventory level of {node_names[i]} > maximum inventory level"
                )

        for d, day in enumerate(day_names):
            # compute route costs
            for route in self.routes[d]:
                tour = [0] + [x for x, _ in route] + [0]
                for s, t in zip(tour[:-1], tour[1:]):
                    cost_transportation += rounded_distance(s, t)

            # each customer receives at most one delivery
            customer_deliveries = [0 for _ in node_names]
            for route in self.routes[d]:
                for customer, _ in route:
                    customer_deliveries[customer] += 1
            for customer, delivery in enumerate(customer_deliveries):
                if delivery > 1:
                    err(
                        f"{day}: {node_names[customer]} is delivered {delivery} times, expected <= 1"
                    )

            # check capacity and update depot level
            for r, route in enumerate(self.routes[d]):
                volume = sum([x for _, x in route])
                inventory[0] -= volume
                if volume > self.instance.capacity:
                    err(
                        f"{day}: {route_names[r]}: Capacity is exceeded: got {volume}, expected <= {self.instance.capacity}"
                    )

            # update inventories by delivery and check upper level limit
            for r, route in enumerate(self.routes[d]):
                for customer, delivery in route:
                    inventory[customer] += delivery
                    if inventory[customer] > self.instance.inventory_max[customer]:
                        err(
                            f"{day}: {route_names[r]}: {node_names[customer]} is delivered {delivery} units, new level is {inventory[customer]}, expecting <= {self.instance.inventory_max[customer]}"
                        )

            # update inventories by daily change and check lower level limit
            for i, change in enumerate(self.instance.inventory_change):
                inventory[i] += change
                if inventory[i] < self.instance.inventory_min[i]:
                    err(
                        f"{day}: new level of {node_names[i]} becomes {inventory[i]} units, expecting >= {self.instance.inventory_min[i]}"
                    )

            # update inventory costs
            for i, cost in enumerate(self.instance.inventory_cost):
                cost_inventory[i] += cost * inventory[i]

        expect_equal(
            "total transportation cost", cost_transportation, self.cost_transportation
        )

        expect_equal_float(
            "total inventory cost at customers",
            cost_inventory[0],
            self.cost_inventory_customers,
        )
        expect_equal_float(
            "total inventory cost at depot",
            sum(cost_inventory[1:]),
            self.cost_inventory_depot,
        )
        expect_equal_float(
            "total cost", cost_transportation + sum(cost_inventory), self.cost
        )

    def verify_time(self, processors):
        """Verifies the processor/time part of the Solution or raises a VerificationError"""

        def err(error):
            raise self.VerificationError(f"Time verification error: {error}")

        if self.processor not in processors:
            err(f"processor '{self.processor}' is unknown")

        mark = processors[self.processor]
        scaling_factor = 2000 / mark
        base_timelimit = 30 * 60  # 30 minutes in seconds
        timelimit = scaling_factor * base_timelimit

        if self.time > timelimit:
            err(
                f"computation time of {self.time} seconds exceeds time limit of {timelimit:.2f} seconds"
            )


def handle_arguments(script, instance_path=None, solution_dir=None, remaining=None):
    import os

    if instance_path is None or remaining is not None:
        print(f"Usage: {script} <instance file> [<directory containing solution file>]")
        return None, None

    instance_dir, instance_file = os.path.split(instance_path)
    instance_file_base, instance_file_ext = os.path.splitext(instance_file)
    solution_file = f"out_{instance_file_base}.txt"
    if solution_dir is None:
        solution_dir = instance_dir
    solution_path = os.path.join(solution_dir, solution_file)

    return instance_path, solution_path


def fetch_passmark_data():
    import urllib.request

    url = "https://www.cpubenchmark.net/singleThread.html"
    prod_start = b'<span class="prdname">'
    prod_end = b"</span>"
    score_start = b'<span class="count">'
    score_end = b"</span>"

    print(f" -> Fetching {url}...")

    response = urllib.request.urlopen(url)
    data = response.read()

    print(" -> Got it! Now parsing...")

    processors = {}

    while True:
        start = data.find(prod_start)
        if start < 0:
            break
        data = data[start + len(prod_start) :]
        end = data.find(prod_end)
        prodname = data[:end].decode()
        data = data[end + len(prod_end) :]

        start = data.find(score_start)
        data = data[start + len(score_start) :]
        end = data.find(score_end)
        score = int(data[:end].replace(b",", b""))
        data = data[end + len(score_end) :]

        processors[prodname] = score

    print(" -> Good! I have the necessary processor information now!")
    print("")

    return processors


def obtain_passmark_data():
    import json

    fn_passmark = "processors.json"

    try:
        with open(fn_passmark, "r") as infile_passmark:
            processors = json.load(infile_passmark)
    except Exception as err:
        print(f"Failed to read file {fn_passmark} with processor information: {err}")
        try:
            processors = fetch_passmark_data()
        except Exception as err:
            print(f"Failed to fetch data from server: {err}")
            return None

        try:
            with open(fn_passmark, "w") as outfile_passmark:
                json.dump(processors, outfile_passmark, indent=4)
        except:
            print(f"Failed to save fetched data to {fn_passmark}")

    return processors


def verify(fn_instance, fn_solution, processors):
    def fail(error):
        print(error)
        return False

    try:
        instance = open(fn_instance, "r")
    except OSError as err:
        return fail(f"Failed to open instance file {fn_instance}: {err.strerror}")
    except Exception as err:
        return fail(f"Failed to open instance file {fn_instance}: {err}")

    try:
        solution = open(fn_solution, "r")
    except OSError as err:
        return fail(f"Failed to open solution file {fn_solution}: {err.strerror}")
    except Exception as err:
        return fail(f"Failed to open solution file {fn_solution}: {err}")

    try:
        instance = Instance(instance)
    except Exception as err:
        return fail(f"Failed to read instance file {fn_instance}: {err}")

    try:
        solution = Solution(instance, solution)
    except Solution.ReadError as err:
        return fail(f"Read error {err}")

    try:
        solution.verify_solution()
        solution.verify_time(processors)
    except Solution.VerificationError as err:
        return fail(err)

    return True


if __name__ == "__main__":
    import sys

    fn_instance, fn_solution = handle_arguments(*sys.argv)
    if fn_instance is None or fn_solution is None:
        sys.exit(1)

    processors = obtain_passmark_data()
    if processors is None:
        sys.exit(2)

    if verify(fn_instance, fn_solution, processors) is False:
        sys.exit(2)

    print(f"Verification of {fn_solution} successful")

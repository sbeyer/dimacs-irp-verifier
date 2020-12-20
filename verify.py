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

        # auxiliary lists for fast access to names
        self.nodes = ["depot"] + [f"customer {i}" for i in range(1, self.num_nodes + 1)]
        self.days = [f"Day {d + 1}" for d in range(self.num_days)]
        self.routes = [f"Route {r + 1}" for r in range(self.num_vehicles)]

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

    class Error(Exception):
        pass

    class ReadError(Error):
        pass

    class VerificationError(Error):
        pass

    def __init__(self, instance, handle):
        """Reads a solution from handle and initializes Solution members"""
        self.instance = instance

        lines = handle.read().splitlines()
        lineno = 0

        def err(error):
            raise self.ReadError(f"Read error on line {lineno}: {error}")

        def err_expected(expected_str, actual):
            if actual is None:
                err(f"missing {expected_str}")
            else:
                err(f"expected {expected_str}, got '{actual}'")

        def next_line(expected):
            nonlocal lineno
            lineno += 1
            if len(lines) == 0:
                err(f"missing line; expected {expected}")
            return lines.pop(0)

        def parse_int(description, value):
            try:
                return int(value)
            except ValueError:
                err_expected(f"(integral) {description}", value)

        def parse_int_line(description):
            line = next_line(description)
            return parse_int(description, line)

        def parse_float(description, value):
            try:
                return float(value)
            except ValueError:
                err_expected(description, value)

        def parse_float_line(description):
            line = next_line(description)
            return parse_float(description, line)

        def check_expected(actual, expected, info=None):
            if actual != expected:
                info_str = "" if info is None else f" {info}"
                err_expected(f"'{expected}'{info_str}", actual)

        def expect_day_line(d):
            day = self.instance.days[d]
            line = next_line(f"'{day}'")
            check_expected(line, day)

        def expect_route_line(r):
            route = self.instance.routes[r]
            line = next_line(f"'{route}: <route>'")
            data = line.split(": ")
            if len(data) != 2 or data[0] != route:
                err_expected(f"'{route}: <route>'", line)

            return data[1]

        def parse_route(start_zero=None, start_dash=None, *route):
            def parse_remaining_route(
                customer_str=None,
                open_par=None,
                quantity_str=None,
                close_par=None,
                dash=None,
                *remaining,
            ):
                if open_par is None:
                    if customer_str == "0":
                        return []
                    else:
                        err_expected("depot (0) at end of route", customer_str)

                customer = parse_int("customer in route", customer_str)
                if customer >= self.instance.num_nodes:
                    err(f"customer {customer} does not exist")
                check_expected(open_par, "(", info="in route")
                quantity = parse_int("delivered quantity in route", quantity_str)
                check_expected(close_par, ")", info="in route")
                check_expected(dash, "-", info="delimiter in route")
                return [(customer, quantity)] + parse_remaining_route(*remaining)

            if start_dash is None:
                err("route is too short to be valid; use '0 - 0' for an empty route")
            if start_zero != "0":
                err("route does not start at depot")
            if start_dash != "-":
                err("expected first node delimiter '-' in route")

            return parse_remaining_route(*route)

        def parse_routes():
            routes = []

            for r in range(self.instance.num_vehicles):
                route = expect_route_line(r).split(" ")
                route = parse_route(*route)
                routes.append(route)

            return routes

        def parse_days_with_routes():
            all_routes = []

            for d in range(self.instance.num_days):
                expect_day_line(d)
                routes = parse_routes()
                all_routes.append(routes)

            return all_routes

        self.routes = parse_days_with_routes()
        self.cost_transportation = parse_int_line("total transportation cost")
        self.cost_inventory_customers = parse_float_line(
            "total inventory cost at customers"
        )
        self.cost_inventory_depot = parse_float_line("total inventory cost at depot")
        self.cost = parse_float_line("total solution cost")
        self.processor = next_line("processor")
        self.time = parse_float_line("solution time in seconds")

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
        cost_inventory = [0.0 for x in self.instance.nodes]

        # this should never happen, because it means the instance is invalid, not the solution
        # but we still check for it:
        for i, level in enumerate(inventory):
            if level < self.instance.inventory_min[i]:
                err(
                    f"Start inventory level of {self.instance.nodes[i]} < minimum inventory level"
                )
            if level > self.instance.inventory_max[i]:
                err(
                    f"Start inventory level of {self.instance.nodes[i]} > maximum inventory level"
                )

        for d, day in enumerate(self.instance.days):
            # compute route costs
            for route in self.routes[d]:
                tour = [0] + [x for x, _ in route] + [0]
                for s, t in zip(tour[:-1], tour[1:]):
                    cost_transportation += rounded_distance(s, t)

            # each customer receives at most one delivery
            customer_deliveries = [0 for _ in self.instance.nodes]
            for route in self.routes[d]:
                for customer, _ in route:
                    customer_deliveries[customer] += 1
            for customer, delivery in enumerate(customer_deliveries):
                if delivery > 1:
                    err(
                        f"{day}: {self.instance.nodes[customer]} is delivered {delivery} times, expected <= 1"
                    )

            # check capacity, update depot level and check depot lower level limit
            for r, route in enumerate(self.routes[d]):
                volume = sum([x for _, x in route])
                if volume > self.instance.capacity:
                    err(
                        f"{day}: {self.instance.routes[r]}: Capacity is exceeded: got {volume}, expected <= {self.instance.capacity}"
                    )

                inventory[0] -= volume
                if inventory[0] < self.instance.inventory_min[0]:
                    err(
                        f"{day}: {self.instance.routes[r]}: new level of {self.instance.nodes[0]} becomes {inventory[0]} units, expected >= {self.instance.inventory_min[0]}"
                    )

            # update inventories by delivery and check upper level limit
            for r, route in enumerate(self.routes[d]):
                for customer, delivery in route:
                    inventory[customer] += delivery
                    if inventory[customer] > self.instance.inventory_max[customer]:
                        err(
                            f"{day}: {self.instance.routes[r]}: {self.instance.nodes[customer]} is delivered {delivery} units, new level is {inventory[customer]}, expected <= {self.instance.inventory_max[customer]}"
                        )

            # update inventories by daily change and check lower level limit
            for i, change in enumerate(self.instance.inventory_change):
                inventory[i] += change
                if inventory[i] < self.instance.inventory_min[i]:
                    err(
                        f"{day}: new level of {self.instance.nodes[i]} becomes {inventory[i]} units, expected >= {self.instance.inventory_min[i]}"
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
        solution.verify_solution()
        solution.verify_time(processors)
    except Solution.Error as err:
        return fail(f"{fn_solution}: {err}")

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

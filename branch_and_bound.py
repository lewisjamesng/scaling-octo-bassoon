
from bisect import bisect_left
import csv
from tqdm import tqdm
import json

node_type_to_time_2 = {
    'vii': 21.2065,
    'blur': 6.0243,
    'night': 24.6639,
    'onnx': 3.9967,
    'emboss': 2.1879,
    'muse': 16.6702,
    'wave': 12.6958,
}

node_type_to_time_3 = {
    'vii': 21,
    'blur': 6,
    'night': 25,
    'onnx': 4,
    'emboss': 2,
    'muse': 17,
    'wave': 13,
}

def read_data(question_number=2):
    with open('input.json') as file:
        data = json.load(file)
    
        name_to_id = {}
        id_to_name = {}

        due_dates = {}
        node_times = {}
        
        i = 1

        for name, date in (data['workflow_0']['due_dates'].items()):
            type = name.split('_')[0]

            name_to_id[name] = i
            id_to_name[i] = name

            if question_number == 2:
                node_times[i] = node_type_to_time_2[type]
            else:
                node_times[i] = node_type_to_time_3[type]
            due_dates[i] = date

            i+= 1
        

        precedences = {}
        dependencies = {}

        for (node1, node2) in data['workflow_0']['edge_set']:

            if name_to_id[node1] not in precedences:
                precedences[name_to_id[node1]] = set()
            precedences[name_to_id[node1]].add(name_to_id[node2])

            if name_to_id[node2] not in dependencies:
                dependencies[name_to_id[node2]] = set()
            dependencies[name_to_id[node2]].add(name_to_id[node1])

        precedences[31] = set()
        dependencies[30] = set()
            
    return due_dates, node_times, precedences, dependencies, id_to_name

def write_to_file(id_to_name, best_solution):
    with open ('output_schedule.json', 'w') as out:
        json.dump([id_to_name[x] for x in best_solution], out)
    with open ('output_schedule.csv', 'w') as out:
        writer = csv.writer(out)
        writer.writerow(best_solution)   

def calculate_tardiness(sequence, due_dates, node_times):
    t = sum(node_times.values())
    n = len(sequence)

    tardiness = [0] * n
    for i in range(n):
        x = sequence[i]
        tardiness[i] = max(0, t - due_dates[x])
        t -= node_times[x]
    return sum(tardiness)

def get_new_available(available, next, precedences, sequence, dependencies):
    new_available = available.copy()
    new_available.remove(next)

    new_available = new_available.union(dependencies[next])
    
    seen_set = set(sequence)
    n = -1
    while n != len(new_available):
        n = len(new_available)
        iter = new_available.copy()
        for node in iter:
            if not seen_set.issuperset(precedences[node]):
                new_available.remove(node)
    return new_available

def calculate_heuristic(sequence, due_dates, precedences, dependencies, node_times, new_available):
    best_solution = sequence.copy()
    while len(best_solution) != 31:

        next_min = list(new_available)[0]
        date_min = due_dates[next_min]

        for next in new_available:
            if date_min > due_dates[next]:
                date_min = due_dates[next]
                next_min = next

        best_solution.append(next_min)
        new_available = get_new_available(new_available, next_min, precedences, best_solution, dependencies)

    return best_solution, calculate_tardiness(best_solution, due_dates, node_times)

# 30k iterations - Q2-665.2461, Q3-659
# converges in 36913 iterations - Q2-541.9018, Q3-542
def branch_and_bound_beam_node_priorities(due_dates, precedences, dependencies, node_times, id_to_name):
    # we start from the end and work backwards
    available = set()
    available.add(31)

    bounds = [([], available, 0)]
    bounds_keys = [0]

    for iterations in tqdm(range(40000)):
        (best_solution, available, _ ) = bounds[0]
        del(bounds[0])
        del(bounds_keys[0])
        
        # our lower bound is a full solution
        if len(available) == 0:
            tardiness = calculate_tardiness(best_solution, due_dates, node_times)
            best_solution.reverse()
            return best_solution, tardiness

        subproblems = []
        subproblem_keys = []

        # check all next available jobs
        for next in available:        

            sequence = best_solution.copy()
            sequence.append(next)

            new_available = get_new_available(available, next, precedences, sequence, dependencies)
        
            item = (sequence, new_available, calculate_tardiness(sequence, due_dates, node_times))

            _, key = calculate_heuristic(sequence, due_dates, precedences, dependencies, node_times, new_available)

            index = bisect_left(subproblem_keys, key)

            subproblem_keys.insert(index, key)
            subproblems.insert(index, item)

        # select best 3 heuristic values in each subtree
        size = min(len(subproblems), 3)
        for i in range(size):
            index = bisect_left(bounds_keys, subproblems[i][2])

            bounds_keys.insert(index, subproblems[i][2])
            bounds.insert(index, subproblems[i])


    # heuristic if we run out of iterations
    best_solution, available, _ = bounds[0]

    best_solution, tardiness = calculate_heuristic(best_solution, due_dates, precedences, dependencies, node_times, available)
    best_solution.reverse()

    write_to_file(id_to_name, best_solution)
    
    return best_solution, tardiness

# 30k iterations - Q2-733.5371, Q3-675
# converged in 76470 iterations - Q2-541.9018, Q3-542
def branch_and_bound(due_dates, precedences, dependencies, node_times, id_to_name):
    available = set()

    available.add(31)

    bounds = [([], available, 0)]
    bounds_keys = [0]

    for iterations in tqdm(range(40000)):
        (best_solution, available, _ ) = bounds[0]
        del(bounds[0])
        del(bounds_keys[0])
        
        # our lower bound is a full solution
        if len(available) == 0:
            tardiness = calculate_tardiness(best_solution, due_dates, node_times)
            best_solution.reverse()
            return best_solution, tardiness

        for next in available:        

            sequence = best_solution.copy()
            sequence.append(next)

            new_available = get_new_available(available, next, precedences, sequence, dependencies)

            item = (sequence, new_available, calculate_tardiness(sequence, due_dates, node_times))
            key = item[2]

            index = bisect_left(bounds_keys, key)

            bounds_keys.insert(index, key)
            bounds.insert(index, item)

    # heuristic if we run out of iterations
    best_solution, available, _ = bounds[0]

    best_solution, tardiness = calculate_heuristic(best_solution, due_dates, precedences, dependencies, node_times, available)
    best_solution.reverse()

    write_to_file(id_to_name, best_solution)

    return best_solution, tardiness
    
    


from bisect import bisect_left
import csv
from tqdm import tqdm
import json

node_type_to_time = {
    'vii': 21.2065,
    'blur': 6.0243,
    'night': 24.6639,
    'onnx': 3.9967,
    'emboss': 2.1879,
    'muse': 16.6702,
    'wave': 12.6958,
}


node_type_to_time_b = {
    'vii': 21,
    'blur': 6,
    'night': 25,
    'onnx': 4,
    'emboss': 2,
    'muse': 17,
    'wave': 13,
}

def read_data():
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

            node_times[i] = node_type_to_time[type]
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

def branch_and_bound(due_dates, precedences, dependencies, node_times, id_to_name):
    available = set()

    available.add(31)

    bounds = [([], available, 0)]
    bounds_keys = [0]

    for iterations in tqdm(range(100000)):
        (best_solution, available, _ ) = bounds[0]
        del(bounds[0])
        del(bounds_keys[0])
        
        # our lower bound is a full solution
        if len(best_solution) == 31:
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

    while len(best_solution) != 31:

        next_min = list(available)[0]
        date_min = due_dates[next_min]

        for next in available:
            if date_min > due_dates[next]:
                date_min = due_dates[next]
                next_min = next

        best_solution.append(next_min)
        available = get_new_available(available, next_min, precedences, best_solution, dependencies)

    tardiness = calculate_tardiness(best_solution, due_dates, node_times)
    best_solution.reverse()

    with open ('output_schedule.json', 'w') as out:
        json.dump([id_to_name[x] for x in best_solution], out)
    with open ('output_schedule.csv', 'w') as out:
        writer = csv.writer(out)
        writer.writerow(best_solution)
    

    return best_solution, tardiness
    
    

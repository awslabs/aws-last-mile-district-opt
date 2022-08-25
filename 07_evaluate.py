"""
This module is adapted from the OR-tools code snippet example
    Simple Travelling Salesperson Problem (TSP) between cities.
https://developers.google.com/optimization/routing/tsp

Under the Apache 2.0 License. 
"""

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import numpy as np
from tqdm import tqdm
import glob
import argparse


def create_data_model(dmatrix):
    """Stores the data for the problem."""
    data = {}
    data['distance_matrix'] = dmatrix
    data['num_vehicles'] = 1
    data['depot'] = 0
    return data


def print_solution(manager, routing, solution):
    """Prints solution on console."""
    #print('Objective: {} miles'.format(solution.ObjectiveValue()))
    ret = [0]
    index = routing.Start(0)
    #plan_output = 'Route for vehicle 0:\n'
    route_distance = 0
    while not routing.IsEnd(index):
        #plan_output += ' {} ->'.format(manager.IndexToNode(index))
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        route_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
        #print(manager.IndexToNode(index))
        ret.append(int(index))
        
    return route_distance #,ret[:-1]


def run_ortools(matrix):
    """Entry point of the program."""
    # Instantiate the data problem.
    data = create_data_model(matrix)

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'], data['depot'])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)


    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if solution:
        return print_solution(manager, routing, solution)
    else:
        raise Exception('cannot solve it')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default="data", help="data directory for raw and intermediate datasets")
    args = parser.parse_args()
    DATA_DIR = args.data_dir
    matrix_dir = 'sol'
    #matrix_dir = 'polygon'
    flist = glob.glob(f'{DATA_DIR}/tsp_dist_matrix/{matrix_dir}/*.npy')
    total_time = 0
    total_count = 0
    tt = []
    for fn in tqdm(flist):
        fmatrix = np.load(fn).astype(np.int32)
        ttt = run_ortools(fmatrix)
        total_time += ttt
        tt.append(ttt)
        total_count += 1
    
    print(total_time, total_count, total_time / total_count)
    print(tt)
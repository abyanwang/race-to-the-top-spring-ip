import os
import math
import numpy as np
import pandas as pd
from docplex.mp.model import Model
from collections import defaultdict
import concurrent.futures
import hashlib

from R2TAlgorithmMulti import R2TAlgorithm,run_single_exp,get_seeds_run_config


# def run_single_exp(config):
#     al = R2TAlgorithm(config['path'], gsq=config['gsq'], beta=config['beta'], epsilon=config['eps'], type_="multi")
#     al.load_csv_multi(config['path'])
#     al.id_2_uk_list()
#     best_tau, result = al.race_to_the_top()
    
#     return result, al.result


if __name__ == "__main__":
    gsq_config = [1e4, 1e5, 1e6, 1e7]
    scale = "1.0"
    input_base_path = "./query/count_query_output_q5_scale_"

    for gsq in gsq_config:
        tmp_path = input_base_path + scale + ".csv"

        run_config = {'path': tmp_path, 'gsq': gsq, 'beta': 0.1, 'eps': 0.8}
        
        total_runs = 100
    

        run_configs = get_seeds_run_config(run_config=run_config, total_runs=total_runs)
        
        with concurrent.futures.ProcessPoolExecutor() as executor:
            raw_results = list(executor.map(run_single_exp, run_configs))
        
        if not raw_results:
            continue

        original_result = raw_results[0][1] 

        error_list = []
        for dp_res, true_res in raw_results:
            abs_err = abs(dp_res - true_res)
            error_list.append((abs_err, dp_res))
        
        error_list.sort(key=lambda x: x[0])
    
        report_list = error_list[20: -20]

        abs_errors = [item[0] for item in report_list]
        final_avg_abs_error = sum(abs_errors) / len(abs_errors)
        
        #relative error
        final_avg_rel_error = final_avg_abs_error / original_result
        
        print(f"Test GSq: {gsq}")
        print(f"Original Total: {original_result}")
        print(f"Extract List: {len(report_list)}")
        print(f"Abs Error: {final_avg_abs_error:.2f}")
        print(f"Relative Error: {final_avg_rel_error:.2%}\n")
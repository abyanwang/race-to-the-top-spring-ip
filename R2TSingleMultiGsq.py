import os
import math
import numpy as np
import pandas as pd
from docplex.mp.model import Model
from collections import defaultdict
import concurrent.futures

from database import config
from R2TAlgorithmSingle import R2TAlgorithmSingle,run_single_exp_single
from R2TAlgorithmMulti import get_seeds_run_config


# def run_single_exp(config):
#     al = R2TAlgorithmSingle(config['path'], gsq=config['gsq'], beta=config['beta'], epsilon=config['eps'], type_="single")
#     al.load_csv_single(config['path'])
#     al.id_2_uk_list()
#     best_tau, result = al.race_to_the_top()
#     # print(best_tau)
    
#     return result, al.result


if __name__ == "__main__":
    input_path = "./query/count_query_output_q3_scale_"

    gsq_config = [1e4, 1e5, 1e6, 1e7]
    scale = "1.0"

    for gsq in gsq_config:
        tmp_path =  input_path + scale + ".csv"
        run_config = {'path': tmp_path, 'gsq': gsq, 'beta': 0.1, 'eps': 0.8}
        total_runs = 100 

        run_configs = get_seeds_run_config(run_config, total_runs)
        
        with concurrent.futures.ProcessPoolExecutor() as executor:
            raw_results = list(executor.map(run_single_exp_single, run_configs))
        
        original_result = raw_results[0][1] 

        error_list = []
        for dp_res, true_res in raw_results:
            abs_err = abs(dp_res - true_res)
            error_list.append((abs_err, dp_res))
        
        # 按照误差排序
        error_list.sort(key=lambda x: x[0])
        
        extract_list = error_list[20:-20]

        # 绝对误差
        abs_errors = [item[0] for item in extract_list]
        final_avg_abs_error = sum(abs_errors) / len(abs_errors)
        
        # 相对误差
        final_avg_rel_error = final_avg_abs_error / original_result 

        print(f"Test GSq: {gsq}")
        print(f"Original Total: {original_result}")
        print(f"Extract List: {len(extract_list)}")
        print(f"Abs Error: {final_avg_abs_error:.2f}")
        print(f"Relative Error: {final_avg_rel_error:.2%}\n")
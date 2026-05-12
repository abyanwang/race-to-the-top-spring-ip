import os
import math
import numpy as np
import pandas as pd
from docplex.mp.model import Model
from collections import defaultdict
import concurrent.futures

from database import config

class R2TAlgorithm:
    def __init__(self, input_file_path, gsq, beta, epsilon, type_):
        self.input_file_path = input_file_path
        self.global_sen = gsq
        self.beta = beta
        self.epsilon = epsilon
        self.type = type_

        self.result = 0.0
        self.dataframe = None
        self.k_cj_I = None
    
    def naive_tau(self, tau):
        return self.dataframe['cnt'].map(lambda x : min(x, tau)).sum()
    
    def load_csv_single(self, input_file_path):
        dataframe = pd.read_csv(input_file_path)

        self.result = dataframe['cnt'].sum()
        self.dataframe = dataframe

    def race_to_the_top(self):
        base = 2

        log_gsq = math.ceil(math.log(self.global_sen, base))
        if log_gsq < 0:
            log_gsq = 0

        max_res1 = -math.inf
        best_tau = -1

        for i in range(1, log_gsq + 1):
            tau = math.pow(base, i)
            
            q_tau = self.naive_tau(tau)
            
            noise_scale = log_gsq * tau / self.epsilon
            noise = np.random.laplace(loc=0.0, scale=noise_scale)
            
            penalty = log_gsq * math.log(log_gsq / self.beta) * (tau / self.epsilon)
            
            t_res2 = q_tau + noise - penalty

            if t_res2 > max_res1:
                max_res1 = t_res2
                best_tau = tau

        return best_tau, max(0, max_res1)


def run_single_exp(config):
    al = R2TAlgorithm(config['path'], gsq=config['gsq'], beta=config['beta'], epsilon=config['eps'], type_="multi")
    al.load_csv_single(config['path'])
    best_tau, result = al.race_to_the_top()
    
    return result, al.result


if __name__ == "__main__":
    input_path = "./query/sum_query_output_q3_scale_"

    for scale, settings in config.items():
        tmp_path =  input_path + scale + ".csv"
        run_config = {'path': tmp_path, 'gsq': 1e6, 'beta': 0.1, 'eps': 0.8}
        total_runs = 100 
        
        with concurrent.futures.ProcessPoolExecutor() as executor:
            raw_results = list(executor.map(run_single_exp, [run_config] * total_runs))
        
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

        print("Test scale: "+ scale)
        print(f"Original Total: {original_result}")
        print(f"Extract List: {len(extract_list)}")
        print(f"Abs Error: {final_avg_abs_error:.2f}")
        print(f"Relative Error: {final_avg_rel_error:.2%}\n")
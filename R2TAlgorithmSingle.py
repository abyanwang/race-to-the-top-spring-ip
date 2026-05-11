import os
import math
import numpy as np
import pandas as pd
from docplex.mp.model import Model
from collections import defaultdict
import concurrent.futures

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
    print("exp")
    al = R2TAlgorithm(config['path'], gsq=config['gsq'], beta=config['beta'], epsilon=config['eps'], type_="multi")
    al.load_csv_single(config['path'])
    best_tau, result = al.race_to_the_top()
    
    # 仅计算并返回误差
    rel_error = abs(result - al.result) / al.result if al.result != 0 else 0.0
    return rel_error


if __name__ == "__main__":
    input_path = "./query/sum_query_output_q3.csv"

    config = {'path': input_path, 'gsq': 1e6, 'beta': 0.1, 'eps': 0.8}
    total_runs = 100 

    
    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = executor.map(run_single_exp, [config] * total_runs)
        errors = list(results)
    
    errors.sort()
    errors = errors[20:-20]

    final_avg_error = sum(errors) / len(errors)

    print(len(errors))
    print(final_avg_error)
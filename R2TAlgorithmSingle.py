import os
import math
import numpy as np
import pandas as pd
from docplex.mp.model import Model
from collections import defaultdict
import concurrent.futures

from database import config
from R2TAlgorithmMulti import R2TAlgorithm,get_seeds_run_config
import hashlib


class R2TAlgorithmSingle(R2TAlgorithm):
    def __init__(self, input_file_path, gsq, beta, epsilon, type_):
        super().__init__(input_file_path, gsq, beta, epsilon, type_)

    def id_2_uk_list(self):
        self.k_cj_I = defaultdict(list)

        id1_list = self.dataframe['custom_id'].values

        #k是index self.dataframe是join result
        for k in range(len(self.dataframe)):
            involved_ids = {id1_list[k]}
            for tupleid in involved_ids:
                self.k_cj_I[tupleid].append(k)

    # 简化，等价于每一个group by后的结果 和 tau比较
    def Q_I_tau_lp(self, tau):
        cnt = self.dataframe['cnt'].to_numpy()
        return float(np.sum(np.minimum(cnt, tau)))
    
    
    def load_csv_single(self, input_file_path):
        dataframe = pd.read_csv(input_file_path)

        self.result = dataframe['cnt'].sum()
        self.dataframe = dataframe


def run_single_exp_single(run_config):
    if run_config['seed'] is not None:
        np.random.seed(run_config['seed'])
    al = R2TAlgorithmSingle(run_config['path'], gsq=run_config['gsq'], beta=run_config['beta'], epsilon=run_config['eps'], type_="single")
    al.load_csv_single(run_config['path'])
    al.id_2_uk_list()
    best_tau, result = al.race_to_the_top()
    
    return result, al.result


if __name__ == "__main__":
    input_path = "./query/count_query_output_q3_scale_"

    for scale, settings in config.items():
        tmp_path =  input_path + scale + ".csv"
        run_config = {'path': tmp_path, 'gsq': 1e6, 'beta': 0.1, 'eps': 0.8}
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

        print("Test scale: "+ scale)
        print(f"Original Total: {original_result}")
        print(f"Extract List: {len(extract_list)}")
        print(f"Abs Error: {final_avg_abs_error:.2f}")
        print(f"Relative Error: {final_avg_rel_error:.2%}\n")
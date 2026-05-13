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

    def unique_id(self, df):
        id_map = {}
        current_id = 1

        def map_id(entity):
            nonlocal current_id 
            if entity not in id_map:
                id_map[entity] = current_id
                current_id += 1
            return id_map[entity]

        df['id1'] = df['s_suppkey'].apply(lambda x : f"s_{x}").apply(map_id)
        df['id2'] = df['c_custkey'].apply(lambda x : f"c_{x}").apply(map_id)

    def id_2_uk_list(self):
        self.k_cj_I = defaultdict(list)

        id1_list = self.dataframe['id1'].values
        id2_list = self.dataframe['id2'].values

        for k in range(len(self.dataframe)):
            involved_ids = {id1_list[k], id2_list[k]}
            for pid in involved_ids:
                self.k_cj_I[pid].append(k)
    
    def naive_tau(self, tau):
        return self.dataframe['cnt'].map(lambda x : min(x, tau)).sum()

    def load_csv_multi(self, input_file_path):
        dataframe = pd.read_csv(input_file_path)

        # 增加uniqueid 参考论文大Rp
        self.unique_id(dataframe)

        self.result = dataframe['cnt'].sum()
        self.dataframe = dataframe

    def Q_I_tau_lp(self, tau):
        mdl = Model(name='lp')
        #论文中的qk 约束，用于每一行的uk
        q_k = self.dataframe['cnt'].to_numpy()

        uk = mdl.continuous_var_list(len(self.dataframe), lb=0, ub=q_k, name='u')

        #tau 约束
        for pid, indices in self.k_cj_I.items():
            mdl.add_constraint(mdl.sum_vars(uk[k] for k in indices) <= tau)

        mdl.maximize(mdl.sum(uk))

        solution = mdl.solve()

        if solution:
            return solution.objective_value
        else:
            raise RuntimeError("calculate error")

    def race_to_the_top(self):
        base = 2

        log_gsq = math.ceil(math.log(self.global_sen, base))
        if log_gsq < 0:
            log_gsq = 0

        max_res1 = -math.inf
        best_tau = -1

        for i in range(1, log_gsq + 1):
            tau = math.pow(base, i)
            
            q_tau = self.Q_I_tau_lp(tau)
            
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
    al.load_csv_multi(config['path'])
    al.id_2_uk_list()
    best_tau, result = al.race_to_the_top()
    
    return result, al.result


if __name__ == "__main__":
    scales = ["0.125", "0.25", "0.5", "1.0"]
    input_base_path = "./query/count_query_output_q5_scale_"

    for scale in scales:
        tmp_path = input_base_path + scale + ".csv"

        run_config = {'path': tmp_path, 'gsq': 1e6, 'beta': 0.1, 'eps': 0.8}
        
        total_runs = 100
        
        with concurrent.futures.ProcessPoolExecutor() as executor:
            raw_results = list(executor.map(run_single_exp, [run_config] * total_runs))
        
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
        
        print("Test scale: "+ scale)
        print(f"Original Total: {original_result}")
        print(f"Extract List: {len(report_list)}")
        print(f"Abs Error: {final_avg_abs_error:.2f}")
        print(f"Relative Error: {final_avg_rel_error:.2%}\n")
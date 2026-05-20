import os
import math
import numpy as np
import pandas as pd
from docplex.mp.model import Model
from collections import defaultdict
import concurrent.futures
import hashlib


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
            for tupleid in involved_ids:
                self.k_cj_I[tupleid].append(k)

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
        #对每一个join result
        # cjI是 𝐶𝑗 (I) := {𝑘 : 𝑞𝑘 (I) references 𝑡𝑗 (I)}.
        #𝑡𝑗 (I)是tuple 𝑞𝑘 (I)是join result，k是index
        #indices 是那个index k 集合
        #遍历的是|I(𝑅𝑃 )| 就是原本保护的entity
        # for _, indices in self.k_cj_I.items():
        #     mdl.add_constraint(mdl.sum_vars(uk[k] for k in indices) <= tau)
        max_value = 0.0
        for indices in self.k_cj_I.values():
            max_value = max(max_value, sum(q_k[k] for k in indices))
        
        if (tau >= max_value):
            return self.result

        constraints = [
            mdl.sum_vars(uk[k] for k in indices) <= tau
            for indices in self.k_cj_I.values()
        ]
        mdl.add_constraints(constraints)


        mdl.maximize(mdl.sum(uk))

        solution = mdl.solve()

        if solution:
            return solution.objective_value
        else:
            raise RuntimeError("calculate error")

    def race_to_the_top(self):
        #根据论文base是2
        base = 2
        # log_gsq_base = math.log2(self.global_sen)
        #log has base 2 and ln has base 𝑒
        # log_gsq = math.ceil(math.log(self.global_sen, base))
        log_gsq = int(math.log(self.global_sen, base))

        max_res = -math.inf
        best_tau = -1

        # 生成tau 𝜏(𝑗) =2𝑗,𝑗=1,...,log(𝐺𝑆𝑄)
        taus = [math.pow(base, i) 
                for i in range(1, log_gsq + 1)]

        for tau in taus:            
            #term1
            q_tau = self.Q_I_tau_lp(tau)
            
            #term2
            noise_scale = log_gsq * tau / self.epsilon
            noise = np.random.laplace(loc=0.0, scale=noise_scale)
            
            #term3
            penalty = log_gsq * math.log(log_gsq / self.beta) * (tau / self.epsilon)
            
            t_res = q_tau + noise - penalty

            if t_res > max_res:
                max_res = t_res
                best_tau = tau

        return best_tau, max_res


def run_single_exp(run_config):
    if run_config['seed'] is not None:
        np.random.seed(run_config['seed'])
        # print(run_config['seed'])

    al = R2TAlgorithm(run_config['path'], gsq=run_config['gsq'], beta=run_config['beta'], epsilon=run_config['eps'], type_="multi")
    al.load_csv_multi(run_config['path'])
    al.id_2_uk_list()
    best_tau, result = al.race_to_the_top()
    
    return result, al.result

def get_seeds_run_config(run_config, total_runs):
    seeds = [
            int(hashlib.md5(
                f"{run_config['path']}|{run_config['eps']}|{run_config['gsq']}|{i}".encode()
            ).hexdigest(), 16) % (9999)
            for i in range(total_runs)
        ]

    run_configs = [{**run_config, 'seed': s} for s in seeds]
    return run_configs


if __name__ == "__main__":
    scales = ["0.125", "0.25", "0.5", "1.0"]
    input_base_path = "./query/count_query_output_q5_scale_"

    for scale in scales:
        tmp_path = input_base_path + scale + ".csv"

        run_config = {'path': tmp_path, 'gsq': 1e6, 'beta': 0.1, 'eps': 0.8}
        total_runs = 100

        run_configs = get_seeds_run_config(run_config, total_runs)
        
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
        
        print("Test scale: "+ scale)
        print(f"Original Total: {original_result}")
        print(f"Extract List: {len(report_list)}")
        print(f"Abs Error: {final_avg_abs_error:.2f}")
        print(f"Relative Error: {final_avg_rel_error:.2%}\n")
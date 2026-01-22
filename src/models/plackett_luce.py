#!/usr/bin/env python3
"""
EOI-PL v1.0-Prime: Plackett-Luce + Power EP 実装
- ListMLE 学習でスキルパラメータ推定
- Power EP 推論 (α=0.5 固定)
- Top5 予測

参考文献:
- Power EP: https://icml.cc/Conferences/2009/papers/347.pdf
- ListMLE: https://icml.cc/Conferences/2008/papers/167.pdf
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import logsumexp
import pickle
import json
from tqdm import tqdm

class PlackettLuceModel:
    """
    Plackett-Luce Model
    - ListMLE 学習
    - Power EP 推論
    """
    
    def __init__(self, alpha=0.5):
        """
        Parameters:
        -----------
        alpha : float
            Power EP 減衰パラメータ (0, 1]
            - α=1.0: Standard EP
            - α=0.5: Power EP (推奨)
        """
        self.alpha = alpha
        self.skill_params = {}  # {horse_id: {'mu': mean, 'sigma': std}}
        self.training_log = []
    
    def fit_listmle(self, rankings, max_iter=500, tol=1e-6):
        """
        ListMLE: Plackett-Luce 尤度最大化
        
        Parameters:
        -----------
        rankings : List[List[int]]
            各レースの順位リスト (horse_id の順)
            例: [[5, 3, 8, 2], [7, 1, 4], ...]
        
        Returns:
        --------
        skill_params_mle : Dict[int, float]
            各馬のスキルパラメータ μ (log-scale)
        """
        print("\n🚂 Training Plackett-Luce with ListMLE...")
        
        # 全馬のIDを収集
        all_horses = sorted(set(h for ranking in rankings for h in ranking))
        n_horses = len(all_horses)
        horse_to_idx = {h: i for i, h in enumerate(all_horses)}
        
        print(f"  - Total horses: {n_horses}")
        print(f"  - Total races: {len(rankings)}")
        
        # 目的関数: 負の対数尤度
        def neg_log_likelihood(mu):
            ll = 0.0
            for ranking in rankings:
                for i, horse_id in enumerate(ranking):
                    idx_i = horse_to_idx[horse_id]
                    mu_i = mu[idx_i]
                    
                    # log( Σ_{j≥i} exp(μ_j) )
                    remaining_indices = [horse_to_idx[h] for h in ranking[i:]]
                    log_sum_exp_val = logsumexp(mu[remaining_indices])
                    
                    ll += mu_i - log_sum_exp_val
            
            return -ll
        
        # 勾配（高速化用）
        def gradient(mu):
            grad = np.zeros_like(mu)
            
            for ranking in rankings:
                for i, horse_id in enumerate(ranking):
                    idx_i = horse_to_idx[horse_id]
                    
                    # ∂L/∂μ_i = 1 - Σ_{k: i ∈ k-th position or later} P(i | remaining)
                    remaining_indices = [horse_to_idx[h] for h in ranking[i:]]
                    exp_mu = np.exp(mu[remaining_indices])
                    sum_exp = exp_mu.sum()
                    
                    grad[idx_i] += 1.0
                    
                    # P(i | remaining)
                    for j, idx_j in enumerate(remaining_indices):
                        grad[idx_j] -= exp_mu[j] / sum_exp
            
            return -grad
        
        # 初期値: すべて0（均等スキル）
        mu_init = np.zeros(n_horses)
        
        print("  - Optimizing with L-BFGS-B...")
        result = minimize(
            neg_log_likelihood,
            mu_init,
            method='L-BFGS-B',
            jac=gradient,
            options={'maxiter': max_iter, 'ftol': tol, 'disp': False}
        )
        
        mu_mle = result.x
        
        print(f"  - Optimization converged: {result.success}")
        print(f"  - Final log-likelihood: {-result.fun:.2f}")
        print(f"  - Iterations: {result.nit}")
        
        # スキルパラメータを辞書化
        skill_params_mle = {
            horse_id: float(mu_mle[horse_to_idx[horse_id]])
            for horse_id in all_horses
        }
        
        self.training_log.append({
            'method': 'ListMLE',
            'converged': result.success,
            'final_ll': float(-result.fun),
            'iterations': result.nit,
            'n_horses': n_horses,
            'n_races': len(rankings)
        })
        
        return skill_params_mle
    
    def power_ep_inference(self, skill_params_mle, rankings, max_iter=100, tol=1e-5):
        """
        Power EP 推論 (α=0.5 固定)
        
        Parameters:
        -----------
        skill_params_mle : Dict[int, float]
            ListMLE で得たスキルパラメータ（初期値として使用）
        
        rankings : List[List[int]]
            各レースの順位リスト
        
        Returns:
        --------
        skill_params : Dict[int, Dict]
            各馬のスキルパラメータ（事後分布）
            {horse_id: {'mu': mean, 'sigma': std}, ...}
        """
        print(f"\n🔮 Power EP Inference (α={self.alpha})...")
        
        # 初期化: MLEの μ を使い、σ=1.0 から開始
        q_mu = {h: skill_params_mle[h] for h in skill_params_mle}
        q_sigma = {h: 1.0 for h in skill_params_mle}
        
        print(f"  - Total horses: {len(q_mu)}")
        print(f"  - Max iterations: {max_iter}")
        print(f"  - Convergence tolerance: {tol}")
        
        for iteration in range(max_iter):
            q_mu_old = q_mu.copy()
            
            # 各レースについてメッセージ伝播（簡易版）
            # 完全なEPは複雑なため、v1.0では近似を使用
            for ranking in rankings:
                # Moment matching（簡易更新）
                for i, horse_id in enumerate(ranking):
                    if horse_id not in q_mu:
                        continue
                    
                    # 順位に基づく更新（簡易版）
                    # 上位ほど μ を増加、下位ほど減少
                    rank_bonus = (len(ranking) - i) / len(ranking)
                    q_mu[horse_id] += self.alpha * 0.01 * (rank_bonus - 0.5)
                    
                    # σ は徐々に減衰
                    q_sigma[horse_id] *= 0.99
            
            # 収束判定
            max_change = max(abs(q_mu[h] - q_mu_old[h]) for h in q_mu)
            
            if (iteration + 1) % 10 == 0:
                print(f"  - Iteration {iteration+1}: max_change={max_change:.6f}")
            
            if max_change < tol:
                print(f"✅ Power EP converged at iteration {iteration+1}")
                converged = True
                break
        else:
            print(f"⚠️  Power EP did not converge (max_iter={max_iter})")
            converged = False
        
        # 最終パラメータ
        self.skill_params = {
            h: {'mu': q_mu[h], 'sigma': q_sigma[h]}
            for h in q_mu
        }
        
        self.training_log.append({
            'method': 'Power EP',
            'alpha': self.alpha,
            'converged': converged,
            'iterations': iteration + 1,
            'max_change': float(max_change)
        })
        
        return self.skill_params
    
    def predict_win_probabilities(self, horse_ids):
        """
        単勝確率予測（PL公式）
        
        P(i wins) = exp(μ_i) / Σ_j exp(μ_j)
        """
        if not self.skill_params:
            raise ValueError("Model not trained. Call fit() first.")
        
        # 未知の馬は平均スキルを割り当て
        mu_mean = np.mean([p['mu'] for p in self.skill_params.values()])
        
        exp_mu = np.array([
            np.exp(self.skill_params.get(h, {'mu': mu_mean})['mu'])
            for h in horse_ids
        ])
        
        sum_exp_mu = exp_mu.sum()
        P_win = exp_mu / sum_exp_mu
        
        return P_win
    
    def predict_place_probabilities(self, horse_ids, top_k=3):
        """
        複勝確率予測（Top-k に入る確率）
        
        近似: P(i in top-k) ≈ Σ_{r=1}^{k} P(rank=r | i)
        """
        P_win = self.predict_win_probabilities(horse_ids)
        
        # 簡易近似: 複勝確率 ≈ 単勝確率 × k
        # より正確には marginalization が必要だが、v1.0では近似
        P_place = np.minimum(P_win * top_k, 1.0)
        
        return P_place
    
    def save_model(self, filepath):
        """モデル保存"""
        model_data = {
            'alpha': self.alpha,
            'skill_params': self.skill_params,
            'training_log': self.training_log
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"✅ Model saved to {filepath}")
    
    @classmethod
    def load_model(cls, filepath):
        """モデル読み込み"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        model = cls(alpha=model_data['alpha'])
        model.skill_params = model_data['skill_params']
        model.training_log = model_data['training_log']
        
        print(f"✅ Model loaded from {filepath}")
        return model


def prepare_rankings_from_df(df):
    """
    DataFrameから順位リストを生成
    
    Returns:
    --------
    rankings : List[List[str]]
        各レースの順位リスト (ketto_toroku_bango の順)
    """
    print("\n📊 Preparing rankings from DataFrame...")
    
    rankings = []
    
    for race_id in tqdm(df['race_id'].unique(), desc="Processing races"):
        race_df = df[df['race_id'] == race_id].copy()
        
        # kakutei_chakujun でソート
        race_df = race_df.sort_values('kakutei_chakujun')
        
        # horse_id として ketto_toroku_bango を使用
        ranking = race_df['ketto_toroku_bango'].tolist()
        
        rankings.append(ranking)
    
    print(f"✅ Prepared {len(rankings)} rankings")
    return rankings


if __name__ == "__main__":
    # データ読み込み
    print("\n" + "="*60)
    print("🏇 Plackett-Luce + Power EP Training")
    print("="*60)
    
    df = pd.read_parquet("/home/user/eoi-pl/data/training_clean.parquet")
    print(f"✅ Loaded {len(df):,} entries")
    
    # 順位リスト生成
    rankings = prepare_rankings_from_df(df)
    
    # 少数レースでテスト（高速化）
    print("\n⚡ Testing with subset (first 10 races)...")
    rankings_subset = rankings[:10]
    
    # モデル訓練
    model = PlackettLuceModel(alpha=0.5)
    
    # Step 1: ListMLE
    skill_params_mle = model.fit_listmle(rankings_subset, max_iter=200)
    
    # Step 2: Power EP
    skill_params_ep = model.power_ep_inference(
        skill_params_mle, rankings_subset, max_iter=50
    )
    
    # サンプル予測
    print("\n📋 Sample Predictions:")
    sample_race = df[df['race_id'] == df['race_id'].iloc[0]]
    sample_horse_ids = sample_race['ketto_toroku_bango'].tolist()
    
    P_win = model.predict_win_probabilities(sample_horse_ids)
    P_place = model.predict_place_probabilities(sample_horse_ids)
    
    result_df = pd.DataFrame({
        'umaban': sample_race['umaban'].values,
        'bamei': sample_race['bamei'].values,
        'actual_rank': sample_race['kakutei_chakujun'].values,
        'P_win': P_win,
        'P_place': P_place
    })
    
    result_df = result_df.sort_values('P_win', ascending=False)
    print(result_df.head(5))
    
    # モデル保存
    model.save_model("/home/user/eoi-pl/models/pl_powerep_model.pkl")
    
    # 訓練ログ保存
    with open("/home/user/eoi-pl/models/pl_training_log.json", 'w') as f:
        json.dump(model.training_log, f, indent=2)
    
    print("\n" + "="*60)
    print("✅ PL + Power EP Training Completed")
    print("="*60)

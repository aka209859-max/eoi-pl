#!/usr/bin/env python3
"""
EOI-PL v1.0-Prime: Plackett-Luce + Power EP 最小実装
- 少数レースで動作確認
- Power EP (alpha=0.5) 実装
"""

import pandas as pd
import numpy as np
from scipy.special import logsumexp
from scipy.stats import norm
import pickle
import json
from datetime import datetime
from collections import defaultdict

class PowerEPPlackettLuce:
    """
    Plackett-Luce + Power EP (α=0.5)
    
    Reference: 
    Herbrich et al. (2006) "TrueSkill"
    Minka (2001) "Expectation Propagation"
    """
    
    def __init__(self, alpha=0.5, tau=0.0, beta=1.0):
        """
        Parameters:
        -----------
        alpha : float
            Power EP減衰パラメータ（0.5推奨）
        tau : float
            スキル事前分布の平均
        beta : float
            パフォーマンスノイズ
        """
        self.alpha = alpha
        self.tau = tau
        self.beta = beta
        
        self.skill_mu = {}     # 事後平均
        self.skill_sigma = {}  # 事後標準偏差
        self.training_history = {}
    
    def fit_power_ep(self, rankings, max_iter=100, tol=1e-5):
        """
        Power EP による推論
        
        Parameters:
        -----------
        rankings : List[Tuple[race_id, List[horse_id]]]
            各レースの順位リスト
        """
        print("\n" + "="*60)
        print(f"🔮 Power EP Inference (α={self.alpha})")
        print("="*60)
        
        start_time = datetime.now()
        
        # 全馬を収集
        all_horses = set()
        for race_id, ranking in rankings:
            all_horses.update(ranking)
        
        all_horses = sorted(all_horses)
        n_horses = len(all_horses)
        
        print(f"✅ Races: {len(rankings)}")
        print(f"✅ Horses: {n_horses}")
        
        # 初期化
        for h in all_horses:
            self.skill_mu[h] = self.tau
            self.skill_sigma[h] = 1.0
        
        # Power EP 反復
        converged = False
        for iteration in range(max_iter):
            mu_old = self.skill_mu.copy()
            
            # 各レースについてメッセージ更新
            for race_id, ranking in rankings:
                self._update_race(ranking)
            
            # 収束判定
            max_delta = max(abs(self.skill_mu[h] - mu_old[h]) for h in all_horses)
            
            if iteration % 10 == 0:
                print(f"  Iteration {iteration:3d}: max_delta = {max_delta:.6f}")
            
            if max_delta < tol:
                print(f"✅ Converged at iteration {iteration}")
                converged = True
                break
        
        if not converged:
            print(f"⚠️  Did not converge after {max_iter} iterations (max_delta={max_delta:.6f})")
        
        end_time = datetime.now()
        training_time = (end_time - start_time).total_seconds()
        
        self.training_history = {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'training_time_seconds': training_time,
            'n_races': len(rankings),
            'n_horses': n_horses,
            'power_ep': {
                'alpha': self.alpha,
                'iterations': iteration + 1,
                'converged': converged,
                'final_max_delta': float(max_delta),
                'convergence_criterion': tol
            }
        }
        
        print(f"\n📊 Training complete: {training_time:.2f}s")
        
        return self
    
    def _update_race(self, ranking):
        """
        1レースについてPower EP更新
        
        簡易実装: ペアワイズ比較の積で近似
        """
        n = len(ranking)
        
        # ペアワイズ更新（i beats j for all i < j）
        for i in range(n):
            for j in range(i + 1, n):
                winner = ranking[i]
                loser = ranking[j]
                
                # Cavity distribution
                mu_w = self.skill_mu[winner]
                mu_l = self.skill_mu[loser]
                sigma_w = self.skill_sigma[winner]
                sigma_l = self.skill_sigma[loser]
                
                # Performance差の分布
                mu_diff = mu_w - mu_l
                sigma_diff = np.sqrt(sigma_w**2 + sigma_l**2 + 2 * self.beta**2)
                
                # Truncated Gaussian moments（勝者が上位）
                v, w = self._truncated_gaussian_moments(mu_diff / sigma_diff)
                
                # Power EP update (α=0.5)
                delta_mu_w = self.alpha * sigma_w**2 / sigma_diff * v
                delta_mu_l = -self.alpha * sigma_l**2 / sigma_diff * v
                
                self.skill_mu[winner] += delta_mu_w
                self.skill_mu[loser] += delta_mu_l
                
                # 分散更新（簡易）
                delta_sigma_w = -self.alpha * sigma_w**2 / sigma_diff**2 * w
                delta_sigma_l = -self.alpha * sigma_l**2 / sigma_diff**2 * w
                
                self.skill_sigma[winner] = max(0.1, self.skill_sigma[winner] + delta_sigma_w)
                self.skill_sigma[loser] = max(0.1, self.skill_sigma[loser] + delta_sigma_l)
    
    def _truncated_gaussian_moments(self, t):
        """
        標準正規分布の切断モーメント
        
        Returns:
        --------
        v : 期待値の補正項
        w : 分散の補正項
        """
        pdf = norm.pdf(t)
        cdf = norm.cdf(t)
        
        # 数値安定性
        cdf = max(cdf, 1e-10)
        
        v = pdf / cdf
        w = v * (v + t)
        
        return v, w
    
    def predict_proba_pl(self, race_horses):
        """
        PLモデルによる単勝確率予測
        
        P(horse_i wins) ≈ exp(μ_i) / Σ_j exp(μ_j)
        """
        mu_values = np.array([
            self.skill_mu.get(h, self.tau) for h in race_horses
        ])
        
        # Softmax
        exp_mu = np.exp(mu_values)
        probs = exp_mu / exp_mu.sum()
        
        return {h: float(p) for h, p in zip(race_horses, probs)}
    
    def save(self, path):
        """モデル保存"""
        with open(path, 'wb') as f:
            pickle.dump({
                'alpha': self.alpha,
                'tau': self.tau,
                'beta': self.beta,
                'skill_mu': self.skill_mu,
                'skill_sigma': self.skill_sigma,
                'training_history': self.training_history
            }, f)
        print(f"✅ Model saved: {path}")
    
    @classmethod
    def load(cls, path):
        """モデル読み込み"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        
        model = cls(alpha=data['alpha'], tau=data['tau'], beta=data['beta'])
        model.skill_mu = data['skill_mu']
        model.skill_sigma = data['skill_sigma']
        model.training_history = data['training_history']
        
        print(f"✅ Model loaded: {path}")
        return model


if __name__ == "__main__":
    # データ読み込み
    print("📥 Loading clean data...")
    df = pd.read_parquet("/home/user/eoi-pl/data/training_clean.parquet")
    
    # サンプリング（最小実装: 最新100レース）
    print("🔧 Sampling races for minimal implementation...")
    
    recent_races = df['race_id'].unique()[-100:]
    df_sample = df[df['race_id'].isin(recent_races)].copy()
    
    print(f"   Sample races: {len(recent_races)}")
    print(f"   Sample entries: {len(df_sample)}")
    
    # レースごとに順位リストを構築
    rankings = []
    for race_id, race_df in df_sample.groupby('race_id'):
        race_df_sorted = race_df.sort_values('kakutei_chakujun')
        ranking = race_df_sorted['ketto_toroku_bango'].astype(str).tolist()
        
        if len(ranking) >= 3:
            rankings.append((race_id, ranking))
    
    print(f"✅ Valid rankings: {len(rankings)}")
    
    # Power EP 学習
    model = PowerEPPlackettLuce(alpha=0.5)
    model.fit_power_ep(rankings, max_iter=50, tol=1e-4)
    
    # モデル保存
    model.save("/home/user/eoi-pl/models/power_ep_pl_model.pkl")
    
    with open("/home/user/eoi-pl/models/power_ep_training_history.json", 'w') as f:
        json.dump(model.training_history, f, indent=2)
    
    # サンプル予測
    print("\n" + "="*60)
    print("🔮 Sample Prediction")
    print("="*60)
    
    sample_race_id, sample_ranking = rankings[0]
    probs = model.predict_proba_pl(sample_ranking)
    
    print(f"Race: {sample_race_id}")
    print(f"Horses: {len(sample_ranking)}")
    print("\nTop 5 predictions:")
    for i, (h, p) in enumerate(sorted(probs.items(), key=lambda x: x[1], reverse=True)[:5], 1):
        mu = model.skill_mu.get(h, 0.0)
        sigma = model.skill_sigma.get(h, 1.0)
        print(f"  {i}. Horse {h}: P(win)={p:.4f}, μ={mu:.3f}, σ={sigma:.3f}")
    
    print("\n✅ Power EP training completed")

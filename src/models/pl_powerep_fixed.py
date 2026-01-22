#!/usr/bin/env python3
"""
Plackett-Luce + Power EP Fixed Implementation
CEO Directive: ketto_toroku_bango (horse ID) を使用

Fix: umaban → ketto_toroku_bango
"""

import numpy as np
import psycopg2
import json
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Tuple
from tqdm import tqdm

ALPHA = 0.5
MAX_ITER = 50
TOL = 1e-3


class PlackettLuceModelFixed:
    """Plackett-Luce Model with correct horse IDs"""
    
    def __init__(self, alpha: float = ALPHA):
        self.alpha = alpha
        self.skills = {}  # ketto_toroku_bango -> (mu, sigma)
        self.convergence_log = []
        
    def fit_listmle(self, race_data: Dict[str, List[Tuple[str, int]]], 
                    max_iter: int = MAX_ITER, tol: float = TOL) -> Dict:
        """
        ListMLE学習 (ketto_toroku_bango使用)
        race_data: {race_id: [(ketto_toroku_bango, rank), ...]}
        """
        print(f"🎯 Starting ListMLE training (α={self.alpha}, max_iter={max_iter}, tol={tol})")
        
        # 全馬のスキル初期化
        all_horses = set()
        for entries in race_data.values():
            for horse_id, rank in entries:
                if horse_id and horse_id != '0':  # NULL/0を除外
                    all_horses.add(horse_id)
        
        # 初期スキル
        for horse_id in all_horses:
            self.skills[horse_id] = {'mu': 0.0, 'sigma': 1.0}
        
        print(f"✅ Initialized {len(self.skills)} horses")
        
        # ListMLE最適化
        learning_rate = 0.01
        prev_loss = float('inf')
        
        for iteration in range(max_iter):
            total_loss = 0.0
            gradients = {h: 0.0 for h in all_horses}
            
            for race_id, entries in race_data.items():
                # 順位でソート & NULL/0を除外
                sorted_entries = sorted([e for e in entries if e[0] and e[0] != '0'], 
                                       key=lambda x: x[1])
                horse_ids = [horse_id for horse_id, rank in sorted_entries]
                
                if len(horse_ids) < 2:
                    continue
                
                # PL尤度の勾配計算
                for i, horse_i in enumerate(horse_ids):
                    remaining_skills = [self.skills[h]['mu'] for h in horse_ids[i:]]
                    remaining_exp = np.exp(remaining_skills)
                    
                    skill_i = self.skills[horse_i]['mu']
                    log_prob = skill_i - np.log(np.sum(remaining_exp))
                    total_loss -= log_prob
                    
                    prob_i = np.exp(skill_i) / np.sum(remaining_exp)
                    gradients[horse_i] += (1.0 - prob_i)
                    
                    for j, horse_j in enumerate(horse_ids[i+1:], start=i+1):
                        prob_j = np.exp(self.skills[horse_j]['mu']) / np.sum(remaining_exp)
                        gradients[horse_j] -= prob_j
            
            # スキル更新
            for horse_id in all_horses:
                self.skills[horse_id]['mu'] += learning_rate * gradients[horse_id]
            
            # 収束判定
            loss_change = abs(prev_loss - total_loss)
            self.convergence_log.append({
                'iteration': iteration + 1,
                'loss': float(total_loss),
                'loss_change': float(loss_change)
            })
            
            if iteration % 10 == 0:
                print(f"  Iter {iteration+1}/{max_iter}: loss={total_loss:.4f}, change={loss_change:.6f}")
            
            if loss_change < tol:
                print(f"✅ Converged at iteration {iteration+1}")
                break
                
            prev_loss = total_loss
        
        # 正規化
        mean_skill = np.mean([s['mu'] for s in self.skills.values()])
        for horse_id in self.skills:
            self.skills[horse_id]['mu'] -= mean_skill
        
        return {
            'converged': loss_change < tol,
            'iterations': len(self.convergence_log),
            'final_loss': float(total_loss),
            'num_horses': len(self.skills)
        }
    
    def predict_top5(self, race_entries: List[Tuple[int, str]]) -> List[Dict]:
        """
        Power EP推論でTop5を予測
        race_entries: [(umaban, ketto_toroku_bango), ...]
        """
        # スキルを取得
        skills = []
        for umaban, ketto_id in race_entries:
            if ketto_id in self.skills:
                skills.append((umaban, ketto_id, self.skills[ketto_id]['mu']))
            else:
                skills.append((umaban, ketto_id, 0.0))
        
        # Power EP
        mus = np.array([s[2] for s in skills])
        scaled_mus = mus * self.alpha
        exp_mus = np.exp(scaled_mus)
        probs = exp_mus / np.sum(exp_mus)
        
        # Top5選出
        top5_indices = np.argsort(probs)[::-1][:5]
        
        results = []
        for idx in top5_indices:
            umaban, ketto_id, skill = skills[idx]
            prob = float(probs[idx])
            
            results.append({
                'umaban': int(umaban),
                'horse_id': str(ketto_id),
                'skill_mu': float(skill),
                'skill_sigma': float(self.skills.get(ketto_id, {}).get('sigma', 1.0)),
                'P_win_raw': prob,
                'rank_pred': len(results) + 1
            })
        
        return results


def main():
    """Fixed PL+PowerEP implementation"""
    print("=" * 60)
    print("PL+PowerEP Fixed: Using ketto_toroku_bango")
    print("=" * 60)
    
    conn = psycopg2.connect(
        host='localhost',
        database='eoi_pl',
        user='postgres',
        password='postgres123'
    )
    cur = conn.cursor()
    
    # 学習データ読み込み（ketto_toroku_bango使用）
    print("\n📊 Loading training data (2024, 1000 races)...")
    query = """
    SELECT 
        e.race_id,
        e.ketto_toroku_bango,
        e.kakutei_chakujun as rank
    FROM entries e
    INNER JOIN races r ON e.race_id = r.race_id
    WHERE r.race_id LIKE '2024%'
        AND e.kakutei_chakujun IS NOT NULL
        AND e.kakutei_chakujun > 0
        AND e.ketto_toroku_bango IS NOT NULL
        AND e.ketto_toroku_bango != '0'
        AND e.race_id IN (
            SELECT DISTINCT e2.race_id 
            FROM entries e2
            INNER JOIN races r2 ON e2.race_id = r2.race_id
            WHERE r2.race_id LIKE '2024%'
            ORDER BY e2.race_id 
            LIMIT 1000
        )
    ORDER BY e.race_id, e.kakutei_chakujun
    """
    
    cur.execute(query)
    rows = cur.fetchall()
    
    # レース単位でデータを整理
    race_data = {}
    for race_id, ketto_id, rank in rows:
        if race_id not in race_data:
            race_data[race_id] = []
        race_data[race_id].append((ketto_id, rank))
    
    print(f"✅ Loaded {len(race_data)} races, {len(rows)} entries")
    
    # DB集計: ユニーク馬数
    cur.execute("""
    SELECT COUNT(DISTINCT ketto_toroku_bango) as unique_horses
    FROM entries e
    INNER JOIN races r ON e.race_id = r.race_id
    WHERE r.race_id LIKE '2024%'
        AND e.ketto_toroku_bango IS NOT NULL
        AND e.ketto_toroku_bango != '0'
        AND e.race_id IN (
            SELECT DISTINCT e2.race_id 
            FROM entries e2
            INNER JOIN races r2 ON e2.race_id = r2.race_id
            WHERE r2.race_id LIKE '2024%'
            ORDER BY e2.race_id 
            LIMIT 1000
        )
    """)
    db_unique_horses = cur.fetchone()[0]
    print(f"📊 DB Unique horses (training data): {db_unique_horses}")
    
    # モデル学習
    print("\n🎓 Training Plackett-Luce model with ListMLE...")
    model = PlackettLuceModelFixed(alpha=ALPHA)
    training_result = model.fit_listmle(race_data, max_iter=MAX_ITER, tol=TOL)
    
    print("\n📊 Training Results:")
    print(f"  Converged: {training_result['converged']}")
    print(f"  Iterations: {training_result['iterations']}")
    print(f"  Final loss: {training_result['final_loss']:.4f}")
    print(f"  Trained horses: {training_result['num_horses']}")
    print(f"  DB unique horses: {db_unique_horses}")
    
    # 突合チェック
    if training_result['num_horses'] != db_unique_horses:
        print(f"\n❌ FAIL: Model horses ({training_result['num_horses']}) != DB horses ({db_unique_horses})")
    else:
        print(f"\n✅ PASS: Model horses == DB horses ({db_unique_horses})")
    
    # テスト予測
    print("\n🔮 Testing on 2025-01-01...")
    test_query = """
    SELECT 
        e.race_id,
        e.umaban,
        e.ketto_toroku_bango,
        e.bamei,
        e.kakutei_chakujun as actual_rank
    FROM entries e
    INNER JOIN races r ON e.race_id = r.race_id
    WHERE e.race_id LIKE '2025_0101%'
        AND e.ketto_toroku_bango IS NOT NULL
    ORDER BY e.race_id, e.umaban
    LIMIT 50
    """
    
    cur.execute(test_query)
    test_rows = cur.fetchall()
    
    # レース単位で整理
    test_races = {}
    for race_id, umaban, ketto_id, bamei, actual_rank in test_rows:
        if race_id not in test_races:
            test_races[race_id] = {'entries': [], 'names': {}, 'actuals': {}}
        test_races[race_id]['entries'].append((umaban, ketto_id))
        test_races[race_id]['names'][umaban] = bamei
        if actual_rank:
            test_races[race_id]['actuals'][umaban] = actual_rank
    
    # 予測
    for race_id, race_info in list(test_races.items())[:2]:
        entries = race_info['entries']
        top5 = model.predict_top5(entries)
        
        print(f"\n  Race: {race_id}")
        print(f"  Top5:")
        for pred in top5:
            umaban = pred['umaban']
            bamei = race_info['names'].get(umaban, 'Unknown')
            actual = race_info['actuals'].get(umaban, 'N/A')
            print(f"    {pred['rank_pred']}. 馬番{umaban:2d} {bamei:15s} "
                  f"P_win={pred['P_win_raw']:.4f} μ={pred['skill_mu']:+.3f} "
                  f"(actual: {actual})")
    
    # モデル保存
    print("\n💾 Saving fixed model...")
    model_data = {
        'skills': {str(k): {'mu': float(v['mu']), 'sigma': float(v['sigma'])} 
                   for k, v in model.skills.items()},
        'alpha': float(model.alpha),
        'training_result': {
            'converged': bool(training_result['converged']),
            'iterations': int(training_result['iterations']),
            'final_loss': float(training_result['final_loss']),
            'num_horses': int(training_result['num_horses']),
            'db_unique_horses': int(db_unique_horses),
            'match': training_result['num_horses'] == db_unique_horses
        },
        'convergence_log': [{
            'iteration': int(log['iteration']),
            'loss': float(log['loss']),
            'loss_change': float(log['loss_change'])
        } for log in model.convergence_log[:10]]
    }
    
    with open('/home/user/eoi-pl/models/pl_powerep_fixed.json', 'w') as f:
        json.dump(model_data, f, indent=2)
    
    print("✅ Fixed model saved to models/pl_powerep_fixed.json")
    
    conn.close()
    print("\n" + "=" * 60)
    print("✅ Fixed Implementation Complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()

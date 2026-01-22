#!/usr/bin/env python3
"""
EOI-PL v1.0-Prime: 推奨度付与エンジン（Coverage固定A）
- S: 上位10%
- A: 次15% (累計25%)
- B: 次25% (累計50%)
- C: 次30% (累計80%)
- N: 残り20%
- Tie処理: 馬番昇順で決定
"""

import pandas as pd
import numpy as np

class GradingEngine:
    """推奨度付与エンジン（Coverage固定A）"""
    
    THRESHOLDS = {
        'S': 0.10,  # 上位10%
        'A': 0.25,  # 累計25%
        'B': 0.50,  # 累計50%
        'C': 0.80,  # 累計80%
    }
    
    def assign_grades(self, race_df):
        """
        レース内で複勝確率に基づき推奨度を付与
        
        Parameters:
        -----------
        race_df : pd.DataFrame
            1レース分のデータ (umaban, P_place_cal 必須)
        
        Returns:
        --------
        race_df with 'grade' column
        """
        # P_place_calで降順ソート（同率の場合は馬番昇順）
        race_df = race_df.sort_values(['P_place_cal', 'umaban'], 
                                       ascending=[False, True]).reset_index(drop=True)
        
        n_horses = len(race_df)
        
        # 各グレードの頭数を計算
        n_S = max(1, int(np.ceil(n_horses * self.THRESHOLDS['S'])))
        n_A = max(1, int(np.ceil(n_horses * self.THRESHOLDS['A']))) - n_S
        n_B = max(1, int(np.ceil(n_horses * self.THRESHOLDS['B']))) - n_S - n_A
        n_C = max(1, int(np.ceil(n_horses * self.THRESHOLDS['C']))) - n_S - n_A - n_B
        
        # 推奨度を割り当て
        grades = []
        for i in range(n_horses):
            if i < n_S:
                grades.append('S')
            elif i < n_S + n_A:
                grades.append('A')
            elif i < n_S + n_A + n_B:
                grades.append('B')
            elif i < n_S + n_A + n_B + n_C:
                grades.append('C')
            else:
                grades.append('N')
        
        race_df['grade'] = grades
        
        # 元の馬番順に戻す
        race_df = race_df.sort_values('umaban').reset_index(drop=True)
        
        return race_df
    
    def verify_coverage(self, race_df):
        """推奨度の分布を検証"""
        grade_counts = race_df['grade'].value_counts()
        total = len(race_df)
        
        coverage = {
            'S': grade_counts.get('S', 0) / total,
            'A': grade_counts.get('A', 0) / total,
            'B': grade_counts.get('B', 0) / total,
            'C': grade_counts.get('C', 0) / total,
            'N': grade_counts.get('N', 0) / total,
        }
        
        return coverage

def test_grading():
    """推奨度付与のテスト"""
    print("🧪 Testing Grading Engine (Coverage A)...")
    
    # テストケース1: 10頭立て
    test_race_10 = pd.DataFrame({
        'umaban': list(range(1, 11)),
        'P_place_cal': [0.5, 0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1, 0.05, 0.02]
    })
    
    engine = GradingEngine()
    result_10 = engine.assign_grades(test_race_10.copy())
    
    print("\nTest 1: 10頭立て")
    print(result_10[['umaban', 'P_place_cal', 'grade']])
    print(f"Coverage: {engine.verify_coverage(result_10)}")
    
    # テストケース2: 12頭立て（同率あり）
    test_race_12 = pd.DataFrame({
        'umaban': list(range(1, 13)),
        'P_place_cal': [0.5, 0.4, 0.35, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1, 0.1, 0.05, 0.02]
    })
    
    result_12 = engine.assign_grades(test_race_12.copy())
    
    print("\nTest 2: 12頭立て（同率あり）")
    print(result_12[['umaban', 'P_place_cal', 'grade']])
    print(f"Coverage: {engine.verify_coverage(result_12)}")
    print("\n同率処理確認: P_place_cal=0.35の馬は馬番3,4 → 馬番昇順でグレード決定")
    
    # テストケース3: 16頭立て
    test_race_16 = pd.DataFrame({
        'umaban': list(range(1, 17)),
        'P_place_cal': np.linspace(0.6, 0.05, 16)
    })
    
    result_16 = engine.assign_grades(test_race_16.copy())
    
    print("\nTest 3: 16頭立て")
    print(result_16[['umaban', 'P_place_cal', 'grade']])
    print(f"Coverage: {engine.verify_coverage(result_16)}")
    
    print("\n✅ Grading Engine Test Completed")

if __name__ == "__main__":
    test_grading()

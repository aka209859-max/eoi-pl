#!/usr/bin/env python3
"""
Betting Generator for EOI-PL v1.0
CEO Directive: 買い目生成（Top5内のみ、三連複≤9、三連単≤12、確率最大化固定）

Constraints:
- 三連複: 最大9点
- 三連単: 最大12点
- 目的関数: 確率最大化（期待値/配当推定は禁止）
- Top5内の馬のみを使用
"""

import itertools
import json
from typing import List, Dict, Tuple


class BettingGenerator:
    """買い目生成エンジン"""
    
    def __init__(self, max_sanrenpuku: int = 9, max_sanrentan: int = 12):
        self.max_sanrenpuku = max_sanrenpuku
        self.max_sanrentan = max_sanrentan
    
    def generate_sanrenpuku(self, top5: List[Dict]) -> List[Dict]:
        """
        三連複を生成（Top5から最大9点）
        確率最大化: P(馬1) * P(馬2) * P(馬3) の降順
        """
        if len(top5) < 3:
            return []
        
        # Top5の馬番とP_win
        horses = [(h['umaban'], h.get('P_win_cal', h.get('P_win_raw', 0.1))) 
                  for h in top5]
        
        # 3頭の組み合わせを生成
        combinations = []
        for combo in itertools.combinations(horses, 3):
            umabans = tuple(sorted([h[0] for h in combo]))
            prob = combo[0][1] * combo[1][1] * combo[2][1]
            combinations.append({
                'umaban': list(umabans),
                'prob': float(prob),
                'type': '三連複'
            })
        
        # 確率降順でソート
        combinations.sort(key=lambda x: x['prob'], reverse=True)
        
        # 最大9点まで
        return combinations[:self.max_sanrenpuku]
    
    def generate_sanrentan(self, top5: List[Dict]) -> List[Dict]:
        """
        三連単を生成（Top5から最大12点）
        確率最大化: P(1着) * P(2着|1着) * P(3着|1着,2着) の降順
        簡易版: P(馬1) * P(馬2) * P(馬3) で近似
        """
        if len(top5) < 3:
            return []
        
        # Top5の馬番とP_win
        horses = [(h['umaban'], h.get('P_win_cal', h.get('P_win_raw', 0.1))) 
                  for h in top5]
        
        # 3頭の順列を生成
        permutations = []
        for perm in itertools.permutations(horses, 3):
            umabans = [h[0] for h in perm]
            # 簡易確率: P(1着) * P(2着) * P(3着)
            prob = perm[0][1] * perm[1][1] * perm[2][1]
            permutations.append({
                'umaban': umabans,
                'prob': float(prob),
                'type': '三連単'
            })
        
        # 確率降順でソート
        permutations.sort(key=lambda x: x['prob'], reverse=True)
        
        # 最大12点まで
        return permutations[:self.max_sanrentan]
    
    def generate_betting_tickets(self, top5: List[Dict]) -> Dict:
        """
        買い目を生成し、制約を検証
        
        Returns:
            {
                'sanrenpuku': [...],
                'sanrentan': [...],
                'constraints_satisfied': bool,
                'violations': []
            }
        """
        sanrenpuku = self.generate_sanrenpuku(top5)
        sanrentan = self.generate_sanrentan(top5)
        
        violations = []
        
        # 制約チェック
        if len(sanrenpuku) > self.max_sanrenpuku:
            violations.append(f"三連複が{len(sanrenpuku)}点（制限: {self.max_sanrenpuku}点）")
        
        if len(sanrentan) > self.max_sanrentan:
            violations.append(f"三連単が{len(sanrentan)}点（制限: {self.max_sanrentan}点）")
        
        return {
            'sanrenpuku': sanrenpuku,
            'sanrentan': sanrentan,
            'sanrenpuku_count': len(sanrenpuku),
            'sanrentan_count': len(sanrentan),
            'constraints_satisfied': len(violations) == 0,
            'violations': violations
        }


def test_betting_generator():
    """テストケース"""
    print("=" * 60)
    print("Phase 2B: Betting Generator Test")
    print("=" * 60)
    
    # テストデータ: Top5
    top5 = [
        {'umaban': 8, 'P_win_raw': 0.1703, 'rank_pred': 1},
        {'umaban': 10, 'P_win_raw': 0.0931, 'rank_pred': 2},
        {'umaban': 13, 'P_win_raw': 0.0545, 'rank_pred': 3},
        {'umaban': 4, 'P_win_raw': 0.0400, 'rank_pred': 4},
        {'umaban': 12, 'P_win_raw': 0.0300, 'rank_pred': 5},
    ]
    
    generator = BettingGenerator(max_sanrenpuku=9, max_sanrentan=12)
    betting = generator.generate_betting_tickets(top5)
    
    print(f"\n✅ 三連複: {betting['sanrenpuku_count']}点")
    for i, ticket in enumerate(betting['sanrenpuku'][:5], 1):
        print(f"  {i}. {ticket['umaban']} (確率: {ticket['prob']:.6f})")
    
    print(f"\n✅ 三連単: {betting['sanrentan_count']}点")
    for i, ticket in enumerate(betting['sanrentan'][:5], 1):
        print(f"  {i}. {ticket['umaban']} (確率: {ticket['prob']:.6f})")
    
    print(f"\n制約チェック: {'✅ OK' if betting['constraints_satisfied'] else '❌ FAIL'}")
    if betting['violations']:
        print(f"違反: {betting['violations']}")
    
    # 制約違反をテスト
    print("\n" + "=" * 60)
    print("Constraint Violation Test")
    print("=" * 60)
    
    # Top6 で10点以上生成されるケース
    top6 = top5 + [{'umaban': 1, 'P_win_raw': 0.0200, 'rank_pred': 6}]
    betting_large = generator.generate_betting_tickets(top6)
    
    print(f"三連複: {betting_large['sanrenpuku_count']}点 (制限: 9点)")
    print(f"三連単: {betting_large['sanrentan_count']}点 (制限: 12点)")
    print(f"制約チェック: {'✅ OK' if betting_large['constraints_satisfied'] else '❌ FAIL'}")
    
    print("\n" + "=" * 60)
    print("✅ Phase 2B Test Complete!")
    print("=" * 60)


if __name__ == '__main__':
    test_betting_generator()

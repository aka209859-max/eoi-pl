#!/usr/bin/env python3
"""
Calibration and Audit Module for EOI-PL v1.0
CEO Directive: 校正（isotonic）＋監査（ECE/MCE、RCC/AUC-RCC、tie監査、DNF除外監査）

References:
- Calibration: https://scikit-learn.org/stable/modules/calibration.html
- Risk-Coverage: https://aclanthology.org/2021.acl-long.84.pdf
"""

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import roc_auc_score
from typing import List, Dict, Tuple
import json


class CalibrationAuditor:
    """校正と監査を実行"""
    
    def __init__(self):
        self.calibrator = None
        self.audit_log = {}
    
    def fit_isotonic_calibration(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict:
        """
        Isotonic Regression で確率校正
        
        Args:
            y_true: 実際の結果 (0 or 1)
            y_pred: 予測確率
        
        Returns:
            校正結果の監査ログ
        """
        self.calibrator = IsotonicRegression(out_of_bounds='clip')
        y_calibrated = self.calibrator.fit_transform(y_pred, y_true)
        
        # 校正前後のECE/MCE計算
        ece_before = self.calculate_ece(y_true, y_pred)
        mce_before = self.calculate_mce(y_true, y_pred)
        ece_after = self.calculate_ece(y_true, y_calibrated)
        mce_after = self.calculate_mce(y_true, y_calibrated)
        
        audit = {
            'method': 'isotonic_regression',
            'samples': int(len(y_true)),
            'ece_before': float(ece_before),
            'mce_before': float(mce_before),
            'ece_after': float(ece_after),
            'mce_after': float(mce_after),
            'improvement_ece': float(ece_before - ece_after),
            'improvement_mce': float(mce_before - mce_after)
        }
        
        return audit
    
    def transform(self, y_pred: np.ndarray) -> np.ndarray:
        """校正済み確率を返す"""
        if self.calibrator is None:
            raise ValueError("Calibrator not fitted. Call fit_isotonic_calibration first.")
        return self.calibrator.transform(y_pred)
    
    def calculate_ece(self, y_true: np.ndarray, y_pred: np.ndarray, n_bins: int = 10) -> float:
        """
        Expected Calibration Error (ECE)
        
        ECE = Σ (|P(bin)| / N) * |accuracy(bin) - confidence(bin)|
        """
        bin_edges = np.linspace(0, 1, n_bins + 1)
        ece = 0.0
        
        for i in range(n_bins):
            bin_mask = (y_pred >= bin_edges[i]) & (y_pred < bin_edges[i + 1])
            if np.sum(bin_mask) > 0:
                bin_accuracy = np.mean(y_true[bin_mask])
                bin_confidence = np.mean(y_pred[bin_mask])
                bin_weight = np.sum(bin_mask) / len(y_true)
                ece += bin_weight * abs(bin_accuracy - bin_confidence)
        
        return ece
    
    def calculate_mce(self, y_true: np.ndarray, y_pred: np.ndarray, n_bins: int = 10) -> float:
        """
        Maximum Calibration Error (MCE)
        
        MCE = max |accuracy(bin) - confidence(bin)|
        """
        bin_edges = np.linspace(0, 1, n_bins + 1)
        mce = 0.0
        
        for i in range(n_bins):
            bin_mask = (y_pred >= bin_edges[i]) & (y_pred < bin_edges[i + 1])
            if np.sum(bin_mask) > 0:
                bin_accuracy = np.mean(y_true[bin_mask])
                bin_confidence = np.mean(y_pred[bin_mask])
                mce = max(mce, abs(bin_accuracy - bin_confidence))
        
        return mce
    
    def calculate_rcc_auc(self, y_true: np.ndarray, y_pred: np.ndarray, 
                          thresholds: List[float] = None) -> Dict:
        """
        Risk-Coverage Curve (RCC) と AUC-RCC
        
        Args:
            y_true: 実際の結果 (0 or 1)
            y_pred: 予測確率
            thresholds: リスク閾値のリスト
        
        Returns:
            RCC監査ログ
        """
        if thresholds is None:
            thresholds = np.linspace(0, 1, 21)  # 0.0, 0.05, ..., 1.0
        
        rcc_points = []
        for threshold in thresholds:
            mask = y_pred >= threshold
            if np.sum(mask) > 0:
                coverage = np.sum(mask) / len(y_true)
                risk = 1 - np.mean(y_true[mask])
                rcc_points.append({
                    'threshold': float(threshold),
                    'coverage': float(coverage),
                    'risk': float(risk)
                })
        
        # AUC-RCC計算（台形則）
        if len(rcc_points) > 1:
            coverages = [p['coverage'] for p in rcc_points]
            risks = [p['risk'] for p in rcc_points]
            auc_rcc = np.trapz(risks, coverages)
        else:
            auc_rcc = 0.0
        
        return {
            'rcc_points': rcc_points[:10],  # 最初の10点のみ保存
            'auc_rcc': float(auc_rcc),
            'num_points': len(rcc_points)
        }
    
    def audit_ties(self, ranks: np.ndarray) -> Dict:
        """
        同着（tie）の監査
        
        Args:
            ranks: 着順の配列
        
        Returns:
            tie監査ログ
        """
        unique_ranks, counts = np.unique(ranks, return_counts=True)
        ties = counts[counts > 1]
        
        return {
            'total_entries': int(len(ranks)),
            'unique_ranks': int(len(unique_ranks)),
            'tie_count': int(len(ties)),
            'tie_rate': float(len(ties) / len(unique_ranks)) if len(unique_ranks) > 0 else 0.0,
            'max_tie_size': int(np.max(ties)) if len(ties) > 0 else 0
        }
    
    def audit_dnf_exclusions(self, exclusion_records: List[Dict]) -> Dict:
        """
        DNF除外の監査
        
        Args:
            exclusion_records: 除外記録のリスト
                [{'race_id': ..., 'umaban': ..., 'reason': ...}, ...]
        
        Returns:
            DNF除外監査ログ
        """
        reasons = {}
        for record in exclusion_records:
            reason = record.get('reason', 'unknown')
            reasons[reason] = reasons.get(reason, 0) + 1
        
        return {
            'total_exclusions': len(exclusion_records),
            'exclusion_by_reason': reasons,
            'sample_exclusions': exclusion_records[:5]  # 最初の5件
        }


def test_calibration_auditor():
    """テストケース"""
    print("=" * 60)
    print("Phase 2C: Calibration & Audit Test")
    print("=" * 60)
    
    # テストデータ生成
    np.random.seed(42)
    n_samples = 1000
    
    # 未校正の予測確率（やや過信気味）
    y_pred = np.random.beta(2, 5, n_samples)
    y_true = (np.random.rand(n_samples) < y_pred * 0.8).astype(int)  # 実際は少し低い
    
    auditor = CalibrationAuditor()
    
    # 1. 校正
    print("\n1️⃣ Isotonic Calibration")
    calibration_audit = auditor.fit_isotonic_calibration(y_true, y_pred)
    print(f"  Samples: {calibration_audit['samples']}")
    print(f"  ECE (before): {calibration_audit['ece_before']:.4f}")
    print(f"  ECE (after):  {calibration_audit['ece_after']:.4f}")
    print(f"  MCE (before): {calibration_audit['mce_before']:.4f}")
    print(f"  MCE (after):  {calibration_audit['mce_after']:.4f}")
    print(f"  Improvement ECE: {calibration_audit['improvement_ece']:.4f}")
    
    # 2. RCC/AUC-RCC
    print("\n2️⃣ Risk-Coverage Curve")
    y_calibrated = auditor.transform(y_pred)
    rcc_audit = auditor.calculate_rcc_auc(y_true, y_calibrated)
    print(f"  AUC-RCC: {rcc_audit['auc_rcc']:.4f}")
    print(f"  RCC Points: {rcc_audit['num_points']}")
    print(f"  Sample (threshold=0.2): coverage={rcc_audit['rcc_points'][4]['coverage']:.3f}, risk={rcc_audit['rcc_points'][4]['risk']:.3f}")
    
    # 3. Tie監査
    print("\n3️⃣ Tie Audit")
    ranks = np.random.randint(1, 10, 100)
    ranks[10:15] = 5  # 5位に5頭の同着
    tie_audit = auditor.audit_ties(ranks)
    print(f"  Total entries: {tie_audit['total_entries']}")
    print(f"  Tie count: {tie_audit['tie_count']}")
    print(f"  Tie rate: {tie_audit['tie_rate']:.2%}")
    print(f"  Max tie size: {tie_audit['max_tie_size']}")
    
    # 4. DNF除外監査
    print("\n4️⃣ DNF Exclusion Audit")
    exclusions = [
        {'race_id': '2024_0101_45_01', 'umaban': 3, 'reason': 'missing_rank'},
        {'race_id': '2024_0101_45_02', 'umaban': 7, 'reason': 'missing_rank'},
        {'race_id': '2024_0101_45_03', 'umaban': 12, 'reason': 'status_keyword:中止'},
    ]
    dnf_audit = auditor.audit_dnf_exclusions(exclusions)
    print(f"  Total exclusions: {dnf_audit['total_exclusions']}")
    print(f"  By reason: {dnf_audit['exclusion_by_reason']}")
    
    # 統合監査ログ
    full_audit = {
        'calibration': calibration_audit,
        'selection': rcc_audit,
        'ties': tie_audit,
        'dnf_exclusions': dnf_audit
    }
    
    # JSON保存
    with open('/home/user/eoi-pl/data/audit_phase2c_test.json', 'w') as f:
        json.dump(full_audit, f, indent=2)
    
    print("\n✅ Audit log saved to data/audit_phase2c_test.json")
    print("\n" + "=" * 60)
    print("✅ Phase 2C Test Complete!")
    print("=" * 60)


if __name__ == '__main__':
    test_calibration_auditor()

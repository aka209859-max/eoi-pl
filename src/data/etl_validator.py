#!/usr/bin/env python3
"""
EOI-PL v1.0-Prime: ETL & Forbidden検出
- odds/人気系カラムの検出 → 即停止
- DNF/中止/除外/失格の除外 (方針B)
- data_hash 生成
"""

import pandas as pd
import numpy as np
import psycopg2
import hashlib
import json
from datetime import datetime

class NumpyEncoder(json.JSONEncoder):
    """JSON encoder for numpy types"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

class DataValidator:
    """データ検証エンジン"""
    
    # 禁止キーワード（CEO確定）
    FORBIDDEN_KEYWORDS = [
        'odds', 'オッズ', 'ninki', '人気', 'popularity',
        'tansho_odds', 'fukusho_odds', 'umaren_odds',
        'wide_odds', 'umatan_odds', 'sanrenpuku_odds', 'sanrentan_odds',
        'tansho_ninki', 'fukusho_ninki'
    ]
    
    # 除外キーワード（DNF/中止/除外/失格）
    EXCLUSION_KEYWORDS = [
        '中止', '除外', '失格', '取消', '競走中止',
        'DQ', 'DNF', 'SCR', 'DISQ', '出走取消'
    ]
    
    # ステータス列候補（列名揺れ対応）
    STATUS_COLUMN_CANDIDATES = [
        'status', 'result_status', 'race_status', 'remarks',
        'disq_flag', 'joken', 'biko', 'memo'
    ]
    
    def __init__(self, conn):
        self.conn = conn
        self.exclusion_log = []
    
    def validate_no_forbidden_columns(self, df, source_name):
        """
        禁止カラム検出 → 即停止
        """
        print(f"🔍 Validating {source_name} for forbidden columns...")
        
        forbidden_found = []
        for col in df.columns:
            for keyword in self.FORBIDDEN_KEYWORDS:
                if keyword.lower() in col.lower():
                    forbidden_found.append({
                        'column': col,
                        'keyword': keyword
                    })
        
        if forbidden_found:
            error_msg = f"🚨 FORBIDDEN COLUMNS DETECTED in {source_name}:\n"
            for item in forbidden_found:
                error_msg += f"  - Column: '{item['column']}' (matched: '{item['keyword']}')\n"
            error_msg += "\n❌ SYSTEM HALTED for compliance violation."
            raise ValueError(error_msg)
        
        print(f"✅ No forbidden columns in {source_name}")
    
    def detect_status_column(self, df):
        """
        ステータス列を自動検出（列名揺れ対応）
        """
        for candidate in self.STATUS_COLUMN_CANDIDATES:
            if candidate in df.columns:
                print(f"✅ Status column detected: '{candidate}'")
                return candidate
        
        print("⚠️  No status column found (will use missing rank only)")
        return None
    
    def exclude_dnf_and_disqualified(self, df):
        """
        DNF/中止/除外/失格を除外（方針B）
        
        除外条件:
        1. kakutei_chakujun が NULL/0/負の値
        2. status列に除外キーワードが含まれる
        
        Returns:
        --------
        df_clean: 除外後のDataFrame
        exclusion_audit: 除外監査情報
        """
        print("\n🔍 Excluding DNF/disqualified entries...")
        
        original_count = len(df)
        exclusion_reasons = []
        
        # 1. 着順欠損/0/負の値を除外
        invalid_rank_mask = (
            df['kakutei_chakujun'].isnull() |
            (df['kakutei_chakujun'] <= 0)
        )
        
        if invalid_rank_mask.sum() > 0:
            excluded_races = df[invalid_rank_mask]['race_id'].unique()
            exclusion_reasons.append({
                'reason': 'missing_or_invalid_rank',
                'count': invalid_rank_mask.sum(),
                'sample_race_ids': excluded_races[:5].tolist()
            })
            print(f"  - Excluded {invalid_rank_mask.sum()} entries (missing/invalid rank)")
        
        df_clean = df[~invalid_rank_mask].copy()
        
        # 2. ステータス列による除外
        status_col = self.detect_status_column(df_clean)
        
        if status_col is not None:
            status_exclusion_mask = df_clean[status_col].apply(
                lambda x: any(kw in str(x) for kw in self.EXCLUSION_KEYWORDS) 
                if pd.notna(x) else False
            )
            
            if status_exclusion_mask.sum() > 0:
                excluded_races = df_clean[status_exclusion_mask]['race_id'].unique()
                exclusion_reasons.append({
                    'reason': f'status_keyword_match (column: {status_col})',
                    'count': status_exclusion_mask.sum(),
                    'sample_race_ids': excluded_races[:5].tolist(),
                    'keywords': self.EXCLUSION_KEYWORDS
                })
                print(f"  - Excluded {status_exclusion_mask.sum()} entries (status keywords)")
            
            df_clean = df_clean[~status_exclusion_mask].copy()
        
        final_count = len(df_clean)
        excluded_count = original_count - final_count
        
        print(f"✅ Exclusion complete: {excluded_count}/{original_count} excluded")
        
        exclusion_audit = {
            'original_count': original_count,
            'excluded_count': excluded_count,
            'final_count': final_count,
            'exclusion_rate': excluded_count / original_count if original_count > 0 else 0.0,
            'reasons': exclusion_reasons
        }
        
        return df_clean, exclusion_audit
    
    def compute_data_hash(self, df):
        """
        データハッシュ計算（freeze再現性保証）
        """
        # race_id と umaban と kakutei_chakujun をソートしてハッシュ化
        key_columns = ['race_id', 'umaban', 'kakutei_chakujun']
        df_sorted = df[key_columns].sort_values(key_columns).reset_index(drop=True)
        
        data_string = df_sorted.to_csv(index=False)
        data_hash = hashlib.sha256(data_string.encode()).hexdigest()
        
        print(f"✅ Data hash: sha256:{data_hash[:16]}...")
        return f"sha256:{data_hash}"
    
    def load_and_validate_data(self, limit_date=None):
        """
        データ読み込み + 検証 + 除外処理
        """
        print("\n" + "="*60)
        print("📥 Loading and validating data...")
        print("="*60)
        
        # クエリ構築
        query = """
            SELECT 
                r.race_id,
                r.kaisai_nen,
                r.kaisai_tsukihi,
                r.keibajo_code,
                r.race_bango,
                r.kyori,
                r.track_code,
                r.babajotai_code_dirt,
                r.kyoso_joken_code,
                r.tosu,
                e.umaban,
                e.wakuban,
                e.bamei,
                e.bataiju,
                e.kakutei_chakujun,
                e.soha_time,
                e.corner_1,
                e.corner_2,
                e.corner_3,
                e.corner_4,
                e.kohan_3f,
                e.ketto_toroku_bango,
                e.kishu_code,
                e.chokyoshi_code
            FROM races r
            INNER JOIN entries e ON r.race_id = e.race_id
        """
        
        # 学習用データは2024年のみ（高速化）
        if limit_date:
            query += f" WHERE r.kaisai_nen = 2024"
        else:
            query += " WHERE r.kaisai_nen >= 2024"
        
        query += " ORDER BY r.kaisai_nen, r.kaisai_tsukihi, r.race_id, e.umaban"
        
        df = pd.read_sql(query, self.conn)
        print(f"✅ Loaded {len(df):,} entries from database")
        
        # 禁止カラム検証
        self.validate_no_forbidden_columns(df, "database query result")
        
        # DNF/除外処理
        df_clean, exclusion_audit = self.exclude_dnf_and_disqualified(df)
        
        # データハッシュ計算
        data_hash = self.compute_data_hash(df_clean)
        
        # 監査情報
        audit_info = {
            'data_hash': data_hash,
            'exclusion_audit': exclusion_audit,
            'data_quality': {
                'total_races': int(df_clean['race_id'].nunique()),
                'total_entries': int(len(df_clean)),
                'date_range': {
                    'min': int(df_clean['kaisai_nen'].min()),
                    'max': int(df_clean['kaisai_nen'].max())
                },
                'join_rate': 1.0,  # INNER JOIN なので 100%
                'missing_rates': {
                    col: float(df_clean[col].isnull().mean())
                    for col in ['bataiju', 'corner_1', 'kohan_3f']
                }
            }
        }
        
        print(f"\n📊 Data Quality Summary:")
        print(f"  - Total races: {audit_info['data_quality']['total_races']:,}")
        print(f"  - Total entries: {audit_info['data_quality']['total_entries']:,}")
        print(f"  - Exclusion rate: {exclusion_audit['exclusion_rate']:.2%}")
        
        return df_clean, audit_info


if __name__ == "__main__":
    # データベース接続
    conn = psycopg2.connect(
        host="localhost",
        database="eoi_pl",
        user="postgres",
        password="eoi_pl_dev"
    )
    
    try:
        validator = DataValidator(conn)
        
        # データ読み込み + 検証（学習用: 2024年まで）
        df_train, audit_train = validator.load_and_validate_data(limit_date=20241231)
        
        # 保存
        df_train.to_parquet("/home/user/eoi-pl/data/training_clean.parquet", index=False)
        
        with open("/home/user/eoi-pl/data/audit_etl.json", 'w') as f:
            json.dump(audit_train, f, indent=2, cls=NumpyEncoder)
        
        print("\n" + "="*60)
        print("✅ ETL & Validation completed")
        print("="*60)
        print(f"  - Clean data: /home/user/eoi-pl/data/training_clean.parquet")
        print(f"  - Audit log:  /home/user/eoi-pl/data/audit_etl.json")
        
    finally:
        conn.close()

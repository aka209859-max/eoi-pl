-- EOI-PL v1.0-Prime Database Schema
-- PostgreSQL用DDL

-- レース基本情報テーブル
CREATE TABLE IF NOT EXISTS races (
    race_id VARCHAR(50) PRIMARY KEY,
    kaisai_nen INTEGER NOT NULL,
    kaisai_tsukihi INTEGER NOT NULL,
    keibajo_code INTEGER NOT NULL,
    race_bango INTEGER NOT NULL,
    kyori INTEGER,  -- 距離
    track_code INTEGER,  -- トラック種別
    babajotai_code_dirt INTEGER,  -- 馬場状態（ダート）
    kyoso_joken_code INTEGER,  -- 競走条件
    hassoujikoku INTEGER,  -- 発走時刻
    tosu INTEGER,  -- 頭数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango)
);

-- エントリー・結果テーブル
CREATE TABLE IF NOT EXISTS entries (
    entry_id SERIAL PRIMARY KEY,
    race_id VARCHAR(50) NOT NULL REFERENCES races(race_id),
    umaban INTEGER NOT NULL,  -- 馬番
    bamei VARCHAR(100),  -- 馬名
    wakuban INTEGER,  -- 枠番
    bataiju FLOAT,  -- 馬体重
    kakutei_chakujun INTEGER,  -- 確定着順（目的変数）
    soha_time FLOAT,  -- 走破タイム
    corner_1 INTEGER,  -- コーナー通過順位1
    corner_2 INTEGER,
    corner_3 INTEGER,
    corner_4 INTEGER,
    kohan_3f FLOAT,  -- 後半3ハロン
    ketto_toroku_bango BIGINT,  -- 血統登録番号
    kishu_code INTEGER,  -- 騎手コード
    chokyoshi_code INTEGER,  -- 調教師コード
    fufu_ketto_toroku_bango BIGINT,  -- 父父血統登録番号
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(race_id, umaban)
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_races_date ON races(kaisai_nen, kaisai_tsukihi);
CREATE INDEX IF NOT EXISTS idx_races_venue ON races(keibajo_code);
CREATE INDEX IF NOT EXISTS idx_entries_race_id ON entries(race_id);
CREATE INDEX IF NOT EXISTS idx_entries_horse ON entries(ketto_toroku_bango);
CREATE INDEX IF NOT EXISTS idx_entries_jockey ON entries(kishu_code);
CREATE INDEX IF NOT EXISTS idx_entries_trainer ON entries(chokyoshi_code);

-- 統計情報
COMMENT ON TABLE races IS 'レース基本情報（2020-2025）';
COMMENT ON TABLE entries IS 'エントリー・結果情報（オッズ/人気なし）';
COMMENT ON COLUMN entries.kakutei_chakujun IS '目的変数：複勝確率を予測する';

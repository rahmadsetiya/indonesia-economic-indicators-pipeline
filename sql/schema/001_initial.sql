CREATE TABLE IF NOT EXISTS dim_indicator (
    indicator_id BIGSERIAL PRIMARY KEY,
    indicator_code TEXT NOT NULL UNIQUE,
    indicator_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_geography (
    geography_id BIGSERIAL PRIMARY KEY,
    geography_code TEXT NOT NULL UNIQUE,
    geography_name TEXT NOT NULL,
    geography_level TEXT NOT NULL CHECK (geography_level IN ('national', 'province', 'regency_city'))
);

CREATE TABLE IF NOT EXISTS dim_unit (
    unit_id BIGSERIAL PRIMARY KEY,
    unit_code TEXT NOT NULL UNIQUE,
    unit_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_source (
    source_id BIGSERIAL PRIMARY KEY,
    institution TEXT NOT NULL,
    dataset_code TEXT NOT NULL,
    dataset_name TEXT NOT NULL,
    source_url TEXT NOT NULL,
    access_method TEXT NOT NULL,
    UNIQUE (institution, dataset_code)
);

CREATE TABLE IF NOT EXISTS source_retrieval (
    retrieval_id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL REFERENCES dim_source(source_id),
    retrieved_at TIMESTAMPTZ NOT NULL,
    raw_file_path TEXT NOT NULL,
    checksum_sha256 CHAR(64) NOT NULL,
    http_status INTEGER,
    UNIQUE (source_id, retrieved_at, checksum_sha256)
);

CREATE TABLE IF NOT EXISTS fact_indicator_observation (
    observation_id BIGSERIAL PRIMARY KEY,
    indicator_id BIGINT NOT NULL REFERENCES dim_indicator(indicator_id),
    geography_id BIGINT NOT NULL REFERENCES dim_geography(geography_id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    frequency TEXT NOT NULL CHECK (frequency IN ('daily', 'monthly', 'quarterly', 'semiannual', 'annual', 'event')),
    value NUMERIC NOT NULL,
    unit_id BIGINT NOT NULL REFERENCES dim_unit(unit_id),
    seasonal_adjustment TEXT NOT NULL DEFAULT '',
    price_basis TEXT NOT NULL DEFAULT '',
    source_id BIGINT NOT NULL REFERENCES dim_source(source_id),
    retrieval_id BIGINT NOT NULL REFERENCES source_retrieval(retrieval_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (period_end >= period_start),
    UNIQUE (
        indicator_id, geography_id, period_start, period_end, frequency,
        unit_id, seasonal_adjustment, price_basis, source_id
    )
);

CREATE INDEX IF NOT EXISTS ix_observation_period
    ON fact_indicator_observation (period_start, period_end);

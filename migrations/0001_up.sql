START TRANSACTION ISOLATION LEVEL SERIALIZABLE;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

UPDATE migration SET version='0001';

CREATE TABLE activities (
    id BIGSERIAL PRIMARY KEY,

    fitfile_name TEXT UNIQUE,
    created TIMESTAMP WITH TIME ZONE,

    user_gender TEXT,
    user_height_meters REAL,
    user_resting_heart_rate SMALLINT,
    user_max_heart_rate SMALLINT,
    user_sleep_time TIME,
    user_running_step_length_meters REAL,
    user_walking_step_length_meters REAL,
    user_wake_time TIME,
    user_weight_kg REAL,

    device_manufacturer TEXT,
    device_product_number TEXT,
    device_serial_number TEXT,

    sport TEXT,
    sub_sport TEXT
);

CREATE TABLE timer_events (
    id BIGSERIAL PRIMARY KEY,
    activity_id BIGINT NOT NULL REFERENCES activities(id) ON UPDATE CASCADE ON DELETE CASCADE,
    message_id BIGINT NOT NULL,
    event_type VARCHAR(32) NOT NULL,
    timer_trigger VARCHAR(32) NOT NULL,
    created TIMESTAMP WITH TIME ZONE NOT NULL,
    UNIQUE (activity_id, message_id)
);

CREATE TABLE fields (
    id BIGSERIAL PRIMARY KEY,
    field_name TEXT,
    field_units TEXT,
    UNIQUE (field_name, field_units)
);

CREATE TABLE samples (
    id BIGSERIAL PRIMARY KEY,
    activity_id BIGINT NOT NULL REFERENCES activities(id) ON UPDATE CASCADE ON DELETE CASCADE,
    message_id BIGINT NOT NULL,
    sampled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    UNIQUE (activity_id, message_id)
);

CREATE TABLE sample_values (
    id BIGSERIAL PRIMARY KEY,
    sample_id BIGINT NOT NULL REFERENCES samples(id) ON UPDATE CASCADE ON DELETE CASCADE,
    field_id BIGINT NOT NULL REFERENCES fields(id) ON UPDATE CASCADE ON DELETE CASCADE,
    int_value BIGINT,
    float_value REAL,
    UNIQUE (sample_id, field_id)
);

COMMIT;

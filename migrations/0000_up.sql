START TRANSACTION ISOLATION LEVEL SERIALIZABLE;

CREATE TABLE migration (
    version text
);

INSERT INTO migration (version) VALUES ('0000');

COMMIT;
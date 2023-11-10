-- 
-- depends: gh_auto_20230903_01_2RSsI

-- Reason:
-- Sometimes, the cadastral URL is there, but some of the values are missing.

ALTER TABLE property_cadastral_data
    ALTER COLUMN value_min DROP NOT NULL,
    ALTER COLUMN value_max DROP NOT NULL,
    ALTER COLUMN value_calculated_on DROP NOT NULL;

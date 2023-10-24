--
-- depends:

-- availability enum
CREATE TYPE availability AS ENUM ('available', 'negotiated', 'sold');

-- energy labels
CREATE TYPE energy_label AS ENUM ('A+++++', 'A++++', 'A+++', 'A++', 'A+', 'A', 'B', 'C', 'D', 'E', 'F', 'G');

CREATE TABLE IF NOT EXISTS property (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address VARCHAR(255) NOT NULL,
    city VARCHAR(255) NOT NULL,
    postal_code VARCHAR(255) NOT NULL,
    latitude DECIMAL(10,8) NOT NULL,
    longitude DECIMAL(11,8) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    funda_data_id INTEGER UNIQUE NOT NULL,
    cadastral_data_id INTEGER UNIQUE NOT NULL,
    FOREIGN KEY (funda_data_id) REFERENCES property_funda_data(id),
    FOREIGN KEY (cadastral_data_id) REFERENCES property_cadastral_data(id)
);

COMMENT ON COLUMN property.name IS 'The name of the property.';
COMMENT ON COLUMN property.address IS 'The address of the property.';
COMMENT ON COLUMN property.city IS 'The city of the property.';
COMMENT ON COLUMN property.postal_code IS 'The postal code of the property.';
COMMENT ON COLUMN property.latitude IS 'The latitude of the property.';
COMMENT ON COLUMN property.longitude IS 'The longitude of the property.';
COMMENT ON COLUMN property.created_at IS 'The creation date of the property.';
COMMENT ON COLUMN property.updated_at IS 'The last update date of the property.';
COMMENT ON COLUMN property.funda_data_id IS 'The ID of the Funda.nl data of the property.';
COMMENT ON COLUMN property.cadastral_data_id IS 'The ID of the cadastral data of the property.';


CREATE TABLE IF NOT EXISTS property_funda_data (
    id SERIAL PRIMARY KEY,
    property_id INTEGER NOT NULL,
    url VARCHAR(1023) UNIQUE NOT NULL,
    asking_price DECIMAL(10,2) NOT NULL CHECK (asking_price > 0),
    price_per_m2 DECIMAL(10,2) NOT NULL CHECK (price_per_m2 > 0),
    availability_status availability NOT NULL,
    offered_since DATE NOT NULL,
    year_built INTEGER NOT NULL CHECK (year_built > 1800 AND year_built < 2100),
    area_to_live INTEGER NOT NULL CHECK (area_to_live > 0),
    area_of_plot INTEGER NOT NULL CHECK (area_of_plot > 0),
    area_of_frontyard INTEGER NOT NULL CHECK (area_of_frontyard >= 0),
    area_of_backyard INTEGER NOT NULL CHECK (area_of_backyard >= 0),
    volume INTEGER NOT NULL CHECK (volume > 0),
    number_of_rooms INTEGER NOT NULL CHECK (number_of_rooms > 0),
    number_of_floors INTEGER NOT NULL CHECK (number_of_floors > 0),
    energy_label energy_label NOT NULL,
    FOREIGN KEY (property_id) REFERENCES property(id)
);

COMMENT ON COLUMN property_funda_data.url IS 'The Funda.nl URL of the property.';
COMMENT ON COLUMN property_funda_data.asking_price IS 'The asking price of the property.';
COMMENT ON COLUMN property_funda_data.price_per_m2 IS 'The price per square meter of the property.';
COMMENT ON COLUMN property_funda_data.availability_status IS 'The availability status of the property.';
COMMENT ON COLUMN property_funda_data.offered_since IS 'The date the property was offered for sale.';
COMMENT ON COLUMN property_funda_data.year_built IS 'The year the property was built.';
COMMENT ON COLUMN property_funda_data.area_to_live IS 'The living area of the property, in m2.';
COMMENT ON COLUMN property_funda_data.area_of_plot IS 'The area of the plot of the property, in m2.';
COMMENT ON COLUMN property_funda_data.area_of_frontyard IS 'The area of the frontyard of the property.';
COMMENT ON COLUMN property_funda_data.area_of_backyard IS 'The area of the backyard of the property.';
COMMENT ON COLUMN property_funda_data.volume IS 'The volume of the property, in m3.';
COMMENT ON COLUMN property_funda_data.number_of_rooms IS 'The number of rooms of the property.';
COMMENT ON COLUMN property_funda_data.number_of_floors IS 'The number of floors of the property.';
COMMENT ON COLUMN property_funda_data.energy_label IS 'The energy label of the property.';


CREATE TABLE IF NOT EXISTS property_funda_image (
    id SERIAL PRIMARY KEY,
    funda_data_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    image_url VARCHAR(1023) UNIQUE NOT NULL,
    FOREIGN KEY (funda_data_id) REFERENCES property_funda_data(id)
);

COMMENT ON COLUMN property_funda_image.name IS 'The name of the image.';
COMMENT ON COLUMN property_funda_image.image_url IS 'The Funda.nl URL of the image.';


CREATE TABLE IF NOT EXISTS property_cadastral_data (
    id SERIAL PRIMARY KEY,
    property_id INTEGER NOT NULL,
    cadastral_url VARCHAR(1023) UNIQUE NOT NULL,
    woz_url VARCHAR(1023) UNIQUE NOT NULL,
    value_min DECIMAL(10,2) NOT NULL CHECK (value_min > 0),
    value_max DECIMAL(10,2) NOT NULL CHECK (value_max > 0),
    value_calculated_on DATE NOT NULL,
    FOREIGN KEY (property_id) REFERENCES property(id)
);

COMMENT ON COLUMN property_cadastral_data.cadastral_url IS 'The kadasterdata.nl URL of the property.';
COMMENT ON COLUMN property_cadastral_data.woz_url IS 'The WOZ URL of the property.';
COMMENT ON COLUMN property_cadastral_data.value_min IS 'The minimum value of the property.';
COMMENT ON COLUMN property_cadastral_data.value_max IS 'The maximum value of the property.';
COMMENT ON COLUMN property_cadastral_data.value_calculated_on IS 'The date the value was calculated.';


CREATE TABLE IF NOT EXISTS property_cadastral_woz (
    id SERIAL PRIMARY KEY,
    property_cadastral_id INTEGER NOT NULL,
    year INTEGER NOT NULL CHECK (year > 1800 AND year < 2100),
    effective_date DATE NOT NULL,
    reference_date DATE NOT NULL,
    value DECIMAL(10,2) NOT NULL CHECK (value > 0),
    FOREIGN KEY (property_cadastral_id) REFERENCES property_cadastral_data(id)
);

COMMENT ON COLUMN property_cadastral_woz.year IS 'The year the WOZ value was calculated.';
COMMENT ON COLUMN property_cadastral_woz.effective_date IS 'The effective date of the WOZ value.';
COMMENT ON COLUMN property_cadastral_woz.reference_date IS 'The reference date of the WOZ value.';
COMMENT ON COLUMN property_cadastral_woz.value IS 'The WOZ value of the property.';

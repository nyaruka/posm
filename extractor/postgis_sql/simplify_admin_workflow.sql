-- create extension postgis;
-- create extension postgis_topology;

set search_path = "$user",'public','topology';

-- deconstruct geometry
SELECT deconstruct_geometry(); -- fill_holes BOOLEAN DEFAULT 't'

SELECT create_base_topology();
SELECT create_state_topology();
SELECT create_country_topology();

SELECT create_simple_geoms(); -- tolerance float DEFAULT 0.1 of a degree


-- create views of every country (in admin_level_0) and every other admin_level in the country
CREATE VIEW simple_admin_0_view AS

SELECT ad0.osm_id, ad0.name, sa0.wkb_geometry, ad0.wkb_geometry as natural_wkb_geometry
FROM admin_level_0 ad0 INNER JOIN simple_admin_0 sa0 ON ad0.osm_id = sa0.osm_id;


CREATE VIEW simple_admin_1_view AS

SELECT ad1.osm_id, ad1.name, sa1.wkb_geometry, ad0.osm_id as is_in_country, ad1.wkb_geometry as natural_wkb_geometry
FROM admin_level_0 ad0 INNER JOIN admin_level_1 ad1 ON ad0.osm_id = ad1.is_in
    INNER JOIN simple_admin_1 sa1 ON ad1.osm_id = sa1.osm_id;

CREATE VIEW simple_admin_2_view AS

SELECT ad2.osm_id, ad2.name, sa2.wkb_geometry, ad0.osm_id as is_in_country, ad1.osm_id as is_in_state, ad2.wkb_geometry as natural_wkb_geometry
FROM admin_level_0 ad0 INNER JOIN admin_level_1 ad1 ON ad0.osm_id = ad1.is_in
    INNER JOIN admin_level_2 ad2 ON ad1.osm_id = ad2.is_in
    INNER JOIN simple_admin_2 sa2 ON ad2.osm_id = sa2.osm_id;

-- create extension postgis;
-- create extension postgis_topology;

set search_path = "$user",'public','topology';

-- deconstruct geometry
SELECT deconstruct_geometry(); -- fill_holes BOOLEAN DEFAULT 't'

SELECT create_base_topology();
-- SELECT create_state_topology();
-- SELECT create_country_topology();

-- SELECT create_simple_geoms(0.02, '{"192787"}'); -- tolerance float DEFAULT 0.1 of a degree

select simplify_dissolve(0.01)--,'{"192787"}')


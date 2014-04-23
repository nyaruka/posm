create extension postgis;
create extension postgis_topology;

set search_path = "$user",'public','topology';

-- deconstruct geometry
SELECT deconstruct_geometry(); -- 2100

SELECT create_base_topology();
SELECT create_state_topology();
SELECT create_country_topology();


-- SELECT layer_id from topology.layer where feature_column = 'topo_state'
-- SELECT id from topology.topology where name = 'admin_topo';

SELECT create_simple_geoms();

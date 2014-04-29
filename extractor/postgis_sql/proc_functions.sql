create or replace function create_base_topology() RETURNS VOID AS
$$
DECLARE
t_count INTEGER;
t_current INTEGER;
rec record;
BEGIN
t_current := 1;

PERFORM DropTopology('admin_topo');
PERFORM CreateTopology('admin_topo', 4326);
PERFORM AddTopoGeometryColumn('admin_topo', 'public', 'all_geom', 'topo', 'MULTIPOLYGON');

select count(*) INTO t_count FROM all_geom;

FOR rec in SELECT * FROM all_geom order by osm_id ASC LOOP
	BEGIN
		UPDATE all_geom SET topo = toTopoGeom(wkb_geometry, 'admin_topo', (SELECT layer_id from topology.layer where feature_column = 'topo'))
		WHERE osm_id = rec.osm_id;
	EXCEPTION
		WHEN OTHERS THEN
			RAISE WARNING 'Topology generation failed, removing feature % - %', rec.osm_id, SQLERRM;
			DELETE FROM all_geom WHERE osm_id = rec.osm_id;
	END;
	RAISE NOTICE 'Done %/% - %', t_current, t_count, rec.osm_id;
	t_current:=t_current + 1;
END LOOP;
END;
$$
LANGUAGE 'plpgsql' VOLATILE STRICT;

create or replace function create_state_topology() RETURNS VOID AS
$$
BEGIN

-- SELECT DropTopoGeometryColumn('public', 'all_geom', 'topo_state');

-- create state_topology
PERFORM AddTopoGeometryColumn('admin_topo', 'public', 'all_geom', 'topo_state', 'MULTIPOLYGON', (SELECT layer_id from topology.layer where feature_column = 'topo')); -- id = 2

update all_geom as ag SET topo_state = topology.CreateTopoGeom(
  'admin_topo', -- topo name
  3, -- topo type 
  (SELECT layer_id from topology.layer where feature_column = 'topo_state'),
  inner_query.bfaces)
 FROM (SELECT b.is_in_state, topology.TopoElementArray_Agg(ARRAY[(topo).id, (SELECT layer_id from topology.layer where feature_column = 'topo')]) As bfaces -- 1 == parent topo
FROM all_geom As b inner join admin_level_1 on b.is_in_state = admin_level_1.osm_id
GROUP BY b.is_in_state
) as inner_query
WHERE inner_query.is_in_state = ag.is_in_state;


update all_geom as ag SET topo_state = topology.CreateTopoGeom(
  'admin_topo', -- topo name
  3, -- topo type 
  (SELECT layer_id from topology.layer where feature_column = 'topo_state'), -- layer
  inner_query.bfaces)
FROM (SELECT b.osm_id, ARRAY[ARRAY[(topo).id, (SELECT layer_id from topology.layer where feature_column = 'topo')]]::topology.topoelementarray As bfaces -- 1 == parent topo
FROM all_geom b -- inner join admin_level_1 ON admin_level_1.osm_id = b.osm_id
where b.topo_state is null
) as inner_query
WHERE inner_query.osm_id = ag.osm_id;

END;
$$
LANGUAGE 'plpgsql' VOLATILE STRICT;

create or replace function create_country_topology() RETURNS VOID AS
$$
BEGIN
-- create country topology
PERFORM AddTopoGeometryColumn('admin_topo', 'public', 'all_geom', 'topo_country', 'MULTIPOLYGON',(SELECT layer_id from topology.layer where feature_column = 'topo_state'));

update all_geom as ag SET topo_country = topology.CreateTopoGeom(
  'admin_topo', -- topo name
  3, -- topo type 
  (SELECT layer_id from topology.layer where feature_column = 'topo_country'), -- layer
  inner_query.bfaces)
 FROM (SELECT b.is_in_country, topology.TopoElementArray_Agg(ARRAY[(topo_state).id, (SELECT layer_id from topology.layer where feature_column = 'topo_state')]) As bfaces -- 5 == parent topo
FROM all_geom As b inner join admin_level_0 on b.is_in_country = admin_level_0.osm_id

GROUP BY b.is_in_country) as inner_query
WHERE inner_query.is_in_country = ag.is_in_country;

update all_geom as ag SET topo_country = topology.CreateTopoGeom(
  'admin_topo', -- topo name
  3, -- topo type 
  (SELECT layer_id from topology.layer where feature_column = 'topo_country'), -- layer
  inner_query.bfaces)
 FROM (SELECT b.osm_id, ARRAY[ARRAY[(topo_state).id, (SELECT layer_id from topology.layer where feature_column = 'topo_state')]]::topology.topoelementarray As bfaces -- 5 == parent topo
FROM all_geom b
where topo_country is null
) as inner_query
WHERE inner_query.osm_id = ag.osm_id;
END;
$$
LANGUAGE 'plpgsql' VOLATILE STRICT;



create or replace function deconstruct_geometry(i_fill_holes BOOLEAN DEFAULT 't') RETURNS VOID AS
$$
DECLARE
rec RECORD;
t_geom GEOMETRY;
tmp_id integer;
BEGIN

-- prepare geom table
BEGIN
	DROP TABLE all_geom;
	EXCEPTION
		WHEN SQLSTATE '42P01' THEN 
END;
CREATE TABLE all_geom (osm_id varchar(255), is_in_state varchar(255), is_in_country varchar(255), adminlevel integer, wkb_geometry GEOMETRY(MULTIPOLYGON,4326));

  tmp_id:=0;

  FOR rec in SELECT * FROM admin_level_1 order by osm_id ASC LOOP
	RAISE NOTICE 'admin_level_1, %', rec.osm_id;
	BEGIN
		select st_multi(st_difference(a.wkb_geometry, (select st_union(b.wkb_geometry) from admin_level_2 b WHERE b.is_in = rec.osm_id))) INTO t_geom from admin_level_1 a where a.osm_id=rec.osm_id;
	EXCEPTION
		WHEN OTHERS THEN
			RAISE WARNING 'Cannot calculate geometry difference, skipping ...  %', SQLERRM;
			CONTINUE; -- skip this iteration, don't process this feature
	END;
	
	if ST_isempty(t_geom) THEN
		RAISE DEBUG 'Good data %', rec.osm_id;
		-- add admin_level_2 geom
		insert into all_geom SELECT osm_id, is_in, rec.is_in, adminlevel, wkb_geometry from admin_level_2 where is_in = rec.osm_id;
	ELSIF t_geom IS NULL THEN
		RAISE DEBUG 'No data %', rec.osm_id;
		-- add admin_level_1 geom
		insert into all_geom VALUES (rec.osm_id, NULL, rec.is_in, rec.adminlevel, rec.wkb_geometry);
	ELSE
		IF i_fill_holes THEN
			RAISE NOTICE 'Filling %', rec.osm_id;
			INSERT INTO all_geom VALUES ('xxx'||tmp_id::varchar, rec.osm_id, rec.is_in, rec.adminlevel, t_geom);
			tmp_id:=tmp_id+1;
		END IF;
		insert into all_geom SELECT osm_id, is_in, rec.is_in, adminlevel, wkb_geometry from admin_level_2 where is_in = rec.osm_id;
	END IF;
  END LOOP;

FOR rec IN SELECT * FROM admin_level_0 order by osm_id ASC LOOP
	RAISE NOTICE 'admin_level_0, %', rec.osm_id;
	BEGIN
		select st_multi(st_difference(rec.wkb_geometry, (
			select st_union(wkb_geometry) from all_geom where
				is_in_state in (select osm_id from admin_level_1 where is_in = rec.osm_id) OR
				osm_id in (select osm_id from admin_level_1 where is_in = rec.osm_id))))
			into t_geom from admin_level_0 a where a.osm_id=rec.osm_id;
	EXCEPTION
		WHEN OTHERS THEN
			RAISE WARNING 'Cannot calculate geometry difference, skipping ...  %', SQLERRM;
			CONTINUE; -- skip this iteration, don't process this feature
	END;

	if ST_isempty(t_geom) THEN
		RAISE DEBUG 'Good data %', rec.osm_id;
		-- add admin_level_1 geom
		 -- insert into all_geom SELECT osm_id, is_in, adminlevel, wkb_geometry from admin_level_1 where is_in = rec.osm_id;
	ELSIF t_geom IS NULL THEN
		RAISE NOTICE 'No data %', rec.osm_id;
		-- add admin_level_0 geom
		insert into all_geom VALUES (rec.osm_id, NULL, NULL, rec.adminlevel, rec.wkb_geometry);
	ELSE
		IF i_fill_holes THEN
			RAISE NOTICE 'Filling %', rec.osm_id;
			INSERT INTO all_geom VALUES ('xxx'||tmp_id::varchar, NULL, rec.osm_id, rec.adminlevel, t_geom);
			tmp_id:=tmp_id+1;
		END IF;
		-- insert into all_geom SELECT osm_id, is_in, adminlevel, wkb_geometry from admin_level_1 where is_in = rec.osm_id;
	END IF;

END LOOP;
END;
$$
LANGUAGE 'plpgsql' VOLATILE STRICT;


create or replace function create_simple_geoms(i_tolerance float DEFAULT 0.1) RETURNS VOID AS
$$
DECLARE
BEGIN

RAISE NOTICE 'Creating simple_admin_2...';
-- simplify county
BEGIN
	drop table simple_admin_2 CASCADE;
	EXCEPTION
		WHEN SQLSTATE '42P01' THEN 
		-- do nothing
END;


create table simple_admin_2 AS
select all_geom.osm_id, ST_simplify(topo, i_tolerance) as wkb_geometry from all_geom inner join admin_level_2 on all_geom.osm_id = admin_level_2.osm_id;


-- simplify state
RAISE NOTICE 'Creating simple_admin_1...';
BEGIN
	drop table simple_admin_1 CASCADE;
	EXCEPTION
		WHEN SQLSTATE '42P01' THEN 
		-- do nothing
END;

create table simple_admin_1 AS
select all_geom.osm_id
,ST_simplify(topo_state, i_tolerance) as wkb_geometry
from all_geom inner join admin_level_1 on all_geom.osm_id =admin_level_1.osm_id

UNION

select all_geom.is_in_state
,ST_simplify(topo_state, i_tolerance) as wkb_geometry
from all_geom inner join admin_level_1 on all_geom.is_in_state =admin_level_1.osm_id;

-- simplify country
RAISE NOTICE 'Creating simple_admin_0...';
BEGIN
	drop table simple_admin_0 CASCADE;
	EXCEPTION
		WHEN SQLSTATE '42P01' THEN 
		-- do nothing
END;

create table simple_admin_0 AS
select all_geom.osm_id
, ST_simplify(topo_country, i_tolerance) as wkb_geometry
from all_geom inner join admin_level_0 on all_geom.osm_id = admin_level_0.osm_id
-- 
 UNION 
-- 
select all_geom.is_in_country
,ST_simplify(topo_country, i_tolerance) as wkb_geometry
from all_geom inner join admin_level_0 on all_geom.is_in_country = admin_level_0.osm_id;


END;
$$
LANGUAGE 'plpgsql' VOLATILE STRICT;

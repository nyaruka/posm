source ./auto_update_osm.conf
CWD=$(pwd)


cd $WORKING_DIRECTORY
mv $PLANET_OSM $PLANET_OSM.last

echo "Updating planet.osm with the latest changes..."
./osmupdate -v $PLANET_OSM.last $PLANET_OSM

echo "Creating admin_level backup file..."
mv admin_levels.o5m admin_levels.o5m.last

echo "Extracting admin_levels..."
./osmfilter $PLANET_OSM --keep=admin_level -o=admin_levels.o5m

echo "Writing admin_level.pbf file... $(pwd)/admin_levels.pbf"
./osmconvert admin_levels.o5m -o=admin_levels.pbf

cd $CWD

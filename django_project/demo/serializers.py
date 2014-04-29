from rest_framework import serializers


class MenuSerializer(serializers.Serializer):
    osm_id = serializers.CharField(max_length=15)
    name = serializers.CharField(max_length=30)
    submenu_url = serializers.HyperlinkedIdentityField(
        view_name='sub_menu', lookup_field='osm_id', format='html'
    )
    data_url = serializers.HyperlinkedIdentityField(
        view_name='data_list', lookup_field='osm_id', format='html'
    )


class SubMenuSerializer(serializers.Serializer):
    osm_id = serializers.CharField(max_length=15)
    name = serializers.CharField(max_length=30)
    data_url = serializers.HyperlinkedIdentityField(
        view_name='data_list', lookup_field='osm_id', format='html'
    )


class IndicatorSerializer(serializers.Serializer):
    osm_id = serializers.CharField(max_length=15, source='object_id')
    name = serializers.CharField(max_length=50, source='name')
    factor_a = serializers.FloatField()
    factor_b = serializers.FloatField()

from django.conf.urls import patterns, url

from .views import MenuList, SubMenuList, IndicatorList, HomePage

urlpatterns = patterns(
    '',
    # basic app views
    # url(r'^...', a_view)
    url(
        r'^menu/$', MenuList.as_view(actions={'get': 'list'}),
        name='main_menu'
    ),
    url(
        r'^menu/(?P<osm_id>[0-9]+)/$',
        SubMenuList.as_view(actions={'get': 'list'}), name='sub_menu'
    ),
    url(
        r'^data/(?P<osm_id>[0-9]+)/$',
        IndicatorList.as_view(actions={'get': 'list'}), name='data_list'
    ),
    url(
        r'^$', HomePage.as_view(), name='homepage'
    )
)

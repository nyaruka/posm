import logging
logger = logging.getLogger(__name__)

from rest_framework import viewsets
from rest_framework.response import Response

from django.views.generic import TemplateView

from .models import AdminLevel0, AdminLevel1, Indicator
from .serializers import MenuSerializer, SubMenuSerializer, IndicatorSerializer


class MenuList(viewsets.ViewSet):

    def list(self, request, *args, **kwargs):
        serializer = MenuSerializer(
            AdminLevel0.objects.order_by('name').all(),
            many=True,
            context={'request': request}
        )

        return Response(serializer.data)


class SubMenuList(viewsets.ViewSet):

    def list(self, request, *args, **kwargs):
        serializer = SubMenuSerializer(
            AdminLevel1.objects.order_by('name').filter(
                is_in_country__exact=self.kwargs.get('osm_id')).all(),
            many=True,
            context={'request': request}
        )

        return Response(serializer.data)


class IndicatorList(viewsets.ViewSet):

    def list(self, request, *args, **kwargs):
        serializer = IndicatorSerializer(
            Indicator.objects.for_osm_id(self.kwargs.get('osm_id')),
            many=True,
            context={'request': request}
        )

        return Response(serializer.data)


class HomePage(TemplateView):
    template_name = "homepage.html"

import logging
logger = logging.getLogger(__name__)

from rest_framework import viewsets
# from rest_framework.views import APIView
from rest_framework.response import Response

from .models import AdminLevel0, AdminLevel1
from .serializers import MenuSerializer, SubMenuSerializer


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

import logging

from django.views.generic import View

from yunity.models import MapItem
from yunity.utils.api import ApiBase
from yunity.utils.elasticsearch import es_search
from yunity.utils.generic import flatten, get_keys

# Get an instance of a logger
logger = logging.getLogger(__name__)


def filter_es_geo_distance(esq, lat, lon, radius_km):
    """ Add a distance filter to a search query
    :param esq: ES Search instance
    :param lat: latitude
    :param lon: longitude
    :param radius_km: radius in kilometers
    :return: ES Search instance
    """
    geo_params = {
        'distance': "%skm" % radius_km,
        'mappable.location': {
            'lat': lat,
            'lon': lon,
        }
    }
    return esq.filter('geo_distance', **geo_params)


def sort_es_geo_distance(esq, lat, lon):
    """ Add a distance sort to a search query
    :param esq: ES Search instance
    :param lat: latitude
    :param lon: longitude
    :return: ES Search instance
    """
    return esq.sort({'_geo_distance': {
        "location": {
            "lat": lat,
            "lon": lon,
        },
        "order": "desc",
        "unit": "km",
        "distance_type": "plane",
    }})


class SearchMappableView(ApiBase, View):

    def get(self, request):
        lat = float(request.GET.get('lat', 0))
        lon = float(request.GET.get('lon', 0))
        radius = float(request.GET.get('radius_km', 0))

        esq = MapItem.es_search()
        if lat and lon:
            esq = sort_es_geo_distance(esq, lat, lon)
            if radius:
                esq = filter_es_geo_distance(esq, lat, lon, radius)

        mappables_json = [m.to_dict() for m in esq.execute().hits]

        return self.json_response({
            "results": mappables_json,
            "total": esq.count(),
        })


class SearchMappableLocationsView(ApiBase, View):

    def get(self, request):
        lat = float(request.GET.get('lat', 0))
        lon = float(request.GET.get('lon', 0))
        radius = float(request.GET.get('radius_km', 0))

        esq = MapItem.es_search()
        if lat and lon and radius:
            esq = filter_es_geo_distance(esq, lat, lon, radius)

        locations_json = [
            get_keys(m.to_dict(), ['locations', 'id']) for m in esq.scan()
        ]

        return self.json_response({
            "results": locations_json,
            "total": esq.count(),
        })
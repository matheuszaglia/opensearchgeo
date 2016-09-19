from urllib import request
from xmltodict import parse
import socket

socket.setdefaulttimeout(10)


def get_bbox(bbox, search_terms, time_start, time_end, start, count):
    west, south, east, north = bbox.split(',')
    url = "http://www.dgi.inpe.br/cwic_cb4/latlong.php?" \
          "dataset={}&north={}&south={}&east={}&west={}" \
          "&startrec={}&maxrecs={}".format(search_terms, north, south, east, west, start, count)
    if time_start is not None:
        url += "&start_date=" + time_start
    if time_end is not None:
        url += "&end_date=" + time_end
    try:
        result = parse(request.urlopen(url))
    except socket.timeout:
        raise IOError
    if 'metaData' in result['searchResponse']:
        return result['searchResponse']['metaData'], int(result['searchResponse']['totalRecords'])
    return {}, int(result['searchResponse']['totalRecords'])


def get_scene(sceneid):
    url = "http://www.dgi.inpe.br/cwic_cb4/sceneid.php?" \
          "sceneid={}".format(sceneid)
    try:
        result = parse(request.urlopen(url))
    except socket.timeout:
        raise IOError
    if 'metaData' in result['searchResponse']:
        return result['searchResponse']['metaData'], int(result['searchResponse']['totalRecords'])
    return {}, int(result['searchResponse']['totalRecords'])
from collections import OrderedDict
from db_connection import database


def get_bbox(bbox, search_terms, time_start, time_end, start, count):
    minX, minY,maxX, maxY = bbox.split(',')
    sql = """
    SELECT  *, DATE_FORMAT(`Date`,'%%Y-%%m-%%dT%%H:%%i:%%s-03:00') as `Date`,
    DATE_FORMAT(`IngestDate`,'%%Y-%%m-%%dT%%H:%%i:%%s-03:00') as `IngestDate` 
    FROM Scene WHERE"""

    where = """ {}<= `TL_Latitude` and {} <=`TL_Longitude` and {} >=`TR_Latitude` and {} <= `TR_Longitude`
                and {} >=`BR_Latitude` and {} >= `BR_Longitude` and {} <= `BL_Latitude` and {} >=`BL_Longitude`"""\
                .format(minY, minX, maxY, minX, maxY, maxX, minY, maxX)
    if time_start is not None:
        where += """ and `Date` >= '{}'""".format(time_start)
    if time_end is not None:
        where+= """ and `Date`<= '{}'""".format(time_end)
    else:
        where+= """ and `Date` <= curdate()"""

    where+=""" ORDER BY `Date` DESC"""
    result = database('login', 'password', 'host', 'database').do_query(sql+where)
    sql_len = """SELECT COUNT(`SceneId`) FROM Scene WHERE {} """.format(where)
    result_len = database('login', 'password', 'host', 'database').do_query(sql_len)
    return prepare_dict(result, start, count), len(result)


def get_scene(sceneid):
    sql = """
    SELECT  *, DATE_FORMAT(`Date`,'%%Y-%%m-%%dT%%H:%%i:%%s-03:00') as `Date`,
    DATE_FORMAT(`IngestDate`,'%%Y-%%m-%%dT%%H:%%i:%%s-03:00') as `IngestDate`
    FROM Scene
    WHERE `SceneId`='{}'""".format(sceneid)

    result = database('login', 'password', 'host', 'database').do_query(sql)
    data = dict(result[0].items())
    data['browseURL'] = "opensearch/browseimage/{}".format(result[0]['SceneId'])
    return data


def prepare_dict(data, start, count):
    res = []
    for i in range(start, start+count):
        res.append(dict(data[i].items()))
        prefix = None
        url_prefix = 'http://www.dgi.inpe.br/'
        res[-1]['browseURL'] = "opensearch/browseimage/{}".format(data[i]['SceneId'])
        res[-1]['cartURL'] = url_prefix + 'CDSR/cart-cwic.php?SCENEID='+ data[i]['SceneId']
    return res


def get_collections():
    return ('INPE_CBERS4_AWFI', 'INPE_CBERS4_MUX', 'INPE_CBERS4_PAN5M', 'INPE_CBERS4_PAN10M',
            'INPE_CBERS4_IRS', 'INPE_ALL')


def get_browse_image(sceneid):
    if sceneid.startswith('L'):
        table = 'LandsatBrowse'
    elif sceneid.startswith('CB'):
        table = 'CbersBrowse'
    elif sceneid.startswith('A1') or sceneid.startswith('T1'):
        table = 'ModisBrowse'
    elif sceneid.startswith('P6'):
        table = 'P6Browse'
    sql = "SELECT `Browse` FROM {} WHERE `SceneId` = '{}'".format(table, sceneid)
    try:
        result = database('login', 'password', 'host', 'database').do_query(sql)
    except:
        raise Exception('Could not retrieve data from the database.')

    return result[0][0]


class CollectionError(Exception):
    pass

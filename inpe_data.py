from db_connection import database
import json
import logging
import os

handler = logging.FileHandler('errors.log')
handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
))

logger = logging.getLogger("opensearch")
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

def get_bbox(bbox=None, uid=None, dataset_id=None, time_start=None, time_end=None, start=0, count=10):
    sql = "SELECT *, DATE_FORMAT(`Date`,'%%Y-%%m-%%dT%%H:%%i:%%s') as `Date`, " \
          "DATE_FORMAT(`IngestDate`,'%%Y-%%m-%%dT%%H:%%i:%%s') as `IngestDate` " \
          "FROM Scene WHERE "

    where = []

    if uid is not None and uid != "":
        where.append("`SceneId` = '{}'".format(uid))

    if bbox is not None and bbox != "":
        try:
            for x in bbox.split(','):
                float(x)
            min_x, min_y, max_x, max_y = bbox.split(',')
            bbox = []

            bbox.append("({} >= `TL_Longitude` and {} <=`TL_Latitude`)".format(max_x, min_y))

            bbox.append("({} <= `TR_Longitude` and {} <=`TR_Latitude`)".format(min_x, min_y))

            bbox.append("({} >= `BL_Longitude` and {} >=`BL_Latitude`)".format(max_x, max_y))

            bbox.append("({} <= `BR_Longitude` and {} >=`BR_Latitude`)".format(min_x, max_y))

            where.append("(" + (" and ".join(bbox)) + ")")

        except:
            raise (InvalidBoundingBoxError())

    if dataset_id is not None and dataset_id != "":
        where.append("CONCAT(`Satellite`, `Sensor`) = '{}'".format(dataset_id))

    if time_start is not None and time_start != "":
        where.append("`Date` >= STR_TO_DATE('{}','%%Y-%%m-%%dT%%H:%%i:%%s')".format(time_start))

    if time_end is not None and time_end != "":
        where.append("`Date`<= STR_TO_DATE('{}','%%Y-%%m-%%dT%%H:%%i:%%s')".format(time_end))

    else:
        where.append("`Date` <= curdate()")

    where = " and ".join(where)

    sql += where

    sql += " ORDER BY `Date` DESC"

    sql += " LIMIT {},{}".format(start, count)

    result = database(os.environ.get('DB_USER'), os.environ.get('DB_PASS'), os.environ.get('DB_HOST'),
                      os.environ.get('DB_NAME')).do_query(sql)

    sql = "SELECT COUNT(`SceneId`) " \
          "FROM Scene " \
          "WHERE {} ".format(where)

    result_len = database(os.environ.get('DB_USER'), os.environ.get('DB_PASS'), os.environ.get('DB_HOST'),
                      os.environ.get('DB_NAME')).do_query(sql)
    if result_len[0][0] < count:
        count = result_len[0][0]

    return prepare_dict(result), result_len[0][0]


def get_updated():
    sql = "SELECT DATE_FORMAT(`update_time`,'%%Y-%%m-%%dT%%H:%%i:%%s') as `Date` " \
          "FROM information_schema.tables WHERE table_name = 'Scene';"

    result = database(os.environ.get('DB_USER'), os.environ.get('DB_PASS'), os.environ.get('DB_HOST'),
                      os.environ.get('DB_NAME')).do_query(sql)

    return result[0][0]


def prepare_dict(data):
    res = []
    for i in data:
        res.append(dict(i.items()))
        res[-1]['icon'] = "opensearch/browseimage/{}".format(i['SceneId'])
        res[-1]['enclosure'] = get_enclosure(res[-1])
    return res


def get_datasets(bbox, query, uid, time_start, time_end, start = 0, count = 10):
    where = []

    if uid is not None and uid != "":
        where.append("CONCAT(`Satellite`, `Sensor`) = '{}'".format(uid))
    elif query is not None and query != "":
        where.append("CONCAT(`Satellite`, `Sensor`) LIKE '%%{}%%'".format(query))

    if bbox is not None and bbox != "":
        try:
            for x in bbox.split(','):
                float(x)
            min_x, min_y, max_x, max_y = bbox.split(',')
            bbox = []

            bbox.append("({} >= `TL_Longitude` and {} <=`TL_Latitude`)".format(max_x, min_y))

            bbox.append("({} <= `TR_Longitude` and {} <=`TR_Latitude`)".format(min_x, min_y))

            bbox.append("({} >= `BL_Longitude` and {} >=`BL_Latitude`)".format(max_x, max_y))

            bbox.append("({} <= `BR_Longitude` and {} >=`BR_Latitude`)".format(min_x, max_y))

            where.append("(" + (" and ".join(bbox)) + ")")

        except:
            raise (InvalidBoundingBoxError())

    if time_start is not None and time_start != "":
        where.append("`Date` >= STR_TO_DATE('{}','%%Y-%%m-%%dT%%H:%%i:%%s')".format(time_start))

    if time_end is not None and time_end != "":
        where.append("`Date`<= STR_TO_DATE('{}','%%Y-%%m-%%dT%%H:%%i:%%s')".format(time_end))

    else:
        where.append("`Date` <= curdate()")

    where = " and ".join(where)

    sql = "SELECT `Satellite`, `Sensor`, " \
          "MAX(DATE_FORMAT(`Date`,'%%Y-%%m-%%dT%%H:%%i:%%s')) as `Date` " \
          "FROM `Scene` WHERE {} " \
          "GROUP BY `Satellite`, `Sensor` " \
          "ORDER BY `Date` DESC".format(where)
    sql += " LIMIT {},{}".format(start, count)

    result = database(os.environ.get('DB_USER'), os.environ.get('DB_PASS'), os.environ.get('DB_HOST'),
                      os.environ.get('DB_NAME')).do_query(sql)

    return result


def get_enclosure(scene):
    from httplib2 import Http
    from datetime import datetime

    url = 'http://www.dpi.inpe.br/newcatalog/tmp/{}/{}_{:02d}/{}/{}_{}_0/{}_BC_UTM_WGS84'
    satellite = ""
    table = ""
    drd = ""
    path = scene['Path']
    row = scene['Row']

    if scene['Satellite'] == 'CB4':
        satellite = 'CBERS4'
        table = 'Cbers'
    elif scene['Satellite'] == 'CB2':
        satellite = 'CBERS2'
        table = 'Cbers'
    elif scene['Satellite'] == 'CB2B':
        satellite = 'CBERS2B'
        table = 'Cbers'
    elif scene['Satellite'] == 'L7':
        satellite = 'LANDSAT7'
        table = 'Landsat'
    elif scene['Satellite'] == 'L5':
        satellite = 'LANDSAT5'
        table = 'Landsat'
    else:
        return None

    dt = datetime.strptime(scene['Date'], '%Y-%m-%dT%H:%M:%S')

    sql = "SELECT `DRD` " \
          "FROM `{}Scene`" \
          " WHERE `SceneId` = '{}' ".format(table, scene['SceneId'])

    drd = database(os.environ.get('DB_USER'), os.environ.get('DB_PASS'), os.environ.get('DB_HOST'),
                      os.environ.get('DB_NAME')).do_query(sql)[0][0]
    url_2 = url.format(satellite, dt.year, dt.month, drd, path, row, '2')
    url_4 = url.format(satellite, dt.year, dt.month, drd, path, row, '4')
    h = Http()
    resp = h.request(url_2, 'HEAD')

    if resp[0]['status'] == '200':
        return url_2
    else:
        resp = h.request(url_4, 'HEAD')
        if resp[0]['status'] == '200':
            return url_4

    return 'http://www.dgi.inpe.br/catalogo/cart-cwic.php?SCENEID=' + scene['SceneId']


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
        result = database(os.environ.get('DB_USER'), os.environ.get('DB_PASS'), os.environ.get('DB_HOST'),
                      os.environ.get('DB_NAME')).do_query(sql)
    except:
        raise Exception('Could not retrieve data from the database.')

    return result[0][0]


class CollectionError(Exception):
    pass


class InvalidBoundingBoxError(Exception):
    pass

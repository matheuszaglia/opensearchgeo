import sqlalchemy
import logging
import os

handler = logging.FileHandler('errors.log')
handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
))


logger = logging.getLogger('opensearch')
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def get_bbox(bbox=None, uid=None, time_start=None, time_end=None,
             radiometric=None, image_type=None, band=None, dataset=None, start=0, count=10):
    sql = "SELECT s.*, DATE_FORMAT(s.`Date`,'%%Y-%%m-%%dT%%H:%%i:%%s') as `Date`, " \
          "DATE_FORMAT(s.`IngestDate`,'%%Y-%%m-%%dT%%H:%%i:%%s') as `IngestDate` " \
          "FROM Scene AS s, Product AS p WHERE "

    where = list()

    where.append('s.`SceneId` = p.`SceneId`')

    if uid is not None and uid != "":
        where.append("s.`SceneId` = '{}'".format(uid))

    if bbox is not None and bbox != "":
        try:
            for x in bbox.split(','):
                float(x)
            min_x, min_y, max_x, max_y = bbox.split(',')

            bbox = list()

            bbox.append("({} >= `TL_Longitude` and {} <=`TL_Latitude`)".format(max_x, min_y))

            bbox.append("({} <= `TR_Longitude` and {} <=`TR_Latitude`)".format(min_x, min_y))

            bbox.append("({} >= `BL_Longitude` and {} >=`BL_Latitude`)".format(max_x, max_y))

            bbox.append("({} <= `BR_Longitude` and {} >=`BR_Latitude`)".format(min_x, max_y))

            where.append("(" + (" and ".join(bbox)) + ")")

        except:
            raise (InvalidBoundingBoxError())

    if time_start is not None and time_start != "":

        where.append("s.`Date` >= STR_TO_DATE('{}','%%Y-%%m-%%dT%%H:%%i:%%s')".format(time_start))

    if time_end is not None and time_end != "":
        where.append("s.`Date`<= STR_TO_DATE('{}','%%Y-%%m-%%dT%%H:%%i:%%s')".format(time_end))

    else:
        where.append("s.`Date` <= curdate()")

    if radiometric is not None and radiometric != "":
        where.append("p.`RadiometricProcessing` LIKE '%%{}%%'".format(radiometric))
    if image_type is not None and image_type != "":
        where.append("p.`Type` LIKE '%%{}%%'".format(image_type))
    if band is not None and band != "":
        where.append("p.`Band` LIKE '%%{}%%'".format(band))
    if dataset is not None and dataset != "":
        where.append("p.`Dataset` LIKE '{}'".format(dataset))

    where = " and ".join(where)

    sql += where

    sql += " GROUP BY s.`SceneId` ORDER BY `Date` DESC"

    sql += " LIMIT {},{}".format(start, count)

    result = do_query(sql)

    sql = "SELECT COUNT(*) as len FROM (" \
          "SELECT s.`SceneId`" \
          "FROM Scene AS s, Product AS p " \
          "WHERE {} GROUP BY s.`SceneId`) as s".format(where)

    result_len = do_query(sql)
    result_len = int(result_len[0]['len'])
    if result_len > 0:
        if result_len < count:
            count = result_len
    else:
        count = 0

    return make_geojson(result), count


def get_updated():
    sql = "SELECT DATE_FORMAT(`update_time`,'%%Y-%%m-%%dT%%H:%%i:%%s') as `Date` " \
          "FROM information_schema.tables WHERE table_name = 'Scene'"

    result = do_query(sql)
    return result[0]['Date']


def get_products(scene_id):
    sql = "SELECT * FROM `Product` WHERE `SceneId` = '{}'".format(scene_id)
    result = do_query(sql)
    return result


def get_datasets():
    sql = "SELECT DISTINCT `Dataset` FROM `Product`"
    result = do_query(sql)
    return result


def make_geojson(data, output='json'):
    geojson = dict()
    geojson['type'] = 'FeatureCollection'
    geojson['features'] = []
    base_url = os.environ.get('BASE_URL')
    for i in data:
        feature = dict()
        feature['type'] = 'Feature'

        geometry = dict()
        geometry['type'] = 'Polygon'
        geometry['coordinates'] = [
          [[i['TL_Longitude'], i['TL_Latitude']],
           [i['BL_Longitude'], i['BL_Latitude']],
           [i['BR_Longitude'], i['BR_Latitude']],
           [i['TR_Longitude'], i['TR_Latitude']],
           [i['TL_Longitude'], i['TL_Latitude']]]
        ]

        feature['geometry'] = geometry
        properties = dict()
        properties['title'] = i['SceneId']
        properties['id'] = '{}/granule.{}?uid={}'.format(base_url, output, i['SceneId'])
        properties['updated'] = i['IngestDate']
        properties['alternate'] = '{}/granule.{}?uid={}'.format(base_url, output, i['SceneId'])
        properties['icon'] = '{}/browseimage/{}'.format(base_url, i['SceneId'])
        properties['via'] = '{}/metadata/{}'.format(base_url, i['SceneId'])

        for key, value in i.items():
            if key != 'SceneId' and key != 'IngestDate':
                properties[key] = value

        products = get_products(i['SceneId'])

        properties['enclosure'] = []
        for p in products:
            enclosure = dict()

            enclosure['band'] = p['Band']
            enclosure['radiometric_processing'] = p['RadiometricProcessing']
            enclosure['type'] = p['Type']
            enclosure['url'] = os.environ.get('ENCLOSURE_BASE') + p['Filename']
            properties['enclosure'].append(enclosure)

        feature['properties'] = properties
        geojson['features'].append(feature)

    return geojson


def get_browse_image(sceneid):
    table = ''

    if sceneid.startswith('L'):
        table = 'LandsatBrowse'
    elif sceneid.startswith('CB'):
        table = 'CbersBrowse'
    elif sceneid.startswith('A1') or sceneid.startswith('T1'):
        table = 'ModisBrowse'
    elif sceneid.startswith('P6'):
        table = 'P6Browse'
    sql = "SELECT `Browse` FROM {} WHERE `SceneId` = '{}'".format(table, sceneid)

    result = do_query(sql)

    return result[0]['Browse']


def do_query(sql):
    connection = 'mysql://{}:{}@{}/{}'.format(os.environ.get('DB_USER'),

                                              os.environ.get('DB_PASS'),
                                              os.environ.get('DB_HOST'),
                                              os.environ.get('DB_NAME'))
    engine = sqlalchemy.create_engine(connection)
    result = engine.execute(sql)
    result = result.fetchall()
    engine.dispose()
    return [dict(row) for row in result]


class InvalidBoundingBoxError(Exception):
    pass

from db_connection import database


def get_bbox(bbox, uid, dataset_id, time_start, time_end, start, count):

    sql = "SELECT *, DATE_FORMAT(`Date`,'%%Y-%%m-%%dT%%H:%%i:%%s') as `Date`, " \
          "DATE_FORMAT(`IngestDate`,'%%Y-%%m-%%dT%%H:%%i:%%s') as `IngestDate` " \
          "FROM Scene WHERE "

    where = []

    if uid is not None:
        where.append("`SceneId` = '{}'".format(uid))

    if bbox is not None:
        try:
            min_x, min_y, max_x, max_y = bbox.split(',')
            for x in bbox.split(','):
                float(x)

            where.append("{}<= `TL_Latitude` and {} <=`TL_Longitude` and {} >=`TR_Latitude` and" \
                   " {} <= `TR_Longitude` and {} >=`BR_Latitude` and {} >= `BR_Longitude` and" \
                   " {} <= `BL_Latitude` and {} >=`BL_Longitude`".format(min_y, min_x, max_y, min_x,
                                                                         max_y, max_x, min_y, max_x))
        except:
            raise (InvalidBoundingBoxError())

    if dataset_id is not None:
        where.append("CONCAT(`Satellite`, `Sensor`) = '{}'".format(dataset_id))

    if time_start is not None:
        where.append("`Date` >= '{}'".format(time_start))

    if time_end is not None:
        where.append("`Date`<= '{}'".format(time_end))

    else:
        where.append("`Date` <= curdate()")

    where = " and ".join(where)

    sql += where

    sql += " ORDER BY `Date` DESC"

    sql += " LIMIT {},{}".format(start, count)

    result = database('login', 'password', 'host', 'database').do_query(sql)

    sql = "SELECT COUNT(`SceneId`) " \
          "FROM Scene " \
          "WHERE {} ".format(where)

    result_len = database('login', 'password', 'host', 'database').do_query(sql)
    if result_len[0][0] < count:
        count = result_len[0][0]

    return prepare_dict(result, start, count), result_len[0][0]

def get_updated():
    sql = "SELECT DATE_FORMAT(`update_time`,'%%Y-%%m-%%dT%%H:%%i:%%s') as `Date` " \
          "FROM information_schema.tables WHERE table_name = 'Scene';"

    result = database('login', 'password', 'host', 'database').do_query(sql)

    return result[0][0]


def prepare_dict(data, start, count):
    res = []
    for i in range(start, start + count):
        res.append(dict(data[i].items()))
        prefix = None
        url_prefix = 'http://www.dgi.inpe.br/'
        res[-1]['browseURL'] = "opensearch/browseimage/{}".format(data[i]['SceneId'])
        res[-1]['cartURL'] = url_prefix + 'CDSR/cart-cwic.php?SCENEID=' + data[i]['SceneId']
    return res


def get_datasets(bbox, query, uid, time_start, time_end, start_index, count):
    where = []

    if uid is not None:
        where.append("CONCAT(`Satellite`, `Sensor`) = '{}'".format(uid))
    elif query is not None:
        where.append("CONCAT(`Satellite`, `Sensor`) LIKE '%%{}%%'".format(query))

    if bbox is not None:
        try:
            min_x, min_y, max_x, max_y = bbox.split(',')
            for x in bbox.split(','):
                float(x)

            where.append("{}<= `TL_Latitude` and {} <=`TL_Longitude` and {} >=`TR_Latitude` and" \
                   " {} <= `TR_Longitude` and {} >=`BR_Latitude` and {} >= `BR_Longitude` and" \
                   " {} <= `BL_Latitude` and {} >=`BL_Longitude`".format(min_y, min_x, max_y, min_x,
                                                                         max_y, max_x, min_y, max_x))
        except:
            raise (InvalidBoundingBoxError())

    if time_start is not None:
        where.append("`Date` >= '{}'".format(time_start))

    if time_end is not None:
        where.append("`Date`<= '{}'".format(time_end))

    else:
        where.append("`Date` <= curdate()")

    where = " and ".join(where)

    sql = "SELECT `Satellite`, `Sensor`, " \
          "MAX(DATE_FORMAT(`Date`,'%%Y-%%m-%%dT%%H:%%i:%%s')) as `Date` " \
          "FROM `Scene` WHERE {} " \
          "GROUP BY `Satellite`, `Sensor` " \
          "ORDER BY `Date`".format(where)

    result = database('login', 'password', 'host', 'database').do_query(sql)

    return result


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


class InvalidBoundingBoxError(Exception):
    pass

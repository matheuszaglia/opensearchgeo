from flask import Flask, request, make_response, render_template, abort, jsonify, send_file
import inpe_data

import io
import logging
import traceback

app = Flask(__name__)
app.config['PROPAGATE_EXCEPTIONS'] = True
app.logger_name = "opensearch"
handler = logging.FileHandler('errors.log')
handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
))

app.logger.addHandler(handler)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True
app.jinja_env.keep_trailing_newline = True


@app.route('/granule.<string:format>', methods=['GET'])
def os_granule(format):
    data = []
    total_results = 0
    start_index = request.args.get('startIndex', 0)
    count = request.args.get('count', 10)

    if start_index == "" or int(start_index) < 1:
        start_index = 0
    else:
        start_index = int(start_index) - 1

    if count == "":
        count = 10
    else:
        count = int(count)

    try:

        data, total_results = inpe_data.get_bbox(request.args.get('bbox', None),
                                                 request.args.get('uid', None),
                                                 request.args.get('collectionId'),
                                                 request.args.get('start', None),
                                                 request.args.get('end', None),
                                                 start_index, count)
    except inpe_data.InvalidBoundingBoxError:
        abort(400, 'Invalid bounding box')
    except IOError:
        abort(503)
    except inpe_data.CollectionError as e:
        abort(400, str(e))

    resp = make_response(render_template('granule.' + format,
                                         url=request.url.replace('&', '&amp;'),
                                         bbox=request.args.get('bbox', None),
                                         data=data, total_results=total_results,
                                         start_index=start_index, count=count,
                                         url_root=request.url_root))

    if format == 'atom':
        format = 'atom+xml'
    resp.content_type = 'application/' + format

    return resp


@app.route('/collections.<string:format>')
def os_dataset(format):
    total_results = 0
    data = None
    start_index = request.args.get('startIndex', 0)
    count = request.args.get('count', 10)

    if start_index == "" or int(start_index) < 1:
        start_index = 0
    else:
        start_index = int(start_index) - 1
    if count == "":
        count = 10
    else:
        count = int(count)

    try:
        result = inpe_data.get_datasets(request.args.get('bbox', None),
                                        request.args.get('searchTerms', None),
                                        request.args.get('uid', None),
                                        request.args.get('start', None),
                                        request.args.get('end', None),
                                        start_index, count)

        data = result
    except IOError:
        abort(503)

    resp = make_response(render_template('collections.' + format,
                                         url=request.url.replace('&', '&amp;'),
                                         data=data, total_results=len(result),
                                         start_index=start_index, count=count,
                                         url_root=request.url_root,
                                         updated=inpe_data.get_updated()
                                         ))
    if format == 'atom':
        format = 'atom+xml'
    resp.content_type = 'application/' + format
    return resp


@app.route('/osdd/granule', defaults={'collection': None})
@app.route('/osdd/granule/<string:collection>')
def os_osdd_granule(collection):
    resp = make_response(render_template('osdd_granule.xml',
                                         url=request.url_root,
                                         collection=collection))
    resp.content_type = 'application/xml'
    return resp


@app.route('/')
@app.route('/osdd')
@app.route('/osdd/collection')
def os_osdd_collection():
    resp = make_response(render_template('osdd_collection.xml', url=request.url_root))
    resp.content_type = 'application/xml'
    return resp


@app.route('/browseimage/<string:sceneid>')
def browse_image(sceneid):
    try:
        image = inpe_data.get_browse_image(sceneid)
    except IndexError:
        abort(400, 'There is no browse image with the provided Scene ID.')
    except Exception as e:
        abort(503, str(e))

    return send_file(io.BytesIO(image), mimetype='image/jpeg')


@app.route('/metadata/<string:sceneid>')
def scene(sceneid):
    try:
        data, result_len = inpe_data.get_bbox(uid=sceneid)
        data[0]['browseURL'] = request.url_root + data[0]['browseURL']
    except Exception as e:
        abort(503, str(e))

    return jsonify(data)


@app.route('/path_row')
def get_path_row():
    data = inpe_data.get_path_row()
    resp = make_response(render_template('path_row.json',
                                         total_results=len(data),
                                         data=data
                                         ))

    resp.content_type = 'application/json'
    return resp


@app.errorhandler(500)
def handle_api_error(e):
    response = jsonify({'code': 500, 'message': 'Internal Server Error'})
    response.status_code = 500
    return response

@app.errorhandler(502)
def handle_bad_gateway_error(e):
    response = jsonify({'code': 502, 'message': 'Bad Gateway'})
    response.status_code = 502
    return response

@app.errorhandler(503)
def handle_service_unavailable_error(e):
    response = jsonify({'code': 503, 'message': 'Service Unavailable'})
    response.status_code = 503
    return response


@app.errorhandler(400)
def handle_bad_request(e):
    response = jsonify({'code': 400, 'message': 'Bad Request - {}'.format(e.description)})
    response.status_code = 400
    return response


@app.errorhandler(404)
def handle_page_not_found(e):
    response = jsonify({'code': 404, 'message': 'Page not found'})
    response.status_code = 404
    return response


@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(traceback.format_exc(-1))
    response = jsonify({'code': 500, 'message': 'Internal Server Error'})
    response.status_code = 500
    return response

from flask import Flask, request, make_response, render_template, abort, jsonify, send_file
import inpe_data
import os
import io
import logging


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


@app.route('/granule.<string:output>', methods=['GET'])
def os_granule(output):
    data = []
    total_results = 0

    start_index = request.args.get('startIndex', 1)
    count = request.args.get('count', 10)

    if start_index == "":
        start_index = 0
    elif int(start_index) == 0:
        abort(400, 'Invalid startIndex')
    else:
        start_index = int(start_index) - 1
    if count == "":
        count = 10
    elif int(count) < 0:
        abort(400, 'Invalid count')
    else:
        count = int(count)

    try:
        data, total_results = inpe_data.get_bbox(request.args.get('bbox', None),
                                                 request.args.get('uid', None),
                                                 request.args.get('start', None),
                                                 request.args.get('end', None),
                                                 request.args.get('radiometricProcessing', None),
                                                 request.args.get('type', None),
                                                 request.args.get('band', None),
                                                 request.args.get('dataset', None),
                                                 start_index, count)
    except inpe_data.InvalidBoundingBoxError:
        abort(400, 'Invalid bounding box')
    except IOError:
        abort(503)


    if output == 'json':
        return jsonify(data)

    resp = make_response(render_template('granule.{}'.format(output),
                                         url=request.url.replace('&', '&amp;'),
                                         data=data, total_results=total_results,
                                         start_index=start_index, count=count,
                                         url_root=os.environ.get('BASE_URL')))

    if output == 'atom':
        resp.content_type = 'application/atom+xml' + output

    return resp


@app.route('/collections.<string:output>')
def os_dataset(output):
    abort(503) # disabled at the moment

    total_results = 0
    data = None
    start_index = request.args.get('startIndex', 1)
    count = request.args.get('count', 10)

    if start_index == "":
        start_index = 0
    elif int(start_index) == 0:
        abort(400, 'Invalid startIndex')

    else:
        start_index = int(start_index) - 1

    if count == "":
        count = 10
    elif int(count) < 0:
        abort(400, 'Invalid count')
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

    resp = make_response(render_template('collections.' + output,
                                         url=request.url.replace('&', '&amp;'),
                                         data=data, total_results=len(result),
                                         start_index=start_index, count=count,
                                         url_root=request.url_root,
                                         updated=inpe_data.get_updated()
                                         ))
    if output == 'atom':
        output = 'atom+xml'
    resp.content_type = 'application/' + output
    return resp


@app.route('/')
@app.route('/osdd')
@app.route('/osdd/granule')
def os_osdd_granule():
    resp = make_response(render_template('osdd_granule.xml',
                                         url=os.environ.get('BASE_URL'),
                                         datasets=inpe_data.get_datasets()))
    resp.content_type = 'application/xml'
    return resp


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


@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.exception(e)
    response = jsonify({'code': 500, 'message': 'Internal Server Error'})
    response.status_code = 500
    return response

from flask import Flask, request, make_response, render_template, abort, jsonify, send_file
import inpe_data
import io

app = Flask(__name__)


@app.route('/<string:format>/granule', methods=['GET'])
def os_granule(format):
    if 'bbox' not in request.url:
        abort(400, 'Parameter \'bbox\' is missing')

    data = []
    total_results = 0
    start_index = int(request.args.get('startIndex', 0))
    count = int(request.args.get('count', 10))

    try:
        bbox = request.args.get('bbox')
        for coord in bbox.split(','):
            float(coord)
        data, total_results = inpe_data.get_bbox(bbox,
                                                 request.args.get('q', None),
                                                 request.args.get('start', None),
                                                 request.args.get('end', None),
                                                 start_index, count)
    except ValueError:
        abort(400, 'Invalid bounding box')
    except IOError:
        abort(503)
    except inpe_data.CollectionError as e:
        abort(400, str(e))

    resp = make_response(render_template('opensearch.' + format,
                                         url=request.url.replace('&', '&amp;'),
                                         data=data, total_results=total_results,
                                         start_index=start_index, count=count,
                                         url_root=request.url_root))

    if format == 'atom':
        format = 'atom+xml'
    resp.content_type = 'application/' + format

    return resp


@app.route('/<string:format>/scene', methods=['GET'])
def os_scene(format):
    if 'sceneid' not in request.url:
        abort(400, 'Parameter \'sceneid\' is missing')
    total_results = 0
    data = []
    try:
        result = inpe_data.get_scene(request.args.get('sceneid'))
        data.append(result)
    except IOError:
        abort(503)

    resp = make_response(render_template('opensearch.' + format,
                                         url=request.url.replace('&', '&amp;'),
                                         data=data, total_results=1,
                                         start_index=0, count=1,
                                         url_root=request.url_root))

    if format == 'atom':
        format = 'atom+xml'
    resp.content_type = 'application/' + format

    return resp


@app.route('/')
@app.route('/osdd')
def os_osdd():
    resp = make_response(render_template('osdd_granule.xml', url=request.url_root))
    resp.content_type = 'application/xml'
    return resp


@app.route('/opensearch/browseimage/<string:sceneid>')
@app.route('/browseimage/<string:sceneid>')
def browse_image(sceneid):
    try:
        image = inpe_data.get_browse_image(sceneid)
    except IndexError:
        abort(400, 'There is no browse image with the provided Scene ID.')
    except Exception as e:
        abort(503, str(e))

    return send_file(io.BytesIO(image), mimetype='image/jpeg')


@app.route('/opensearch/metadata/<string:sceneid>')
@app.route('/metadata/<string:sceneid>')
def scene(sceneid):
    try:
        data = inpe_data.get_scene(sceneid)
        data['browseURL'] = request.url_root + data['browseURL']
    except Exception as e:
        abort(503, str(e))

    return jsonify(data)

@app.errorhandler(500)
def handle_api_error(e):
    response = jsonify({'code': 500, 'message': 'Internal Server Error'})
    response.status_code = 500
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


if __name__ == '__main__':
    app.run(debug=True)

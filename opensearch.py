from flask import Flask, request, make_response, render_template, abort, jsonify, send_file
import inpe_data
import io

app = Flask(__name__)
app.config["APPLICATION_ROOT"] = "/opensearch"

@app.route('/granule.<string:format>', methods=['GET'])
def os_granule(format):

    data = []
    total_results = 0
    start_index = int(request.args.get('startIndex', 0))
    count = int(request.args.get('count', 10))

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
    start_index = int(request.args.get('startIndex', 0))
    count = int(request.args.get('count', 10))

    try:
        result = inpe_data.get_datasets(request.args.get('bbox', None),
                                        request.args.get('keyword', None),
                                        request.args.get('uid', None),
                                        request.args.get('start', None),
                                        request.args.get('end', None),
                                        start_index, count)
        total_results = len(result)
        data = result
    except IOError:
        abort(503)

    resp = make_response(render_template('collections.' + format,
                                         url=request.url.replace('&', '&amp;'),
                                         data=data, total_results=total_results,
                                         start_index=0, count=count,
                                         url_root=request.url_root
                                         ))
    if format == 'atom':
        format = 'atom+xml'
    resp.content_type = 'application/' + format
    return resp


@app.route('/osdd/granule', defaults={'collection' : None})
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
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    app.jinja_env.keep_trailing_newline = True
    app.run(debug=True)

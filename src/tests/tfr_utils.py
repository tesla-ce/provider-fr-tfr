import os


def get_image(img='valid_image'):
    with open(os.path.abspath(os.path.join(os.path.dirname(__file__), './data/{}.b64'.format(img))), 'r') as fd_image:
        return fd_image.read()


def get_sample(sample_mimetype='__default__', data_mimetype='__default__', image_data=None, image='valid_image',
               sample_id=1, learner_id='9cfd197a-3b42-4361-841a-a45ef435b0e6', validations=[]):
    from tesla_ce_provider.models.base import Sample
    if image_data is None:
        img = get_image(image)
        assert img is not None and len(img)>0
        image_data_parts = img.split(',')
        image_data = image_data_parts[1]
        if data_mimetype == '__default__':
            try:
                data_mimetype = image_data_parts[0].split(':')[1].split(';')[0]
            except Exception:
                # if the data mimetype is not found, assign None
                data_mimetype = None
    if data_mimetype == '__default__':
        data_mimetype = None
    if sample_mimetype == '__default__':
        if data_mimetype is None:
            sample_mimetype = 'image/jpeg'
        else:
            sample_mimetype = data_mimetype

    sample_data = {
        "learner_id": learner_id,
        "data": "data:{};base64,{}".format(data_mimetype, image_data),
        "instruments":[1],
        "metadata": {
            "context": {},
            "mimetype": sample_mimetype
        }
    }

    if data_mimetype is None:
        sample_data['data'] = "data:;base64,{}".format(image_data)

    if sample_mimetype is None:
        del sample_data['metadata']['mimetype']

    return Sample({
        'id': sample_id,
        'learner_id': learner_id,
        'data': sample_data,
        'validations': validations
    })


def get_request(request_mimetype='__default__', data_mimetype='__default__', image_data=None, image='valid_image',
                learner_id='9cfd197a-3b42-4361-841a-a45ef435b0e6', course_id=1, activity_id=1, session_id=1):
    from tesla_ce_provider.models.base import Request
    if image_data is None:
        img = get_image(image)
        assert img is not None and len(img) > 0
        image_data_parts = img.split(',')
        image_data = image_data_parts[1]
        if data_mimetype == '__default__':
            try:
                data_mimetype = image_data_parts[0].split(':')[1].split(';')[0]
            except Exception:
                # if the data mimetype is not found, assign None
                data_mimetype = None
    if data_mimetype == '__default__':
        data_mimetype = None
    if request_mimetype == '__default__':
        if data_mimetype is None:
            request_mimetype = 'image/jpeg'
        else:
            request_mimetype = data_mimetype

    if data_mimetype is None:
        request_data = "data:base64,{}".format(image_data)
    else:
        request_data = "data:{};base64,{}".format(data_mimetype, image_data)

    request_obj = {
        "learner_id": learner_id,
        "course_id": course_id,
        "activity_id": activity_id,
        "session_id": session_id,
        "data": request_data,
        "instruments": [1],
        "metadata": {
            "file": None,
            "context": {},
            "mimetype": request_mimetype
        }
    }

    if request_mimetype is None:
        del request_obj['metadata']['mimetype']

    return Request(request_obj)


def check_validation_result(result):
    import tesla_ce_provider
    assert isinstance(result, tesla_ce_provider.result.ValidationResult)


def check_enrolment_result(result):
    import tesla_ce_provider
    assert isinstance(result, tesla_ce_provider.result.EnrolmentResult)


def check_verification_result(result):
    import tesla_ce_provider
    assert isinstance(result, tesla_ce_provider.result.VerificationResult)


class Request:

    def __init__(self, object):
        self._object = object




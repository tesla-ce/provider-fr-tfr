#  Copyright (c) 2020 Xavier Baró
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU Affero General Public License as
#      published by the Free Software Foundation, either version 3 of the
#      License, or (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU Affero General Public License for more details.
#
#      You should have received a copy of the GNU Affero General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.
""" TeSLA CE TFR validation tests module """
import base64
from .tfr_utils import get_sample, check_validation_result


def test_missing_mimetype(tfr_provider):

    sample = get_sample(sample_mimetype=None, data_mimetype=None)
    result_id = 1
    result = tfr_provider.validate_sample(sample, result_id=result_id)

    check_validation_result(result)

    assert result.contribution is None
    assert result.message_code_id == 'PROVIDER_MISSING_MIMETYPE'
    assert result.error_message == 'Missing mimetype.'
    assert result.status == 2


def test_different_mimetypes(tfr_provider):

    sample = get_sample(sample_mimetype='image/png')
    result_id = 1
    result = tfr_provider.validate_sample(sample, result_id=result_id)

    check_validation_result(result)

    assert result.contribution is None
    assert result.message_code_id == 'PROVIDER_INVALID_MIMETYPE'
    assert result.error_message == 'Mimetype in sample data differs from sample mimetype'
    assert result.status == 2


def test_unsuported_mimetypes(tfr_provider):

    sample = get_sample(sample_mimetype='image/other', data_mimetype='image/other')
    result_id = 1
    result = tfr_provider.validate_sample(sample, result_id=result_id)

    check_validation_result(result)

    assert result.contribution is None
    assert result.message_code_id == 'PROVIDER_INVALID_MIMETYPE'
    assert result.error_message == "Invalid mimetype. Accepted types are: [{}]".format(
                ', '.join(tfr_provider.accepted_mimetypes))
    assert result.status == 2


def test_mimetype_both(tfr_provider):

    sample = get_sample()
    result_id = 1
    result = tfr_provider.validate_sample(sample, result_id=result_id)

    check_validation_result(result)

    assert result.contribution > 0
    assert result.message_code_id is None
    assert result.error_message is None
    assert result.status == 1
    assert 'face_location' in result.info


def test_mimetype_sample(tfr_provider):

    sample = get_sample(sample_mimetype=None)
    result_id = 1
    result = tfr_provider.validate_sample(sample, result_id=result_id)

    check_validation_result(result)

    assert result.contribution > 0
    assert result.message_code_id is None
    assert result.error_message is None
    assert result.status == 1
    assert 'face_location' in result.info


def test_invalid_sample_datab64(tfr_provider):

    sample = get_sample(image_data='this is not a b64')
    result_id = 1
    result = tfr_provider.validate_sample(sample, result_id=result_id)

    check_validation_result(result)

    assert result.contribution is None
    assert result.message_code_id == 'PROVIDER_INVALID_SAMPLE_DATA'
    assert result.error_message == 'Invalid image format in sample data.'
    assert result.status == 2


def test_invalid_sample_data(tfr_provider):

    sample = get_sample(image_data=base64.b64encode(b'this is not a b64').decode())
    result_id = 1
    result = tfr_provider.validate_sample(sample, result_id=result_id)

    check_validation_result(result)

    assert result.contribution is None
    assert result.message_code_id == 'PROVIDER_INVALID_SAMPLE_DATA'
    assert result.error_message == 'Invalid image format in sample data.'
    assert result.status == 2


def test_black_image(tfr_provider):

    sample = get_sample(image='black_image')
    result_id = 1
    result = tfr_provider.validate_sample(sample, result_id=result_id)

    check_validation_result(result)

    assert result.contribution is None
    assert result.message_code_id == 'PROVIDER_BLACK_IMAGE'
    assert result.error_message == 'Black image.'
    assert result.status == 2


def test_multiple_faces_image(tfr_provider):

    sample = get_sample(image='multiple_faces')
    result_id = 1
    result = tfr_provider.validate_sample(sample, result_id=result_id)

    check_validation_result(result)

    assert result.contribution is None
    assert result.message_code_id == 'PROVIDER_MULTIPLE_PEOPLE'
    assert result.error_message == 'Multiple faces in the image.'
    assert result.status == 2

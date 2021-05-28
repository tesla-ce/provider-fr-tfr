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
from .tfr_utils import get_sample


def test_get_sample_image(tfr_provider):
    from tfr.provider.utils import get_sample_image
    from tesla_ce_provider.models.base import Sample

    sample = get_sample(sample_id=1, image_data=None)
    sample_json = sample._object
    valid_image = sample_json['data']['data']

    # Image data is None
    sample_json['data']['data'] = None
    sample = Sample(sample_json)
    image = get_sample_image(sample)
    assert image is None

    # Image data is base64, but not an image
    sample_json['data']['data'] = base64.b64encode('some information'.encode()).decode()
    sample = Sample(sample_json)
    image = get_sample_image(sample)
    assert image is None

    # Image data is the base64
    sample_json['data']['data'] = valid_image.split(',')[1]
    sample = Sample(sample_json)
    image = get_sample_image(sample)
    assert image is not None


def test_get_sample_video(tfr_provider):
    from tfr.provider.utils import get_sample_image
    from tesla_ce_provider.models.base import Sample




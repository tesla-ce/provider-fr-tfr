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
""" TeSLA CE Face Recognition utility module """
import base64
from base64 import binascii
from io import BytesIO
import numpy as np
from PIL import Image, UnidentifiedImageError
from tesla_ce_provider import message


def get_sample_image(sample):
    """
        Get image from sample

        :param sample: Sample structure
        :type sample: tesla_ce_provider.models.base.Sample | tesla_provider.models.base.Request
        :return: Image
        :rtype: np.Array
    """
    try:
        data = sample.data.split(',')[1]
    except AttributeError:
        return None
    except IndexError:
        data = sample.data
    try:
        buffer = BytesIO()
        buffer.write(base64.b64decode(data))
        buffer.flush()
    except binascii.Error:
        return None
    try:
        image = Image.open(buffer)
    except UnidentifiedImageError:
        return None

    im_array = np.array(image)

    # Convert from RGBA to RGB
    if np.shape(im_array)[2] == 4:
        chanel_r, chanel_g, chanel_b, chanel_a = np.rollaxis(im_array, axis=-1)
        chanel_r[chanel_a == 0] = 0
        chanel_g[chanel_a == 0] = 0
        chanel_b[chanel_a == 0] = 0
        im_array = np.dstack([chanel_r, chanel_g, chanel_b])

    return im_array


def check_sample_image(sample, accepted_mimetypes=None):
    """
        Check sample information
        :param sample: Sample structure
        :type sample: tesla_ce_provider.models.base.Sample | tesla_provider.models.base.Request
        :param accepted_mimetypes: Accepted mimetype values
        :type accepted_mimetypes: list
        :return: An object with the image and mimetype or the found errors
        :rtype: dict
    """
    # Check mimetype
    mimetype = None
    try:
        sample_mimetype = sample.data.split(',')[0].split(';')[0].split(':')[1]
        if len(sample_mimetype.strip()) == 0:
            sample_mimetype = None
    except IndexError:
        sample_mimetype = None
    if sample.mime_type is not None:
        mimetype = sample.mime_type
    if sample_mimetype is not None and mimetype is not None and sample_mimetype != mimetype:
        return {
            'valid': False,
            'msg': "Mimetype in sample data differs from sample mimetype",
            'code': message.Provider.PROVIDER_INVALID_MIMETYPE.value,
            'image': None
        }
    if mimetype is None:
        mimetype = sample_mimetype
    if mimetype is None:
        return {
            'valid': False,
            'msg': "Missing mimetype.",
            'code': message.Provider.PROVIDER_MISSING_MIMETYPE.value,
            'image': None
        }
    if mimetype not in accepted_mimetypes:
        return {
            'valid': False,
            'msg': "Invalid mimetype. Accepted types are: [{}]".format(', '.join(accepted_mimetypes)),
            'code': message.Provider.PROVIDER_INVALID_MIMETYPE.value,
            'image': None
        }

    # Open the image
    image = get_sample_image(sample)
    if image is None:
        return {
            'valid': False,
            'msg': "Invalid image format in sample data.",
            'code': message.Provider.PROVIDER_INVALID_SAMPLE_DATA.value,
            'image': None
        }

    return {
        'valid': True,
        'mimetype': mimetype,
        'image': image
    }


def get_face_image(image, face_locations):
    """
        Cut the face region from an image and returns it as a JPEG image
        :param image: The source image
        :type image: np.array
        :param face_locations: Face location as (top, right, bottom, left)
        :type face_locations: tuple
        :return: Face image in JPEG format
        :rtype: str
    """
    # Get the image
    img = Image.fromarray(image)

    # Crop image
    # (It will not change orginal image)
    face_img = img.crop((face_locations[3], face_locations[0], face_locations[1], face_locations[2]))

    buffer = BytesIO()
    face_img.save(buffer, format='jpeg')
    buffer.flush()

    return 'data:image/jpeg;base64,{}'.format(base64.b64encode(buffer.getvalue()).decode('utf-8'))


def is_black_image(img):
    """
        Check if an image is all black
        :param img: Image to check
        :type img: np.array
        :return: True if the image is black or False otherwise
        :rtype: bool
    """
    image = Image.fromarray(img)
    extrema = image.convert("L").getextrema()
    if extrema[0] == 0 and extrema[1] < 5:
        return True

    return False

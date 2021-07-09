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
""" TeSLA CE Face Recognition module """
import face_recognition
import simplejson
import numpy as np
from tesla_ce_provider import BaseProvider, result, message
from tesla_ce_provider.models.fr import FRValidationData
from tesla_ce_provider.provider.audit.fr import FaceRecognitionAudit
from . import utils
from .models import FRSimpleModel


class TFRProvider(BaseProvider):
    """
        TeSLA Face Recognition implementation
    """
    _logger = None

    def __init__(self):
        super().__init__()
        self._model_class = FRSimpleModel
        self._video_mimetypes = []
        self._image_mimetypes = ['image/jpeg', 'image/png']
        self.accepted_mimetypes = self._video_mimetypes + self._image_mimetypes
        self.config = {
            'model': 'cnn',
            'fast_validation': False,
            'number_of_times_to_upsample': 1,
            'min_enrol_samples': 10,
            'target_enrol_samples': 15,
            'encoding_num_jitters': 5
        }

    def set_options(self, options):
        """
            Set options for the provider
            :param options: Provider options following provider options_scheme definition
            :type options: dict
        """
        if options is not None:
            if 'model' in options:
                self.config['model'] = options['model']
            if 'fast_validation' in options:
                self.config['fast_validation'] = options['fast_validation']
            if 'upsample_times' in options:
                self.config['number_of_times_to_upsample'] = options['upsample_times']
            if 'min_enrol_samples' in options:
                self.config['min_enrol_samples'] = options['min_enrol_samples']
            if 'target_enrol_samples' in options:
                self.config['target_enrol_samples'] = options['target_enrol_samples']
            if 'encoding_num_jitters' in options:
                self.config['encoding_num_jitters'] = options['encoding_num_jitters']

    def enrol(self, samples, model=None):
        """
            Update the model with a new enrolment sample
            :param samples: Enrolment samples
            :type sample: list
            :param model: Current model
            :type model: dict
            :return: Enrolment result
            :rtype: tesla_ce_provider.result.EnrolmentResult
        """
        # Load model
        self.log_trace('TFR: Start enrolment process.')
        tfr_model = self._model_class(model)
        tfr_model.set_required_samples(self.config['target_enrol_samples'])
        tfr_model.set_min_required_samples(self.config['min_enrol_samples'])

        self.log_trace('TFR: Start processing enrolment samples')
        for sample in samples:
            self.log_trace('TFR: Sample process START')
            # Get the image
            image = utils.get_sample_image(sample)
            if image is None:
                self.log_trace('TFR: Image is None. Skip enrolment for current sample: \n{}'.format(
                    simplejson.dumps(sample, indent=4, skipkeys=True))
                )
                continue

            # Get face locations
            face_locations = None
            if not self.config['fast_validation']:
                self.log_trace('TFR: Search for matching validation data.')
                # If fast validation is disabled, information obtained in the validation can be used.
                for validation in sample.validations:
                    if validation.provider['id'] == self.provider_id:
                        self.log_trace('Validation data is available. Using validated information.')
                        face_locations = [(
                            # top
                            validation.face_location['top'],
                            # right
                            validation.face_location['left'] + validation.face_location['width'] - 1,
                            # bottom
                            validation.face_location['top'] + validation.face_location['height'] - 1,
                            # left
                            validation.face_location['left'],
                        ),]
            if face_locations is None:
                self.log_trace('TFR: Validation data is not available. Find faces in image.')
                face_locations = face_recognition.face_locations(
                    image,
                    number_of_times_to_upsample=self.config['number_of_times_to_upsample'],
                    model=self.config['model']
                )
                if len(face_locations) == 0:
                    self.log_trace('TFR: No faces in image. Brake enrolment process.')
                    return result.EnrolmentResult(tfr_model.to_json(),
                                                  tfr_model.get_percentage(),
                                                  tfr_model.can_analyse(),
                                                  valid=False,
                                                  error_message=message.Provider.PROVIDER_INVALID_SAMPLE_DATA.value)
                if len(face_locations) > 1:
                    self.log_trace('TFR: Multiple faces in image. Brake enrolment process.')
                    return result.EnrolmentResult(tfr_model.to_json(),
                                                  tfr_model.get_percentage(),
                                                  tfr_model.can_analyse(),
                                                  valid=False,
                                                  error_message=message.Provider.PROVIDER_MULTIPLE_PEOPLE.value)

            # Get face descriptor
            self.log_trace('TFR: One face detected. Compute encodings.')
            encoding = face_recognition.face_encodings(image,
                                                       face_locations,
                                                       num_jitters=self.config['encoding_num_jitters'])
            self.log_trace('TFR: Add encodings to model.')
            tfr_model.add_sample(sample, encoding)
            self.log_trace('TFR: Sample process END')
        self.log_trace('TFR: Enrolment process finished: [percentage={}]'.format(tfr_model.get_percentage()))
        return result.EnrolmentResult(tfr_model.to_json(), tfr_model.get_percentage(), tfr_model.can_analyse(),
                                      used_samples=tfr_model.get_used_samples())

    def validate_sample(self, sample, validation_id):
        """
            Validate an enrolment sample
            :param sample: Enrolment sample
            :type sample: tesla_ce_provider.models.base.Sample
            :param validation_id: Request validation identification
            :type validation_id: int
            :return: Validation result
            :rtype: tesla_ce_provider.ValidationResult
        """
        # Check provided input
        sample_check = utils.check_sample_image(sample, self.accepted_mimetypes)
        if not sample_check['valid']:
            return result.ValidationResult(False, sample_check['msg'],
                                           message_code_id=sample_check['code'])
        # TODO: Check mimetype to use different approaches for video and image inputs
        # mimetype = sample_check['mimetype']
        image = sample_check['image']

        if utils.is_black_image(image):
            return result.ValidationResult(False, "Black image.",
                                           message_code_id=message.Provider.PROVIDER_BLACK_IMAGE.value)

        # Detect faces (top, right, bottom, left)
        if self.config['fast_validation']:
            face_locations = face_recognition.face_locations(
                image,
                number_of_times_to_upsample=0,
                model="hog"
            )
        else:
            face_locations = face_recognition.face_locations(
                image,
                number_of_times_to_upsample=self.config['number_of_times_to_upsample'],
                model=self.config['model']
            )

        if len(face_locations) == 0:
            return result.ValidationResult(False, "No faces in image.",
                                           message_code_id=message.Provider.PROVIDER_NO_FACE_DETECTED.value)
        if len(face_locations) > 1:
            return result.ValidationResult(False, "Multiple faces in the image.",
                                           message_code_id=message.Provider.PROVIDER_MULTIPLE_PEOPLE.value)

        face = FRValidationData()
        face.set_instrument(self.instrument['id'], self.instrument['acronym'])
        face.set_provider(self.provider_id, self.info['acronym'], self.info['version'])
        face.set_location(face_locations[0][3],
                          face_locations[0][0],
                          face_locations[0][2] - face_locations[0][0] + 1,
                          face_locations[0][1] - face_locations[0][3] + 1)

        return result.ValidationResult(True,
                                       contribution=1.0 / float(self.config['target_enrol_samples']),
                                       info=face.to_json())

    def verify(self, request, model):
        """
            Verify a learner request
            :param request: Verification request
            :type request: tesla_ce_provider.models.base.Request
            :param model: Provider model
            :type model: dict
            :return: Verification result
            :rtype: tesla_ce_provider.VerificationResult
        """
        # Load model
        tfr_model = self._model_class(model)

        # Check provided input
        sample_check = utils.check_sample_image(request, self.accepted_mimetypes)
        if not sample_check['valid']:
            return result.VerificationResult(True, error_message=sample_check['msg'],
                                             message_code=sample_check['code'])

        # TODO: Check mimetype to use different approaches for video and image inputs
        # mimetype = sample_check['mimetype']
        image = sample_check['image']

        if utils.is_black_image(image):
            return result.VerificationResult(True, code=result.VerificationResult.AlertCode.WARNING,
                                             error_message="Black Image.",
                                             message_code=message.Provider.PROVIDER_BLACK_IMAGE.value)

        # Detect faces in current image
        face_locations = face_recognition.face_locations(
            image,
            number_of_times_to_upsample=self.config['number_of_times_to_upsample'],
            model=self.config['model']
        )
        if len(face_locations) == 0:
            return result.VerificationResult(True, code=result.VerificationResult.AlertCode.WARNING,
                                             error_message="No faces in image.",
                                             message_code=message.Provider.PROVIDER_NO_FACE_DETECTED.value)
        # Get sample encodings
        encodings = face_recognition.face_encodings(image,
                                                    face_locations,
                                                    num_jitters=self.config['encoding_num_jitters'])
        # Get reference encodings
        reference_encodings = tfr_model.get_encodings()

        # Compute distances between found faces and model
        distances = []
        audit = FaceRecognitionAudit()

        for i, face_encoding in enumerate(encodings, 0):
            distances = list(face_recognition.face_distance(reference_encodings, face_encoding))
            distance = min(distances)
            idx = int(np.argmin(distances))
            audit.add_face(coordinates=face_locations[i],
                           score=1.0 - distance,
                           image=utils.get_face_image(image, face_locations[i]),
                           most_similar=tfr_model.get_sample_id(idx))
            distances.append(distance)

        # Get the minimum distance and convert to the final score
        score = 1.0 - min(distances)

        # Check alerts
        if len(face_locations) > 1:
            return result.VerificationResult(True, result=score,
                                             code=result.VerificationResult.AlertCode.ALERT,
                                             message_code=message.Provider.PROVIDER_MULTIPLE_PEOPLE,
                                             audit=audit)

        return result.VerificationResult(True, result=score,
                                         code=result.VerificationResult.AlertCode.OK, audit=audit)

    def on_notification(self, key, info):
        """
            Respond to a notification task
            :param key: The notification task unique key
            :type key: str
            :param info: Information stored in the notification
            :type info: dict

            self.update_or_create_notification(result.NotificationTask('key', countdown=30, info={'my_field': 3}))
        """
        raise NotImplementedError('Method not implemented on provider')

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
""" TeSLA CE Face Recognition models module """
from tesla_ce_provider.models import SimpleModel
import numpy as np


class FRSimpleModel(SimpleModel):
    """
        Model for FaceRecognition based on a list of reference images
    """
    def __init__(self, model_object=None):
        super().__init__(model_object=model_object)

    def add_sample(self, sample, features=None):
        """
            Add given sample to model and update the enrolment percentage
            :param sample: Sample object
            :type sample: tesla_ce_provider.models.base.Sample
            :param features: Optional provider representation for this sample
            :type features: dict
        """
        # Change features to be serializable
        features = features[0].tolist()
        super().add_sample(sample, features)

    def get_encodings(self):
        """
            Get the list of keypoint encodings

            :return: list
        """
        encodings = []
        for sample in self._samples:
            encodings.append(np.array(sample['features']))
        return encodings

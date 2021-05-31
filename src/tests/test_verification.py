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
import pytest
import os
from .tfr_utils import get_sample, get_request, check_enrolment_result, check_verification_result

PYTEST_MISSING_MODELS_MSG = 'Missing user models'

# Users IDs
u1_uid = 'e9d9580f-a9b3-4580-bd23-b6215e505610'
u2_uid = '255e6aad-4a3e-440c-90e9-a432339037ad'

# Users enrolment images
u1_enr = [
    'user1_enr_up1', 'user1_enr_front1', 'user1_enr_up1', 'user1_enr_down1',
    'user1_enr_left1', 'user1_enr_right1'
]
u2_enr = [
    'user2_enr_up1', 'user2_enr_front1', 'user2_enr_up1', 'user2_enr_down1',
    'user2_enr_left1', 'user2_enr_right1'
]

# Users test images
u1_test = [
    'user1_test_1',
]
u2_test = [
    'user2_test_1',
]

fast_test_env = os.getenv('TFR_FAST_TEST', None)
fast_test = True
if fast_test_env is not None:
    fast_test = fast_test_env in ['1', 1, True, 'true', 'True']

users = [
        {'learner_id': u1_uid, 'enrolment': u1_enr, 'test': u1_test},
        {'learner_id': u2_uid, 'enrolment': u2_enr, 'test': u2_test},
    ]

users_all = users
if fast_test:
    users = [users[0], ]
models = {}


@pytest.mark.dependency()
def test_progressive_enrolment(tfr_provider):

    tfr_provider.set_options({'min_enrol_samples': 3, 'target_enrol_samples': 6})

    for user in users:
        model = None
        sample_id = 0
        for img in user['enrolment']:
            sample = get_sample(image=img, sample_id=sample_id, learner_id=user['learner_id'])
            sample_id += 1
            result = tfr_provider.enrol(samples=[sample], model=model)
            check_enrolment_result(result)
            assert result.valid
            assert result.error_message is None

            if sample_id < 3:
                assert not result.can_analyse
            else:
                assert result.can_analyse
            assert result.percentage is not None
            if sample_id == 6:
                assert (1.0 - result.percentage) < 0.0001
            else:
                assert 0 <= result.percentage < 1.0
            model = result.model
            assert len(model['samples']) == sample_id
            assert len(result.used_samples) == sample_id

        assert model['percentage'] is not None
        assert (1.0 - model['percentage']) < 0.0001
        models[user['learner_id']] = model


def test_batch_enrolment(tfr_provider):

    if fast_test:
        pytest.skip('Using Fast Test option. Skip this test.')

    tfr_provider.set_options({'min_enrol_samples': 3, 'target_enrol_samples': 6 })
    for user in users:
        sample_id = 0
        samples = []
        for img in user['enrolment']:
            samples.append(get_sample(image=img, sample_id=sample_id, learner_id=user['learner_id']))
            sample_id += 1

        result = tfr_provider.enrol(samples=samples, model=None)
        check_enrolment_result(result)
        assert result.valid
        assert result.error_message is None
        assert result.can_analyse
        assert (1.0 - result.percentage) < 0.0001
        assert len(result.model['samples']) == 6
        assert len(result.used_samples) == 6
        assert (1.0 - result.model['percentage']) < 0.0001


@pytest.mark.dependency(depends=["test_progressive_enrolment"], scope='module')
def test_identity_verification_enrol(tfr_provider):
    test_progressive_enrolment(tfr_provider)
    for user in users:
        if user['learner_id'] not in models:
            pytest.skip(PYTEST_MISSING_MODELS_MSG)
    idx = 1
    for user in users:
        request = get_request(image=user['enrolment'][0], learner_id=user['learner_id'])
        result = tfr_provider.verify(request, models[user['learner_id']], idx)
        check_verification_result(result)
        assert result.status == 1
        assert result.code == result.AlertCode.OK
        assert result.result > 0.9
        idx += 1


@pytest.mark.dependency(depends=["test_progressive_enrolment"], scope='module')
def test_identity_verification(tfr_provider):

    for user in users:
        if user['learner_id'] not in models:
            pytest.skip(PYTEST_MISSING_MODELS_MSG)

    idx = 1
    for user in users:
        for img in user['test']:
            request = get_request(image=img, learner_id=user['learner_id'])
            result = tfr_provider.verify(request, models[user['learner_id']], idx)
            check_verification_result(result)
            assert result.status == 1
            assert result.code == result.AlertCode.OK
            assert result.result > tfr_provider.info['alert_below']
            idx += 1


@pytest.mark.dependency(depends=["test_progressive_enrolment"], scope='module')
def test_identity_refutation(tfr_provider):

    for user in users:
        if user['learner_id'] not in models:
            pytest.skip(PYTEST_MISSING_MODELS_MSG)

    user_idx = 0
    idx = 1
    for user in users:
        ref_idx = (user_idx+1) % len(users_all)
        user_idx += 1
        for img in users_all[ref_idx]['test']:
            request = get_request(image=img, learner_id=user['learner_id'])
            result = tfr_provider.verify(request, models[user['learner_id']], idx)
            check_verification_result(result)
            assert result.status == 1
            assert result.code == result.AlertCode.OK
            assert result.result < tfr_provider.info['warning_below']
            idx += 1


@pytest.mark.dependency(depends=["test_progressive_enrolment"], scope='module')
def test_verify_multiple_people_with_user(tfr_provider):
    from tesla_ce_provider.message import Provider

    user = users[0]
    if user['learner_id'] not in models:
        pytest.skip(PYTEST_MISSING_MODELS_MSG)

    request = get_request(image='multiple_faces', learner_id=user['learner_id'])
    idx = 1
    result = tfr_provider.verify(request, models[user['learner_id']], idx)
    check_verification_result(result)
    assert result.status == 1
    assert result.code == result.AlertCode.ALERT
    assert result.message_code == Provider.PROVIDER_MULTIPLE_PEOPLE
    assert result.result > tfr_provider.info['alert_below']


@pytest.mark.dependency(depends=["test_progressive_enrolment"], scope='module')
def test_verify_multiple_people_without_user(tfr_provider):
    from tesla_ce_provider.message import Provider

    user = users[0]
    if user['learner_id'] not in models:
        pytest.skip(PYTEST_MISSING_MODELS_MSG)

    request = get_request(image='multiple_faces_2', learner_id=user['learner_id'])
    idx = 1
    result = tfr_provider.verify(request, models[user['learner_id']], idx)
    check_verification_result(result)
    assert result.status == 1
    assert result.code == result.AlertCode.ALERT
    assert result.message_code == Provider.PROVIDER_MULTIPLE_PEOPLE
    assert result.result < tfr_provider.info['warning_below']


@pytest.mark.dependency(depends=["test_progressive_enrolment"], scope='module')
def test_verify_no_face(tfr_provider):
    user = users[0]
    if user['learner_id'] not in models:
        pytest.skip(PYTEST_MISSING_MODELS_MSG)

    request = get_request(image='no_face', learner_id=user['learner_id'])
    idx = 1
    result = tfr_provider.verify(request, models[user['learner_id']], idx)
    check_verification_result(result)
    assert result.status == 1
    assert result.code == result.AlertCode.WARNING
    assert result.message_code == 'PROVIDER_NO_FACE_DETECTED'


@pytest.mark.dependency(depends=["test_progressive_enrolment"], scope='module')
def test_verify_black_image(tfr_provider):
    user = users[0]
    if user['learner_id'] not in models:
        pytest.skip(PYTEST_MISSING_MODELS_MSG)

    request = get_request(image='black_image', learner_id=user['learner_id'])
    idx = 1
    result = tfr_provider.verify(request, models[user['learner_id']], idx)
    check_verification_result(result)
    assert result.status == 1
    assert result.code == result.AlertCode.WARNING
    assert result.message_code == 'PROVIDER_BLACK_IMAGE'


def perform_batch_enrolment_with_validation(tfr_provider):
    from tesla_ce_provider.models.parser import parse_validation_data
    result_id = 1
    for user in users:
        sample_id = 0
        samples = []
        for img in user['enrolment']:
            sample = get_sample(image=img, sample_id=sample_id, learner_id=user['learner_id'])
            val_result = tfr_provider.validate_sample(sample, result_id=result_id)
            if val_result.status == 1:
                validation = parse_validation_data(val_result.info)
                sample = get_sample(image=img, sample_id=sample_id, learner_id=user['learner_id'],
                                    validations=[validation])
                samples.append(sample)
            sample_id += 1
            result_id += 1

        result = tfr_provider.enrol(samples=samples, model=None)
        check_enrolment_result(result)
        assert result.valid
        assert result.error_message is None
        assert result.can_analyse
        assert result.percentage > 0


def test_batch_enrolment_with_normal_validation(tfr_provider):
    tfr_provider.set_options({'fast_validation': False, 'min_enrol_samples': 3, 'target_enrol_samples': 6 })
    perform_batch_enrolment_with_validation(tfr_provider)


def test_batch_enrolment_with_fast_validation(tfr_provider):
    tfr_provider.set_options({'fast_validation': True, 'min_enrol_samples': 3, 'target_enrol_samples': 6 })
    perform_batch_enrolment_with_validation(tfr_provider)


def test_batch_enrolment_with_normal_validation_other(tfr_provider):
    from tesla_ce_provider.models.parser import parse_validation_data
    tfr_provider.set_options({'fast_validation': False, 'min_enrol_samples': 3, 'target_enrol_samples': 6 })
    result_id = 1
    for user in users:
        sample_id = 0
        samples = []
        for img in user['enrolment']:
            sample = get_sample(image=img, sample_id=sample_id, learner_id=user['learner_id'])
            val_result = tfr_provider.validate_sample(sample, result_id=result_id)
            if val_result.status == 1:
                new_val_info = val_result.info
                new_val_info['provider']['id'] = 30
                validation = parse_validation_data(new_val_info)
                sample = get_sample(image=img, sample_id=sample_id, learner_id=user['learner_id'],
                                    validations=[validation])
                samples.append(sample)
            sample_id += 1
            result_id += 1

        result = tfr_provider.enrol(samples=samples, model=None)
        check_enrolment_result(result)
        assert result.valid
        assert result.error_message is None
        assert result.can_analyse
        assert result.percentage > 0

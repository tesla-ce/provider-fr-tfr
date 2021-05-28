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
""" Test fixtures module """
import pytest
from logging import getLogger

@pytest.fixture
def tesla_ce_provider_conf():
    return {
        'provider_class': 'tfr.TFRProvider',
        'provider_desc_file': None,
        'instrument': None,
        'info': None
    }


@pytest.fixture
def tfr_provider(tesla_ce_base_provider):
    from tfr import TFRProvider
    assert isinstance(tesla_ce_base_provider, TFRProvider)

    logger = getLogger('tfr Tests')
    tesla_ce_base_provider.set_logger(logger.info)

    return tesla_ce_base_provider

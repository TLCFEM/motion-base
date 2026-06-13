#  Copyright (C) 2022-2026 Theodore Chang
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os.path

import numpy as np
import pytest

from mb.record.parser import ParserNZSM
from mb.record.response_spectrum import response_spectrum
from mb.record.utility import str_factory
from mb.utility import UPath


@pytest.mark.parametrize(
    "file_path,results",
    [
        pytest.param(
            "data/20110222_015029_MQZ.V2A",
            [
                {
                    "file_name": "20110222_015029_MQZ.V2A",
                    "file_hash": "e84a0bdb5a11b1cc2e5103a5281a029f00b4d130688d95249dee148ceada48f5",
                    "category": "processed",
                    "region": "nz",
                    "magnitude": 5.86,
                    "maximum_acceleration": 133.63,
                    "event_time": "2011-02-22T01:50:29",
                    "event_location": [172.63, -43.59],
                    "depth": 7.0,
                    "station_code": "MQZ",
                    "station_location": [172.654, -43.708],
                    "record_time": "2011-02-22T01:50:12",
                    "last_update_time": "2015-05-27T12:00:00",
                    "sampling_frequency": 50.0,
                    "sampling_frequency_unit": "hertz",
                    "duration": 65.98,
                    "direction": "E",
                    "scale_factor": 1e-05,
                    "raw_data_unit": "millimeter / second ** 2",
                },
                {
                    "file_name": "20110222_015029_MQZ.V2A",
                    "file_hash": "756ef9711910fdff4db32dc206df0dd04d09d0ed0e63acb5ef36dd55d85e5408",
                    "category": "processed",
                    "region": "nz",
                    "magnitude": 5.86,
                    "maximum_acceleration": 133.21,
                    "event_time": "2011-02-22T01:50:29",
                    "event_location": [172.63, -43.59],
                    "depth": 7.0,
                    "station_code": "MQZ",
                    "station_location": [172.654, -43.708],
                    "record_time": "2011-02-22T01:50:12",
                    "last_update_time": "2015-05-27T12:00:00",
                    "sampling_frequency": 50.0,
                    "sampling_frequency_unit": "hertz",
                    "duration": 65.98,
                    "direction": "N",
                    "scale_factor": 1e-05,
                    "raw_data_unit": "millimeter / second ** 2",
                },
                {
                    "file_name": "20110222_015029_MQZ.V2A",
                    "file_hash": "36dddac1d8dfee8350d23e53157cb9e163f4e1d2f486fc132560ba8e299fbb57",
                    "category": "processed",
                    "region": "nz",
                    "magnitude": 5.86,
                    "maximum_acceleration": 56.410000000000004,
                    "event_time": "2011-02-22T01:50:29",
                    "event_location": [172.63, -43.59],
                    "depth": 7.0,
                    "station_code": "MQZ",
                    "station_location": [172.654, -43.708],
                    "record_time": "2011-02-22T01:50:12",
                    "last_update_time": "2015-05-27T12:00:00",
                    "sampling_frequency": 50.0,
                    "sampling_frequency_unit": "hertz",
                    "duration": 65.98,
                    "direction": "UP",
                    "scale_factor": 1e-05,
                    "raw_data_unit": "millimeter / second ** 2",
                },
            ],
        ),
        pytest.param(
            "data/20190904_070311_WAKS_20.V1A",
            [
                {
                    "file_name": "20190904_070311_WAKS_20.V1A",
                    "file_hash": "dae8a577f96baf39948e1c825abfb762a0e94a7e00b85efb29ddd46d4c287719",
                    "category": "unprocessed",
                    "region": "nz",
                    "magnitude": 5.02,
                    "maximum_acceleration": 7.5,
                    "event_time": "2019-09-04T07:02:52",
                    "event_location": [175.91, -38.851],
                    "depth": 5.0,
                    "station_code": "WAKS",
                    "station_location": [176.252, -39.773],
                    "record_time": "2019-09-04T07:02:31",
                    "last_update_time": "2019-10-01T11:00:00",
                    "sampling_frequency": 200.0,
                    "sampling_frequency_unit": "hertz",
                    "duration": 127.0,
                    "direction": "UP",
                    "scale_factor": 1e-05,
                    "raw_data_unit": "millimeter / second ** 2",
                }
            ],
        ),
        pytest.param(
            "data/I06465B10.V2A",
            [
                {
                    "file_name": "I06465B10.V2A",
                    "file_hash": "7a6ba3c50333e6a53304553e88069a9ed5da6f195511ea59aa546376a835792c",
                    "category": "processed",
                    "region": "nz",
                    "magnitude": 5.5,
                    "maximum_acceleration": 5.32,
                    "event_time": "2006-07-23T00:37:37",
                    "event_location": [173.26, -40.6],
                    "depth": 180.0,
                    "station_code": "465B",
                    "station_location": [174.954, -41.208],
                    "last_update_time": "2015-05-06T12:00:00",
                    "sampling_frequency": 200.0,
                    "sampling_frequency_unit": "hertz",
                    "duration": 33.0,
                    "direction": "N87E",
                    "scale_factor": 1e-05,
                    "raw_data_unit": "millimeter / second ** 2",
                },
                {
                    "file_name": "I06465B10.V2A",
                    "file_hash": "0225673a3373c82a758d035fcb3f368242a417cbb128086b0f1ca80273e526d0",
                    "category": "processed",
                    "region": "nz",
                    "magnitude": 5.5,
                    "maximum_acceleration": 3.7700000000000005,
                    "event_time": "2006-07-23T00:37:37",
                    "event_location": [173.26, -40.6],
                    "depth": 180.0,
                    "station_code": "465B",
                    "station_location": [174.954, -41.208],
                    "last_update_time": "2015-05-06T12:00:00",
                    "sampling_frequency": 200.0,
                    "sampling_frequency_unit": "hertz",
                    "duration": 33.0,
                    "direction": "N03W",
                    "scale_factor": 1e-05,
                    "raw_data_unit": "millimeter / second ** 2",
                },
                {
                    "file_name": "I06465B10.V2A",
                    "file_hash": "24a19ee06e4b1be4ce65057e31a84020e39c1bc83655a8fbe17f96f1de3f3d6d",
                    "category": "processed",
                    "region": "nz",
                    "magnitude": 5.5,
                    "maximum_acceleration": 1.8399999999999999,
                    "event_time": "2006-07-23T00:37:37",
                    "event_location": [173.26, -40.6],
                    "depth": 180.0,
                    "station_code": "465B",
                    "station_location": [174.954, -41.208],
                    "last_update_time": "2015-05-06T12:00:00",
                    "sampling_frequency": 200.0,
                    "sampling_frequency_unit": "hertz",
                    "duration": 33.0,
                    "direction": "UP",
                    "scale_factor": 1e-05,
                    "raw_data_unit": "millimeter / second ** 2",
                },
            ],
        ),
        pytest.param(
            "data/D9644D08.V2A",
            [
                {
                    "file_name": "D9644D08.V2A",
                    "file_hash": "aba37c2d199668cae0e84ad2329b9cf093fbe45a14f49d97642874cd856f25da",
                    "category": "processed",
                    "region": "nz",
                    "magnitude": 5.5,
                    "maximum_acceleration": 31.5,
                    "event_time": "1999-01-03T07:00:21",
                    "event_location": [174.51, -41.09],
                    "depth": 57.0,
                    "station_code": "644D",
                    "station_location": [174.882, -41.219],
                    "last_update_time": "2004-09-06T12:00:00",
                    "sampling_frequency": 50.0,
                    "sampling_frequency_unit": "hertz",
                    "duration": 47.64,
                    "direction": "N65W",
                    "scale_factor": 1e-05,
                    "raw_data_unit": "millimeter / second ** 2",
                },
                {
                    "file_name": "D9644D08.V2A",
                    "file_hash": "2ba22b81f00d49c9e8e8142226944e2b999fa2bd3e0ab307fdcf7ca9f2ed3f7f",
                    "category": "processed",
                    "region": "nz",
                    "magnitude": 5.5,
                    "maximum_acceleration": 33.32,
                    "event_time": "1999-01-03T07:00:21",
                    "event_location": [174.51, -41.09],
                    "depth": 57.0,
                    "station_code": "644D",
                    "station_location": [174.882, -41.219],
                    "last_update_time": "2004-09-06T12:00:00",
                    "sampling_frequency": 50.0,
                    "sampling_frequency_unit": "hertz",
                    "duration": 47.64,
                    "direction": "S25W",
                    "scale_factor": 1e-05,
                    "raw_data_unit": "millimeter / second ** 2",
                },
                {
                    "file_name": "D9644D08.V2A",
                    "file_hash": "f4d8cfeb7fe73488fede15a5a70038e87a47091657a3f1e8a4857e3df0e642db",
                    "category": "processed",
                    "region": "nz",
                    "magnitude": 5.5,
                    "maximum_acceleration": 25.380000000000003,
                    "event_time": "1999-01-03T07:00:21",
                    "event_location": [174.51, -41.09],
                    "depth": 57.0,
                    "station_code": "644D",
                    "station_location": [174.882, -41.219],
                    "last_update_time": "2004-09-06T12:00:00",
                    "sampling_frequency": 50.0,
                    "sampling_frequency_unit": "hertz",
                    "duration": 47.64,
                    "direction": "UP",
                    "scale_factor": 1e-05,
                    "raw_data_unit": "millimeter / second ** 2",
                },
            ],
        ),
        pytest.param(
            "data/D5054A01.V2A",
            [
                {
                    "file_name": "D5054A01.V2A",
                    "file_hash": "902bb8ae33530ac86f91a0140c8ea7d2260f23bd88432287bf406c18642d5490",
                    "category": "processed",
                    "region": "nz",
                    "magnitude": 5.3,
                    "maximum_acceleration": 15.990000000000002,
                    "event_time": "1995-09-26T16:53:35",
                    "event_location": [168.32, -44.23],
                    "depth": 5.0,
                    "station_code": "054A",
                    "station_location": [169.043, -43.884],
                    "last_update_time": "2001-05-02T12:00:00",
                    "sampling_frequency": 50.0,
                    "sampling_frequency_unit": "hertz",
                    "duration": 35.56,
                    "direction": "N80E",
                    "scale_factor": 1e-05,
                    "raw_data_unit": "millimeter / second ** 2",
                },
                {
                    "file_name": "D5054A01.V2A",
                    "file_hash": "4f3be589a3ed7d6e9d4befdf60916eabfd125e7e04716cef7c193744930951fb",
                    "category": "processed",
                    "region": "nz",
                    "magnitude": 5.3,
                    "maximum_acceleration": 9.72,
                    "event_time": "1995-09-26T16:53:35",
                    "event_location": [168.32, -44.23],
                    "depth": 5.0,
                    "station_code": "054A",
                    "station_location": [169.043, -43.884],
                    "last_update_time": "2001-05-02T12:00:00",
                    "sampling_frequency": 50.0,
                    "sampling_frequency_unit": "hertz",
                    "duration": 35.56,
                    "direction": "N10W",
                    "scale_factor": 1e-05,
                    "raw_data_unit": "millimeter / second ** 2",
                },
                {
                    "file_name": "D5054A01.V2A",
                    "file_hash": "8adaf62ae0d922f5093665b7fb68daad0f322e807df09b71db24c22c4040a369",
                    "category": "processed",
                    "region": "nz",
                    "magnitude": 5.3,
                    "maximum_acceleration": 6.33,
                    "event_time": "1995-09-26T16:53:35",
                    "event_location": [168.32, -44.23],
                    "depth": 5.0,
                    "station_code": "054A",
                    "station_location": [169.043, -43.884],
                    "last_update_time": "2001-05-02T12:00:00",
                    "sampling_frequency": 50.0,
                    "sampling_frequency_unit": "hertz",
                    "duration": 35.56,
                    "direction": "UP",
                    "scale_factor": 1e-05,
                    "raw_data_unit": "millimeter / second ** 2",
                },
            ],
        ),
    ],
)
async def test_nz_parse_file(pwd, file_path, results, mongo_connection):
    records = await ParserNZSM.parse_file(os.path.join(pwd, file_path), str_factory())
    assert results == [
        x.model_dump(
            mode="json",
            exclude_none=True,
            exclude_defaults=True,
            exclude={"raw_data", "id", "uploaded_by"},
        )
        for x in records
    ]


@pytest.mark.parametrize("file_path", ["data/nz_test.tar.gz"])
async def test_nz_parse_archive(pwd, file_path, mongo_connection):
    await ParserNZSM.parse_archive(
        archive_obj=UPath(pwd) / file_path, user_id=str_factory()
    )


def test_nz_response_spectrum():
    motion = np.array([0, 1, 1, 0, 2, 0, 0], dtype=float)
    interval = 0.01
    period = np.arange(0.1, 0.2, interval)
    response_spectrum(0.05, interval, motion, period)

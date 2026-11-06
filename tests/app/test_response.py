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

from datetime import UTC, datetime

import numpy as np
import pytest
from pydantic import ValidationError

from mb.app.response import (
    MetadataResponse,
    PaginationConfig,
    PaginationResponse,
    ProcessConfig,
    QueryConfig,
    RecordResponse,
    UploadTaskResponse,
)


def _record_response(**kwargs) -> RecordResponse:
    data = {
        "id": "record-id",
        "raw_data_unit": "cm/s/s",
        "time_interval": 0.01,
        "waveform": [0.0, 1.0, -1.0, 0.5],
    }
    data.update(kwargs)
    return RecordResponse(**data)


def test_metadata_response_accepts_model_and_mapping():
    response = MetadataResponse(id="record-id")
    assert response.id == "record-id"

    # A model instance is passed through the before validator untouched.
    assert MetadataResponse.model_validate(response) == response


def test_record_response_default_unit():
    response = _record_response(processed_data_unit="m/s/s")
    assert response.processed_data_unit == "cm/s/s"

    response = _record_response()
    assert response.processed_data_unit is None


def test_normalise_waveform():
    response = _record_response(waveform=[1.0, -2.0, 0.5])
    response.normalise()

    assert response.processed_data_unit == "1"
    assert response.waveform == [0.5, -1.0, 0.25]


def test_normalise_requires_waveform():
    response = _record_response(waveform=None)
    with pytest.raises(RuntimeError, match="Cannot normalise"):
        response.normalise()


def test_filter_waveform():
    window = np.array([0.25, 0.5, 0.25])
    response = _record_response(waveform=[0.0, 1.0, 0.0], time_interval=0.02)
    response.filter(window, up_ratio=2)

    assert response.time_interval == pytest.approx(0.01)
    assert len(response.waveform) == 6


def test_to_spectrum():
    response = _record_response()
    response.to_spectrum()

    assert response.frequency_interval == pytest.approx(25.0)
    assert len(response.spectrum) == 3


def test_to_spectrum_requires_waveform():
    response = _record_response(waveform=None)
    with pytest.raises(RuntimeError, match="Cannot convert to spectrum"):
        response.to_spectrum()


@pytest.mark.parametrize("as_array", [True, False])
def test_to_response_spectrum(as_array):
    response = _record_response(waveform=[0.0, 1.0, -1.0, 0.5, 0.0], time_interval=0.01)
    period = np.array([0.0, 0.1, 0.2]) if as_array else [0.0, 0.1, 0.2]

    response.to_response_spectrum(0.05, period)

    expected = period.tolist() if as_array else period
    assert response.period == expected
    assert len(response.displacement_spectrum) == 3
    assert len(response.velocity_spectrum) == 3
    assert len(response.acceleration_spectrum) == 3


@pytest.mark.parametrize(
    "sort_by,expected",
    [
        ("-magnitude", "-magnitude"),
        ("+event_time", "+event_time"),
        ("-DEPTH", "-depth"),
    ],
)
def test_pagination_sort_by(sort_by, expected):
    assert PaginationConfig(sort_by=sort_by).sort_by == expected


def test_pagination_sort_by_default_and_invalid():
    assert PaginationConfig.validate_sort_by(None) == "-maximum_acceleration"

    with pytest.raises(ValidationError):
        PaginationConfig(sort_by="not-a-field")


def test_pagination_response():
    response = PaginationResponse(total=12, page_size=5, page_number=2)

    assert response.total == 12
    assert response.page_size == 5
    assert response.page_number == 2


def test_query_config_mongo_empty():
    assert QueryConfig().generate_query_string() == {}


def test_query_config_mongo_all_fields():
    config = QueryConfig(
        region="jp",
        category="KNT",
        min_magnitude=4,
        max_magnitude=8,
        event_location=[140.0, 35.0],
        max_event_distance=1000.0,
        station_location=[141.0, 36.0],
        max_station_distance=2000.0,
        from_date=datetime(2000, 1, 1, tzinfo=UTC),
        to_date=datetime(2001, 1, 1, tzinfo=UTC),
        min_pga=10,
        max_pga=100,
        file_name="SZO",
        station_code="SZO",
        direction="NS",
    )

    query = config.generate_query_string()

    assert query["region"] == "jp"
    assert query["category"] == "knt"
    assert query["magnitude"] == {"$gte": 4, "$lte": 8}
    assert query["maximum_acceleration"] == {"$gte": 10, "$lte": 100}
    assert query["direction"] == {"$regex": "NS", "$options": "i"}
    assert query["file_name"] == {"$regex": "SZO", "$options": "i"}
    assert query["station_code"] == {"$regex": "SZO", "$options": "i"}
    assert "$geoWithin" in query["event_location"]
    assert "$geoWithin" in query["station_location"]
    assert "$gte" in query["event_time"]
    assert "$lte" in query["event_time"]


def test_query_config_mongo_default_distances():
    config = QueryConfig(event_location=[140.0, 35.0], station_location=[141.0, 36.0])

    query = config.generate_query_string()

    assert query["event_location"]["$geoWithin"]["$centerSphere"][1] == pytest.approx(
        100000.0 / 6378100.0
    )
    assert query["station_location"]["$geoWithin"]["$centerSphere"][1] == pytest.approx(
        100000.0 / 6378100.0
    )


def test_query_config_elastic_empty():
    assert QueryConfig().generate_elastic_query() == {"bool": {"must": []}}


def test_query_config_elastic_all_fields():
    config = QueryConfig(
        region="jp",
        category="KNT",
        min_magnitude=4,
        max_magnitude=8,
        event_location=[140.0, 35.0],
        max_event_distance=1000.0,
        station_location=[141.0, 36.0],
        max_station_distance=2000.0,
        from_date=datetime(2000, 1, 1, tzinfo=UTC),
        to_date=datetime(2001, 1, 1, tzinfo=UTC),
        min_pga=10,
        max_pga=100,
        file_name="SZO",
        station_code="SZO",
        direction="NS",
    )

    must = config.generate_elastic_query()["bool"]["must"]

    assert {"match": {"region": "jp"}} in must
    assert {"match": {"category": "knt"}} in must
    assert {"range": {"magnitude": {"gte": 4, "lte": 8}}} in must
    assert {
        "range": {"event_time": {"gte": config.from_date, "lte": config.to_date}}
    } in must
    assert {"range": {"maximum_acceleration": {"gte": 10, "lte": 100}}} in must
    assert {
        "geo_distance": {
            "distance": "1000m",
            "event_location": {"lon": 140.0, "lat": 35.0},
        }
    } in must
    assert {
        "geo_distance": {
            "distance": "2000m",
            "station_location": {"lon": 141.0, "lat": 36.0},
        }
    } in must
    assert {"regexp": {"direction": {"value": "NS", "case_insensitive": True}}} in must
    assert {"regexp": {"file_name": {"value": "SZO", "case_insensitive": True}}} in must
    assert {
        "regexp": {"station_code": {"value": "SZO", "case_insensitive": True}}
    } in must


def test_query_config_elastic_default_distances():
    config = QueryConfig(event_location=[140.0, 35.0], station_location=[141.0, 36.0])

    must = config.generate_elastic_query()["bool"]["must"]

    assert {
        "geo_distance": {
            "distance": "100000m",
            "event_location": {"lon": 140.0, "lat": 35.0},
        }
    } in must
    assert {
        "geo_distance": {
            "distance": "100000m",
            "station_location": {"lon": 141.0, "lat": 36.0},
        }
    } in must


def test_process_config_defaults():
    config = ProcessConfig()

    assert config.up_ratio == 1
    assert config.normalised is False
    assert config.with_filter is False


def test_upload_task_response():
    response = UploadTaskResponse(
        id="task-id",
        create_time=datetime.now(UTC),
        total_size=10,
        current_size=4,
    )

    assert response.id == "task-id"

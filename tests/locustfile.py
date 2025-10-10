#  Copyright (C) 2022-2025 Theodore Chang
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

from locust import FastHttpUser, tag, task

from mb.app.response import PaginationConfig, QueryConfig


class HelloWorldUser(FastHttpUser):
    search_query = QueryConfig(
        min_magnitude=6,
        min_pga=300,
        pagination=PaginationConfig(page_size=100),
    ).model_dump(exclude_none=True)

    process_query = {
        "filter_length": 400,
        "filter_type": "bandpass",
        "window_type": "blackmanharris",
        "high_cut": 25,
        "damping_ratio": 0.02,
        "period_end": 1,
        "period_step": 0.001,
        "with_filter": True,
        "with_spectrum": True,
        "with_response_spectrum": True,
    }

    host = "https://tlcfem.top:8443"

    @tag("alive")
    @task
    def alive(self):
        self.client.get("/alive")

    @tag("raw")
    @task
    def raw(self):
        self.client.get("/raw/jackpot")

    @tag("waveform")
    @task
    def waveform(self):
        self.client.get("/waveform/jackpot")

    @tag("search")
    @task
    def search(self):
        self.client.post("/search", json=self.search_query)

    @tag("process")
    @task
    def process(self):
        self.client.post(
            "/process?record_id=a4590f38-5063-5625-bad4-90e3103dcffc",
            json=self.process_query,
        )

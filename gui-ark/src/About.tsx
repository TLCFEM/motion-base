//  Copyright (C) 2022-2026 Theodore Chang
//
//  This program is free software: you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation, either version 3 of the License, or
//  (at your option) any later version.

import { Component, createResource, createSignal } from "solid-js";
import fastapi_logo from "./assets/fastapi.svg";
import beanie_logo from "./assets/beanie.svg";
import leaflet_logo from "./assets/leaflet.svg";
import mb_logo from "./assets/logo.svg";
import mongodb_logo from "./assets/mongodb.svg";
import plotly_logo from "./assets/plotly.svg";
import scipy_logo from "./assets/scipy.svg";
import solid_logo from "./assets/solid.svg";
import taskiq_logo from "./assets/taskiq.svg";
import ark_logo from "./assets/ark.svg";
import tan_logo from "./assets/tanstack.svg";
import { post_total_api, QueryConfig } from "./api";
import { DialogShell } from "./ui";

const statsConfigs = (): QueryConfig[] => [
    { min_magnitude: 0, pagination: {} },
    { min_magnitude: 6, pagination: {} },
    { min_pga: 100, pagination: {} },
];

const AboutModal: Component<{ online: boolean }> = (props) => {
    const [open, setOpen] = createSignal(false);
    const [stats] = createResource(
        () => props.online,
        (online) => (online ? post_total_api(statsConfigs()) : Promise.resolve(null)),
    );

    return (
        <>
            <button class="btn secondary" onClick={() => setOpen(true)}>
                About
            </button>
            <DialogShell open={open()} onOpenChange={setOpen} title="About" size="lg">
                <div class="row">
                    <img src={mb_logo} alt="Motion Base logo" height="46" />
                    <h2>motion-base</h2>
                </div>

                <p class="about-section">
                    This is a demo of the ground motion database. The source code is available at{" "}
                    <a href="https://github.com/TLCFEM/motion-base">github.com/TLCFEM/motion-base</a>.
                </p>

                {stats()?.length === 3 && (
                    <p class="about-section">
                        This server currently contains {stats()![0].toLocaleString()} records. Among them, {stats()![1].toLocaleString()}{" "}
                        records have a magnitude greater than six and {stats()![2].toLocaleString()} records have a PGA greater than 100
                        Gal.
                    </p>
                )}

                <h3 class="about-section">Japan Database</h3>
                <p>
                    The data is retrieved from <a href="https://www.kyoshin.bosai.go.jp/kyoshin/data/index_en.html">NIED</a>. The data is
                    not processed. Users may want to further filter the records.
                </p>

                <h3 class="about-section">New Zealand Database</h3>
                <p>
                    The data is retrieved from the{" "}
                    <a href="https://www.geonet.org.nz/data/supplementary/nzsmdb">New Zealand Strong-Motion</a> database. Some selected
                    strong motions are processed (*.V2A files). The other records (*.V1A files) are not processed. Users may want to further
                    filter the records.
                </p>

                <h3 class="about-section">Built with</h3>
                <div class="about-logos">
                    <a href="https://www.mongodb.com/">
                        <img src={mongodb_logo} alt="MongoDB" />
                    </a>
                    <a href="https://beanie-odm.dev/">
                        <img src={beanie_logo} alt="Beanie" />
                    </a>
                    <a href="https://taskiq-python.github.io/">
                        <img src={taskiq_logo} alt="Taskiq" />
                    </a>
                    <a href="https://scipy.org/">
                        <img src={scipy_logo} alt="SciPy" />
                    </a>
                    <a href="https://fastapi.tiangolo.com/">
                        <img src={fastapi_logo} alt="FastAPI" />
                    </a>
                    <a href="https://www.solidjs.com/">
                        <img src={solid_logo} alt="Solid" />
                    </a>
                    <a href="https://leafletjs.com/">
                        <img src={leaflet_logo} alt="Leaflet" />
                    </a>
                    <a href="https://plotly.com/javascript/">
                        <img src={plotly_logo} alt="Plotly" />
                    </a>
                    <a href="https://ark-ui.com/">
                        <img src={ark_logo} alt="Ark UI" />
                    </a>
                    <a href="https://tanstack.com/table/">
                        <img src={tan_logo} alt="TanStack Table" />
                    </a>
                </div>
            </DialogShell>
        </>
    );
};

export default AboutModal;

//  Copyright (C) 2022-2024 Theodore Chang
//
//  This program is free software: you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation, either version 3 of the License, or
//  (at your option) any later version.
//
//  This program is distributed in the hope that it will be useful,
//  but WITHOUT ANY WARRANTY; without even the implied warranty of
//  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//  GNU General Public License for more details.
//
//  You should have received a copy of the GNU General Public License
//  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import { Box, Button, Link, Modal, Stack, Typography } from "@suid/material";
import useTheme from "@suid/material/styles/useTheme";
import { createSignal } from "solid-js";
import mongodb_logo from "./assets/mongodb.svg";
import fastapi_logo from "./assets/fastapi.svg";
import beanie_logo from "./assets/beanie.svg";
import solid_logo from "./assets/solid.svg";
import tippy_logo from "./assets/tippy.svg";
import plotly_logo from "./assets/plotly.svg";
import leafllet_logo from "./assets/leaflet.svg";
import mb_logo from "./assets/logo.svg";
import mongoengine_logo from "./assets/mongoengine.png";
import celery_logo from "./assets/celery.png";
import scipy_logo from "./assets/scipy.svg";

export default function AboutModal() {
    const [open, setOpen] = createSignal(false);
    const theme = useTheme();

    const repo_link = <Link href="https://github.com/TLCFEM/motion-base">github.com/TLCFEM/motion-base</Link>;
    const nied_link = <Link href="https://www.kyoshin.bosai.go.jp/kyoshin/data/index_en.html">NIED</Link>;
    const nzsm_link = <Link href="https://www.geonet.org.nz/data/supplementary/nzsmdb">New Zealand Strong-Motion</Link>;

    return (
        <>
            <Button onClick={() => setOpen(true)} variant="contained">
                About
            </Button>
            <Modal
                open={open()}
                onClose={() => setOpen(false)}
                aria-labelledby="modal-modal-title"
                aria-describedby="modal-modal-description"
            >
                <Box
                    sx={{
                        position: "absolute",
                        top: "50%",
                        left: "50%",
                        transform: "translate(-50%, -50%)",
                        width: "60%",
                        bgcolor: theme.palette.background.paper,
                        border: "1px solid lightgrey",
                        borderRadius: "4px",
                        boxShadow: "24px",
                        p: 4,
                    }}
                >
                    <Stack direction="row" spacing={2} sx={{ p: 1 }} alignItems="center">
                        <img src={mb_logo} alt="logo" height="50px" />
                        <Typography variant="h4" sx={{ p: 1 }}>
                            Motion Base
                        </Typography>
                    </Stack>
                    <Typography variant="body1" sx={{ p: 1 }}>
                        This is a demo of the ground motion database.
                    </Typography>
                    <Typography variant="body1" sx={{ p: 1 }}>
                        The source code is available in this repository {repo_link}.
                    </Typography>
                    <Typography variant="h6" sx={{ p: 1 }}>
                        Japan Database
                    </Typography>
                    <Typography variant="body1" sx={{ p: 1 }}>
                        The data is retrieved from {nied_link}. The data is not processed. Users may want to further
                        filter the records.
                    </Typography>
                    <Typography variant="h6" sx={{ p: 1 }}>
                        New Zealand Database
                    </Typography>
                    <Typography variant="body1" sx={{ p: 1 }}>
                        The data is retrieved from {nzsm_link} database. Some selected strong motions are processed
                        (*.V2A files). The other records (*.V1A files) are not processed. Users may want to further
                        filter the records.
                    </Typography>
                    <Typography variant="h6" sx={{ p: 1 }}>
                        Built with
                    </Typography>
                    <Stack direction="row" spacing={3} sx={{ p: 1 }} alignItems="center" justifyContent="center">
                        <Link href="https://www.mongodb.com/">
                            <img src={mongodb_logo} alt="mongodb" height="40px" />
                        </Link>
                        <Link href="http://mongoengine.org/">
                            <img src={mongoengine_logo} alt="mongoengine" height="40px" />
                        </Link>
                        <Link href="https://beanie-odm.dev/">
                            <img src={beanie_logo} alt="beanie" height="40px" />
                        </Link>
                    </Stack>
                    <Stack direction="row" spacing={3} sx={{ p: 1 }} alignItems="center" justifyContent="center">
                        <Link href="https://fastapi.tiangolo.com/">
                            <img src={fastapi_logo} alt="fastapi" height="40px" />
                        </Link>
                        <Link href="https://docs.celeryq.dev/en/stable/">
                            <img src={celery_logo} alt="celery" height="40px" />
                        </Link>
                        <Link href="https://scipy.org/">
                            <img src={scipy_logo} alt="scipy" height="40px" />
                        </Link>
                    </Stack>
                    <Stack direction="row" spacing={3} sx={{ p: 1 }} alignItems="center" justifyContent="center">
                        <Link href="https://www.solidjs.com/">
                            <img src={solid_logo} alt="solid" height="40px" />
                        </Link>
                        <Link href="https://leafletjs.com/">
                            <img src={leafllet_logo} alt="leaflet" height="40px" />
                        </Link>
                        <Link href="https://plotly.com/javascript/">
                            <img src={plotly_logo} alt="plotly" height="40px" />
                        </Link>
                        <Link href="https://atomiks.github.io/tippyjs/">
                            <img src={tippy_logo} alt="tippy" height="40px" />
                        </Link>
                    </Stack>
                </Box>
            </Modal>
        </>
    );
}

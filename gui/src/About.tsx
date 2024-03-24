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

export default function AboutModal() {
    const [open, setOpen] = createSignal(false);
    const theme = useTheme();

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
                            About
                        </Typography>
                    </Stack>
                    <Typography variant="body1" sx={{ p: 1 }}>
                        This is a demo of the strong motion database. The source code is available at GitHub.
                    </Typography>
                    <Typography variant="h6" sx={{ p: 1 }}>
                        Japan Database
                    </Typography>
                    <Typography variant="body1" sx={{ p: 1 }}>
                        The data is retrieved from{" "}
                        <Link href="https://www.kyoshin.bosai.go.jp/kyoshin/data/index_en.html">NIED</Link>. The data is
                        not processed. Users may want to further filter the records.
                    </Typography>
                    <Typography variant="h6" sx={{ p: 1 }}>
                        New Zealand Database
                    </Typography>
                    <Typography variant="body1" sx={{ p: 1 }}>
                        The data is retrieved from{" "}
                        <Link href="https://www.geonet.org.nz/data/supplementary/nzsmdb">
                            New Zealand Strong-Motion
                        </Link>{" "}
                        database. The selected strong motions are processed (*.V2A files). The other records (*.V1A
                        files) are not processed. Users may want to further filter the records.
                    </Typography>
                    <Typography variant="h6" sx={{ p: 1 }}>
                        Built with
                    </Typography>
                    <Stack direction="row" spacing={3} sx={{ p: 1 }} alignItems="center" justifyContent="center">
                        <img src={mongodb_logo} alt="mongodb" height="40px" />
                        <img src={fastapi_logo} alt="fastapi" height="40px" />
                        <img src={solid_logo} alt="solid" height="40px" />
                    </Stack>
                    <Stack direction="row" spacing={3} sx={{ p: 1 }} alignItems="center" justifyContent="center">
                        <img src={beanie_logo} alt="beanie" height="40px" />
                        <img src={leafllet_logo} alt="leaflet" height="40px" />
                        <img src={plotly_logo} alt="plotly" height="40px" />
                        <img src={tippy_logo} alt="tippy" height="40px" />
                    </Stack>
                </Box>
            </Modal>
        </>
    );
}

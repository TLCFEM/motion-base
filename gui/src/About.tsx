import { Box, Button, Link, Modal, Stack, Typography } from "@suid/material";
import useTheme from "@suid/material/styles/useTheme";
import { createSignal } from "solid-js";
import mongodb from "./assets/mongodb.svg";
import fastapi from "./assets/fastapi.svg";
import beanie from "./assets/beanie.svg";
import solid from "./assets/solid.svg";
import tippylogo from "./assets/tippy.svg";
import plotlylogo from "./assets/plotly.svg";
import leaflletlogo from "./assets/leaflet.svg";
import logo from "./assets/logo.svg";

export default function AboutModal() {
    const [open, setOpen] = createSignal(false);
    const theme = useTheme();

    return <>
        <Button onClick={() => setOpen(true)} color="inherit">About</Button>
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
                    p: 4
                }}
            >
                <Stack direction="row" spacing={2} sx={{ p: 1 }} alignItems="center">
                    <img src={logo} alt="logo" height="50px" />
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
                    The data is retrieved from <Link
                    href="https://www.kyoshin.bosai.go.jp/kyoshin/data/index_en.html">NIED</Link>. The data is not
                    processed. Users may want to further filter the records.
                </Typography>
                <Typography variant="h6" sx={{ p: 1 }}>
                    New Zealand Database
                </Typography>
                <Typography variant="body1" sx={{ p: 1 }}>
                    The data is retrieved from <Link
                    href="https://www.geonet.org.nz/data/supplementary/nzsmdb">New Zealand
                    Strong-Motion</Link> database. The selected strong motions are processed (*.V2A files). The other
                    records (*.V1A files) are not processed. Users may want to further filter the records.
                </Typography>
                <Typography variant="h6" sx={{ p: 1 }}>
                    Built with
                </Typography>
                <Stack direction="row" spacing={3} sx={{ p: 1 }} alignItems="center" justifyContent="center">
                    <img src={mongodb} alt="mongodb" height="40px" />
                    <img src={fastapi} alt="fastapi" height="40px" />
                    <img src={solid} alt="solid" height="40px" />
                </Stack>
                <Stack direction="row" spacing={3} sx={{ p: 1 }} alignItems="center" justifyContent="center">
                    <img src={beanie} alt="beanie" height="40px" />
                    <img src={leaflletlogo} alt="leaflet" height="40px" />
                    <img src={plotlylogo} alt="plotly" height="40px" />
                    <img src={tippylogo} alt="tippy" height="40px" />
                </Stack>
            </Box>
        </Modal>
    </>;
}

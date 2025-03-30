//  Copyright (C) 2022-2025 Theodore Chang
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

import { Box, Button, LinearProgress, Modal, Paper, Stack, TextField } from "@suid/material";
import useTheme from "@suid/material/styles/useTheme";
import { Component, createEffect, createSignal, onMount } from "solid-js";
import axios from "axios";
import { AggregationItem, get_stats } from "./API";
import Plotly from "plotly.js-basic-dist-min";

interface HistogramProps {
    id: string;
    item: string;
    data: AggregationItem[];
}

const Histogram: Component<HistogramProps> = (props) => {
    createEffect(async () => {
        await Plotly.newPlot(
            props.id,
            [
                {
                    x: props.data.map(item => item.key),
                    y: props.data.map(item => item.doc_count),
                    type: "bar"
                }
            ],
            {
                title: { text: props.item + " Histogram" },
                xaxis: {
                    title: { text: props.item },
                    autorange: true,
                    automargin: true
                },
                yaxis: {
                    title: { text: "Counts" },
                    autorange: true,
                    automargin: true
                },
                width: 450,
                height: 400
            },
            { autosizable: true, responsive: true }
        );
    });

    return <Paper id={props.id} sx={{ width: 450, height: 400 }} />;
};

export default function ServerModal() {
    const [open, setOpen] = createSignal(false);
    const [newServer, setNewServer] = createSignal(axios.defaults.baseURL);
    const [loading, setLoading] = createSignal(false);
    const theme = useTheme();
    const [magnitudeHist, setMagnitudeHist] = createSignal([] as AggregationItem[]);
    const [pgaHist, setPgaHist] = createSignal([] as AggregationItem[]);

    onMount(async () => {
        const allStats = await get_stats();
        setMagnitudeHist(allStats.magnitude.buckets);
        setPgaHist(allStats.pga.buckets);
    });

    return (
        <>
            <Button size="small" onClick={() => setOpen(true)} variant="contained">
                Change Server
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
                        // width: "60ch",
                        bgcolor: theme.palette.background.paper,
                        border: "1px solid lightgrey",
                        borderRadius: "4px",
                        boxShadow: "24px"
                    }}
                >
                    <Stack direction="row" spacing={2} sx={{ p: 1 }} alignItems="center" justifyContent="center">
                        <TextField
                            size="small"
                            id="server-id"
                            sx={{ minWidth: "36ch" }}
                            label="Server"
                            value={newServer()}
                            onChange={(_, value) => setNewServer(value)}
                        />
                        <Button variant="contained" size="small" onClick={async () => {
                            setLoading(true);
                            try {
                                await axios.get(`${newServer()}/alive`);
                                axios.defaults.baseURL = newServer();
                                setOpen(false);
                            } catch {
                                alert("Target server is not reachable.");
                            }
                            setLoading(false);
                        }} disabled={loading()} id="btn-change">Change</Button>
                        <Button variant="contained" size="small" onClick={() => setOpen(false)} disabled={loading()}
                            id="btn-cancel">
                            Cancel
                        </Button>
                    </Stack>
                    {loading() ? <LinearProgress /> : <LinearProgress variant="determinate" value={0} />}
                    <Stack direction="row" spacing={1} sx={{ p: 1 }} alignItems="center" justifyContent="center">
                        <Histogram id="magnitude-hist" item="Magnitude" data={magnitudeHist()} />
                        <Histogram id="pga-hist" item="PGA" data={pgaHist()} />
                    </Stack>
                </Box>
            </Modal>
        </>
    );
}

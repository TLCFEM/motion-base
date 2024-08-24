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

import { Box, Button, CircularProgress, LinearProgress, Modal, Stack, TextField } from "@suid/material";
import useTheme from "@suid/material/styles/useTheme";
import { createSignal } from "solid-js";
import axios from "axios";

export default function ServerModal() {
    const [open, setOpen] = createSignal(false);
    const [newServer, setNewServer] = createSignal(axios.defaults.baseURL);
    const [loading, setLoading] = createSignal(false);
    const theme = useTheme();

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
                        width: "60ch",
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
                </Box>
            </Modal>
        </>
    );
}

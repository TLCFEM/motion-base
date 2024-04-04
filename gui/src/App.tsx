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

import { Component, createResource, createSignal, Match, onMount, Switch } from "solid-js";
import { AppBar, Box, Button, Stack, Toolbar, Typography } from "@suid/material";
import AboutModal from "./About";
import Jackpot from "./Jackpot";
import QueryDatabase from "./Query";
import tippy from "tippy.js";
import "tippy.js/dist/tippy.css";
import "tippy.js/animations/scale.css";
import { total_api } from "./API";
import Process from "./Process";

const [mode, setMode] = createSignal<"jackpot" | "query" | "process">("jackpot");
const [total] = createResource<number>(total_api);

const App: Component = () => {
    onMount(() => {
        tippy(`#btn-jackpot`, {
            content: "Get a random record from the database.",
            animation: "scale",
            theme: "translucent",
        });
        tippy(`#btn-query`, {
            content: "Query the database according to certain criteria.",
            animation: "scale",
            theme: "translucent",
        });
        tippy(`#btn-process`, {
            content: "Apply further processing to records.",
            animation: "scale",
            theme: "translucent",
        });
    });

    const variant = screen.height <= 1080 ? "dense" : "regular";

    return (
        <Stack>
            <AppBar position="static" enableColorOnDark>
                <Toolbar
                    variant={variant}
                    sx={{
                        display: "flex",
                        alignItems: "center",
                        alignContent: "center",
                        gap: "1rem",
                    }}
                >
                    <Typography sx={{ flexGrow: 1 }} variant="h5">
                        {total.loading ? "..." : `Record Count: ${total().toLocaleString()}.`}
                    </Typography>
                    <Button size="small" id="btn-jackpot" onClick={() => setMode("jackpot")} variant="contained">
                        Jackpot
                    </Button>
                    <Button size="small" id="btn-query" onClick={() => setMode("query")} variant="contained">
                        Query
                    </Button>
                    <Button size="small" id="btn-process" onClick={() => setMode("process")} variant="contained">
                        Process
                    </Button>
                    <AboutModal />
                </Toolbar>
            </AppBar>
            <Box sx={{ display: "flex", gap: "1rem", alignItems: "stretch", padding: "1rem" }}>
                <Switch>
                    <Match when={mode() === "jackpot"}>
                        <Jackpot sx={{ border: "1px solid darkgrey", height: "90vh" }} />
                    </Match>
                    <Match when={mode() === "query"}>
                        <QueryDatabase />
                    </Match>
                    <Match when={mode() === "process"}>
                        <Process sx={{ border: "1px solid darkgrey" }} />
                    </Match>
                </Switch>
            </Box>
        </Stack>
    );
};

export default App;

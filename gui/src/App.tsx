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

import {
    Component,
    createResource,
    createSignal,
    Match,
    onMount,
    Switch,
} from "solid-js";
import { AppBar, Box, Button, Grid, Toolbar, Typography } from "@suid/material";
import AboutModal from "./About";
import Jackpot from "./Jackpot";
import QueryDatabase from "./Query";
import tippy from "tippy.js";
import "tippy.js/dist/tippy.css";
import "tippy.js/animations/scale.css";
import { total_api } from "./API";

const [mode, setMode] = createSignal<"jackpot" | "query">("jackpot");
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
    });

    return (
        <Box sx={{ marginLeft: "1vw", marginRight: "1vw", marginTop: "1vh" }}>
            <Grid container spacing={1}>
                <Grid item xs={12} md={12}>
                    <AppBar position="static" enableColorOnDark>
                        <Toolbar
                            // variant="dense"
                            sx={{
                                display: "flex",
                                alignItems: "center",
                                alignContent: "center",
                                gap: "1rem",
                            }}
                        >
                            <Typography sx={{ flexGrow: 1 }} variant="h5">
                                {total.loading
                                    ? "..."
                                    : `Record Count: ${total().toLocaleString()}.`}
                            </Typography>
                            <Button
                                id="btn-jackpot"
                                onClick={() => setMode("jackpot")}
                                variant="contained"
                            >
                                Jackpot
                            </Button>
                            <Button
                                id="btn-query"
                                onClick={() => setMode("query")}
                                variant="contained"
                            >
                                Query
                            </Button>
                            <AboutModal />
                        </Toolbar>
                    </AppBar>
                </Grid>
                <Switch>
                    <Match when={mode() === "jackpot"}>
                        <Jackpot />
                    </Match>
                    <Match when={mode() === "query"}>
                        <QueryDatabase />
                    </Match>
                </Switch>
            </Grid>
        </Box>
    );
};

export default App;

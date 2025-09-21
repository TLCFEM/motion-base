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

import {Component, createResource, createSignal, Match, onMount, Switch} from "solid-js";
import {AppBar, Box, Button, Stack, Toolbar, Typography} from "@suid/material";
import AboutModal from "./About";
import Jackpot from "./Jackpot";
import QueryDatabase from "./Query";
import tippy from "tippy.js";
import "tippy.js/dist/tippy.css";
import "tippy.js/animations/scale.css";
import {get_total_api} from "./API";
import Process from "./Process";
import ServerModal from "./Server";
import {marked} from "marked";
import hljs from "highlight.js";

const [mode, setMode] = createSignal<"jackpot" | "query" | "process" | "scripting" | "brief">("brief");
const [total] = createResource<number>(get_total_api);

const MarkdownContent = (props: { src: string }) => {
    const [content, setContent] = createSignal<string>("");

    onMount(async () => {
        const response = await fetch(`/src/assets/${props.src}`);

        setContent(
            await marked
                .use({async: true})
                .parse((await response.text()).replace(/\(client_files\//g, "(/src/assets/client_files/")),
        );

        hljs.highlightAll();
    });

    return <div style={{margin: "auto", "max-width": "800pt"}} innerHTML={content()}/>;
};

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
        tippy(`#btn-scripting`, {
            content: "Guides to programmatic usage.",
            animation: "scale",
            theme: "translucent",
        });
    });

    const variant = screen.height <= 1080 ? "dense" : "regular";

    return (
        <Stack>
            <AppBar position="sticky" enableColorOnDark>
                <Toolbar
                    variant={variant}
                    sx={{
                        display: "flex",
                        alignItems: "center",
                        alignContent: "center",
                        gap: "1rem",
                        height: "4rem",
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
                    <Button size="small" id="btn-scripting" onClick={() => setMode("scripting")} variant="contained">
                        Scripting
                    </Button>
                    <AboutModal />
                    <ServerModal />
                </Toolbar>
            </AppBar>
            <Box sx={{ display: "flex", gap: "1rem", alignItems: "stretch", padding: "1rem" }}>
                <Switch>
                    <Match when={mode() === "jackpot"}>
                        <Jackpot sx={{ border: "1px solid darkgrey", height: "calc(100vh - 7rem)" }} />
                    </Match>
                    <Match when={mode() === "query"}>
                        <QueryDatabase />
                    </Match>
                    <Match when={mode() === "process"}>
                        <Process sx={{ border: "1px solid darkgrey" }} />
                    </Match>
                    <Match when={mode() === "scripting"}>
                        <MarkdownContent src="client.md" />
                    </Match>
                    <Match when={mode() === "brief"}>
                        <MarkdownContent src="brief.md" />
                    </Match>
                </Switch>
            </Box>
        </Stack>
    );
};

export default App;

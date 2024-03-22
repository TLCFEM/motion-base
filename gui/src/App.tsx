import { Component, createSignal, Match, onMount, Switch } from "solid-js";
import { AppBar, Box, Button, Grid, Toolbar } from "@suid/material";
import AboutModal from "./About";
import Jackpot from "./Jackpot";
import QueryDatabase from "./Query";
import tippy from "tippy.js";
import "tippy.js/dist/tippy.css";
import "tippy.js/animations/scale.css";

const [mode, setMode] = createSignal<"jackpot" | "query">("jackpot");

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
                            variant="dense"
                            sx={{
                                display: "flex",
                                flexDirection: "row",
                                justifyContent: "flex-end",
                                alignContent: "center",
                                gap: "1rem",
                            }}
                        >
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

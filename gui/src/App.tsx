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

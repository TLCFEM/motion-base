import { Component, createSignal, Match, Switch } from "solid-js";
import { AppBar, Box, Button, Grid, Toolbar } from "@suid/material";
import AboutModal from "./About";
import Jackpot from "./Jackpot";
import Overview from "./Query";

const [mode, setMode] = createSignal<"jackpot" | "query">("jackpot");

const App: Component = () => {
    return (
        <Box sx={{ marginLeft: "1vw", marginRight: "1vw", marginTop: "1vh" }}>
            <Grid container spacing={1}>
                <Grid item xs={12} md={12}>
                    <AppBar position="static">
                        <Toolbar
                            variant="dense"
                            sx={{ justifyContent: "flex-end" }}
                        >
                            <Button
                                onClick={() => setMode("jackpot")}
                                color="inherit"
                            >
                                Jackpot
                            </Button>
                            <Button
                                onClick={() => setMode("query")}
                                color="inherit"
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
                        <Overview />
                    </Match>
                </Switch>
            </Grid>
        </Box>
    );
};

export default App;

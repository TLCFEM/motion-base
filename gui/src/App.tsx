import { Component } from "solid-js";
import { AppBar, Box, Grid, Toolbar } from "@suid/material";
import AboutModal from "./About";
import Jackpot from "./Jackpot";

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
                            <AboutModal />
                        </Toolbar>
                    </AppBar>
                </Grid>
                <Jackpot />
            </Grid>
        </Box>
    );
};

export default App;

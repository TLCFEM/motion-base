import { Component, createSignal, onMount } from "solid-js";
import tippy from "tippy.js";
import {
    Alert,
    AlertTitle,
    Box,
    Button,
    ButtonGroup,
    Card,
    CardContent,
    Grid,
    LinearProgress,
    Modal,
    TextField,
} from "@suid/material";

const [error, setError] = createSignal("");

const Settings: Component = () => {
    const [loading, setLoading] = createSignal<boolean>(false);

    const [currentRecord, setCurrentRecord] = createSignal("abf60c4d-ae35-4ec0-b63a-38362891cea7");

    async function process() {
        setLoading(true);

        setLoading(false);
    }

    function clear() {}

    onMount(() => {
        tippy(`#btn-process`, {
            content: "Process the record with the current settings.",
            animation: "scale",
        });
        tippy(`#btn-reset`, {
            content: "Clear the current settings.",
            animation: "scale",
        });
    });

    return (
        <Card>
            <CardContent
                sx={{
                    display: "flex",
                    flexDirection: "row",
                    justifyContent: "center",
                    alignContent: "center",
                    gap: "1rem",
                }}
            >
                <TextField
                    label="ID"
                    value={currentRecord()}
                    defaultValue={currentRecord()}
                    InputProps={{ readOnly: true }}
                    sx={{ width: "34ch" }}
                />
                <ButtonGroup variant="outlined">
                    <Button onClick={process} id="btn-process" disabled={loading()}>
                        Process
                    </Button>
                    <Button onClick={clear} id="btn-reset" disabled={loading()}>
                        Reset
                    </Button>
                </ButtonGroup>
                <Modal open={error() !== ""} onClose={() => setError("")}>
                    <Alert
                        severity="error"
                        sx={{
                            position: "absolute",
                            top: "50%",
                            left: "50%",
                            transform: "translate(-50%, -50%)",
                            width: "40%",
                        }}
                    >
                        <AlertTitle>Error</AlertTitle>
                        {error()}
                    </Alert>
                </Modal>
            </CardContent>
            <Box sx={{ width: "100%" }}>
                {loading() ? <LinearProgress /> : <LinearProgress variant="determinate" value={0} />}
            </Box>
        </Card>
    );
};

export default function Process() {
    return (
        <>
            <Grid item xs={12} md={12}>
                <Settings />
            </Grid>
        </>
    );
}

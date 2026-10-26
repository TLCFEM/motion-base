//  Copyright (C) 2022-2026 Theodore Chang
//
//  This program is free software: you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation, either version 3 of the License, or
//  (at your option) any later version.

import { Component, createEffect, createResource, createSignal, onCleanup } from "solid-js";
import Plotly from "plotly.js-basic-dist-min";
import { AggregationItem, errorMessage, get_stats, getBaseUrl, http, setBaseUrl } from "./api";
import { plotAxis, plotConfig, plotLayout } from "./plot";
import { DialogShell, TextField } from "./ui";

const Histogram: Component<{ id: string; title: string; data: AggregationItem[]; scale: Plotly.AxisType }> = (props) => {
    createEffect(async () => {
        await Plotly.newPlot(
            props.id,
            [
                {
                    x: props.data.map((item) => (item.key_as_string ? item.key_as_string.slice(0, 4) : item.key)),
                    y: props.data.map((item) => item.doc_count),
                    type: "bar",
                    marker: { color: "#0d9488", line: { width: 0 } },
                    opacity: 0.88,
                },
            ],
            plotLayout(`${props.title} Histogram`, {
                xaxis: plotAxis(props.title),
                yaxis: plotAxis("Counts", { type: props.scale }),
                bargap: 0.12,
            }),
            { ...plotConfig, displayModeBar: false },
        );
    });

    onCleanup(() => Plotly.purge(props.id));

    return <div id={props.id} class="histogram" />;
};

const ServerModal: Component<{ onConnected: () => void }> = (props) => {
    const [open, setOpen] = createSignal(false);
    const [server, setServer] = createSignal(getBaseUrl());
    const [checking, setChecking] = createSignal(false);
    const [error, setError] = createSignal("");

    const [stats] = createResource(open, (isOpen) => (isOpen ? get_stats() : Promise.resolve(null)));

    function show() {
        setServer(getBaseUrl());
        setError("");
        setOpen(true);
    }

    async function change() {
        const target = server().trim().replace(/\/+$/, "");
        if (!target) {
            setError("Enter a server URL.");
            return;
        }

        setChecking(true);
        setError("");
        try {
            await http.get(`${target}/alive`, { timeout: 5000 });
            setBaseUrl(target);
            props.onConnected();
            setOpen(false);
        } catch (err) {
            setError(errorMessage(err) || "Target server is not reachable.");
        } finally {
            setChecking(false);
        }
    }

    return (
        <>
            <button class="btn secondary" onClick={show}>
                Change Server
            </button>
            <DialogShell open={open()} onOpenChange={setOpen} title="Server" size="xl">
                <div class="server-form">
                    <TextField
                        id="server-id"
                        label="Server"
                        value={server()}
                        onValueChange={setServer}
                        title="Base URL of the Motion Base API"
                    />
                    <button
                        class="btn"
                        classList={{ loading: checking() }}
                        onClick={change}
                        disabled={checking()}
                        id="btn-change"
                        aria-busy={checking()}
                    >
                        Change
                    </button>
                    <button class="btn secondary" onClick={() => setOpen(false)} disabled={checking()} id="btn-cancel">
                        Cancel
                    </button>
                </div>
                {error() && <p class="error-text">{error()}</p>}

                <div class="histograms">
                    <Histogram id="year-hist" title="Year" data={stats()?.year.buckets ?? []} scale="log" />
                    <Histogram id="magnitude-hist" title="Magnitude" data={stats()?.magnitude.buckets ?? []} scale="linear" />
                    <Histogram id="pga-hist" title="PGA" data={stats()?.pga.buckets ?? []} scale="log" />
                </div>
            </DialogShell>
        </>
    );
};

export default ServerModal;

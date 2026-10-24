//  Copyright (C) 2022-2026 Theodore Chang
//
//  This program is free software: you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation, either version 3 of the License, or
//  (at your option) any later version.

import Plotly from "plotly.js-basic-dist-min";
import { theme } from "./theme";

type Axis = NonNullable<Plotly.Layout["xaxis"]>;

export const plotConfig: Partial<Plotly.Config> = {
    autosizable: true,
    responsive: true,
    displaylogo: false,
    modeBarButtonsToRemove: ["lasso2d"],
};

const palette = () => {
    const dark = theme() === "dark";

    return {
        text: dark ? "#e6edf6" : "#0f172a",
        textSoft: dark ? "#c3cfdd" : "#475569",
        muted: dark ? "#8a9bb0" : "#64748b",
        grid: dark ? "rgba(148, 163, 184, 0.16)" : "rgba(148, 163, 184, 0.2)",
        zero: dark ? "rgba(148, 163, 184, 0.28)" : "rgba(148, 163, 184, 0.35)",
        line: dark ? "rgba(148, 163, 184, 0.24)" : "rgba(148, 163, 184, 0.3)",
        hoverBg: dark ? "#e6edf6" : "#0f172a",
        hoverText: dark ? "#0b1220" : "#f8fafc",
        colorway: dark ? ["#2dd4bf", "#38bdf8", "#818cf8", "#fbbf24", "#f472b6"] : ["#0d9488", "#0ea5e9", "#6366f1", "#f59e0b", "#ec4899"],
    };
};

export const plotAxis = (title: string, extra: Partial<Axis> = {}): Partial<Axis> => {
    const colors = palette();

    return {
        title: { text: title, font: { size: 11, color: colors.muted } },
        automargin: true,
        gridcolor: colors.grid,
        zerolinecolor: colors.zero,
        linecolor: colors.line,
        tickfont: { size: 11, color: colors.muted },
        ...extra,
    };
};

export const plotLayout = (title: string, extra: Partial<Plotly.Layout> = {}): Partial<Plotly.Layout> => {
    const colors = palette();

    return {
        title: { text: title, x: 0.012, xanchor: "left", font: { size: 13, color: colors.text } },
        autosize: true,
        paper_bgcolor: "rgba(0, 0, 0, 0)",
        plot_bgcolor: "rgba(0, 0, 0, 0)",
        font: { family: 'Inter, "Segoe UI", system-ui, sans-serif', size: 12, color: colors.textSoft },
        margin: { l: 58, r: 22, t: 46, b: 50 },
        colorway: colors.colorway,
        hoverlabel: {
            bgcolor: colors.hoverBg,
            bordercolor: colors.hoverBg,
            font: { color: colors.hoverText, size: 11 },
        },
        legend: { font: { size: 11, color: colors.muted } },
        ...extra,
    };
};

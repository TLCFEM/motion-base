//  Copyright (C) 2022-2026 Theodore Chang
//
//  This program is free software: you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation, either version 3 of the License, or
//  (at your option) any later version.

/* @refresh reload */
import { render } from "solid-js/web";
import "highlight.js/styles/monokai.css";
import "./index.css";
import App from "./App";

const root = document.getElementById("root");

if (!(root instanceof HTMLElement)) {
    throw new Error("Root element not found.");
}

render(() => <App />, root);

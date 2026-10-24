//  Copyright (C) 2022-2026 Theodore Chang
//
//  This program is free software: you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation, either version 3 of the License, or
//  (at your option) any later version.

import { Switch as ThemeSwitch } from "@ark-ui/solid/switch";
import { Tabs } from "@ark-ui/solid/tabs";
import { marked } from "marked";
import hljs from "highlight.js/lib/common";
import { Component, createEffect, createResource, createSignal, Match, onCleanup, onMount, Switch } from "solid-js";
import AboutModal from "./About";
import { check_backend, get_total_api } from "./api";
import Jackpot from "./Jackpot";
import Process from "./Process";
import QueryDatabase from "./Query";
import ServerModal from "./Server";
import { applyTheme, setTheme, theme, watchSystemTheme } from "./theme";

type Mode = "brief" | "scripting" | "jackpot" | "query" | "process";

const MarkdownContent: Component<{ src: string }> = (props) => {
    const [content] = createResource(
        () => props.src,
        async (src) => {
            const response = await fetch(`./${src}`);
            const text = (await response.text()).replace(/\(client_files\//g, "(./client_files/");
            return marked.parse(text) as string;
        },
    );

    let container: HTMLDivElement | undefined;

    createEffect(() => {
        if (content() && container) {
            container.querySelectorAll("pre code").forEach((element) => hljs.highlightElement(element as HTMLElement));
        }
    });

    return <div ref={container} class="markdown" innerHTML={content() ?? ""} />;
};

const App: Component = () => {
    const [mode, setMode] = createSignal<Mode>("brief");
    const [online, { mutate: setOnline }] = createResource(() => check_backend());
    const [total] = createResource(
        () => online() === true,
        (isOnline) => (isOnline ? get_total_api() : Promise.resolve(0)),
    );

    createEffect(() => applyTheme(theme()));

    onMount(() => {
        const stopWatching = watchSystemTheme();
        onCleanup(stopWatching);
    });

    const subtitle = () => {
        if (!online()) return "Server unavailable";
        if (total.loading) return "Loading records…";
        const count = total();
        return count === undefined ? "Motion Base" : `${count.toLocaleString()} records`;
    };

    return (
        <Tabs.Root value={mode()} onValueChange={(details) => details.value && setMode(details.value as Mode)}>
            <header class="app-header">
                <div class="brand">
                    <strong>Motion Base</strong>
                    <span classList={{ online: online() === true, offline: online() === false }}>{subtitle()}</span>
                </div>
                <Tabs.List class="nav" aria-label="Application sections">
                    <Tabs.Trigger value="brief" class="tab" title="Project overview">
                        Overview
                    </Tabs.Trigger>
                    <Tabs.Trigger value="scripting" class="tab" title="Guides to programmatic usage">
                        Scripting
                    </Tabs.Trigger>
                    <Tabs.Trigger value="jackpot" class="tab" disabled={!online()} title="Get a random record from the database">
                        Jackpot
                    </Tabs.Trigger>
                    <Tabs.Trigger value="query" class="tab" disabled={!online()} title="Query the database according to certain criteria">
                        Query
                    </Tabs.Trigger>
                    <Tabs.Trigger value="process" class="tab" disabled={!online()} title="Apply further processing to records">
                        Process
                    </Tabs.Trigger>
                </Tabs.List>
                <div class="header-actions">
                    <ThemeSwitch.Root
                        class="theme-switch"
                        checked={theme() === "dark"}
                        onCheckedChange={(details) => setTheme(details.checked ? "dark" : "light")}
                        title="Toggle dark theme"
                    >
                        <ThemeSwitch.Control class="theme-switch-control">
                            <ThemeSwitch.Thumb class="theme-switch-thumb" aria-hidden="true">
                                {theme() === "dark" ? "☾" : "☀"}
                            </ThemeSwitch.Thumb>
                        </ThemeSwitch.Control>
                        <ThemeSwitch.Label class="theme-switch-label">Dark</ThemeSwitch.Label>
                        <ThemeSwitch.HiddenInput aria-label="Dark theme" />
                    </ThemeSwitch.Root>
                    <AboutModal online={online() === true} />
                    <ServerModal onConnected={() => setOnline(true)} />
                </div>
            </header>

            <main class="page" classList={{ fixed: mode() === "query" }}>
                <Switch>
                    <Match when={mode() === "jackpot"}>
                        <Jackpot />
                    </Match>
                    <Match when={mode() === "query"}>
                        <QueryDatabase />
                    </Match>
                    <Match when={mode() === "process"}>
                        <Process />
                    </Match>
                    <Match when={mode() === "scripting"}>
                        <MarkdownContent src="client.md" />
                    </Match>
                    <Match when={mode() === "brief"}>
                        <MarkdownContent src="brief.md" />
                    </Match>
                </Switch>
            </main>
        </Tabs.Root>
    );
};

export default App;

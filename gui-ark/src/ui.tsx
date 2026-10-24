//  Copyright (C) 2022-2026 Theodore Chang
//
//  This program is free software: you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation, either version 3 of the License, or
//  (at your option) any later version.

import { Checkbox } from "@ark-ui/solid/checkbox";
import { Dialog } from "@ark-ui/solid/dialog";
import { Field } from "@ark-ui/solid/field";
import { Select, createListCollection } from "@ark-ui/solid/select";
import { For, JSX } from "solid-js";
import { Portal } from "solid-js/web";

export interface TextFieldProps {
    id?: string;
    label: string;
    value: string;
    onValueChange: (value: string) => void;
    type?: "text" | "number" | "date";
    disabled?: boolean;
    invalid?: boolean;
    title?: string;
    placeholder?: string;
    min?: number | string;
    max?: number | string;
    step?: number | string;
    class?: string;
}

export function TextField(props: TextFieldProps) {
    return (
        <Field.Root class={`field ${props.class ?? ""}`} invalid={props.invalid} disabled={props.disabled} title={props.title}>
            <Field.Label class="field-label">{props.label}</Field.Label>
            <Field.Input
                id={props.id}
                class="input"
                type={props.type ?? "text"}
                value={props.value}
                placeholder={props.placeholder}
                min={props.min}
                max={props.max}
                step={props.step}
                onInput={(event) => props.onValueChange(event.currentTarget.value)}
            />
        </Field.Root>
    );
}

export interface CheckboxFieldProps {
    id?: string;
    name?: string;
    label: string;
    checked: boolean;
    onCheckedChange: (checked: boolean) => void;
    disabled?: boolean;
    title?: string;
}

export function CheckboxField(props: CheckboxFieldProps) {
    return (
        <Checkbox.Root
            id={props.id}
            name={props.name}
            class="check"
            checked={props.checked}
            disabled={props.disabled}
            title={props.title}
            onCheckedChange={(details) => props.onCheckedChange(details.checked === true)}
        >
            <Checkbox.Control class="check-control">
                <Checkbox.Indicator class="check-indicator">✓</Checkbox.Indicator>
            </Checkbox.Control>
            <Checkbox.Label class="check-label">{props.label}</Checkbox.Label>
            <Checkbox.HiddenInput />
        </Checkbox.Root>
    );
}

export interface Option {
    label: string;
    value: string;
}

export interface SelectFieldProps {
    id?: string;
    label: string;
    value: string;
    options: Option[];
    onValueChange: (value: string) => void;
    disabled?: boolean;
    title?: string;
    class?: string;
}

export function SelectField(props: SelectFieldProps) {
    const collection = createListCollection<Option>({ items: props.options });

    return (
        <Select.Root
            id={props.id}
            class={`field ${props.class ?? ""}`}
            collection={collection}
            value={[props.value]}
            disabled={props.disabled}
            title={props.title}
            onValueChange={(details) => props.onValueChange(details.value[0] ?? "")}
        >
            <Select.Label class="field-label">{props.label}</Select.Label>
            <Select.Control class="select-control">
                <Select.Trigger class="input select-trigger">
                    <Select.ValueText placeholder="Select" />
                </Select.Trigger>
                <Select.Indicator class="select-chevron">▾</Select.Indicator>
            </Select.Control>
            <Select.Positioner>
                <Select.Content class="select-content">
                    <For each={props.options}>
                        {(option) => (
                            <Select.Item item={option} class="select-item">
                                <Select.ItemText>{option.label}</Select.ItemText>
                                <Select.ItemIndicator class="select-item-check">✓</Select.ItemIndicator>
                            </Select.Item>
                        )}
                    </For>
                </Select.Content>
            </Select.Positioner>
            <Select.HiddenSelect />
        </Select.Root>
    );
}

export interface DialogShellProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    title: string;
    children: JSX.Element;
    size?: "sm" | "md" | "lg" | "xl";
}

export function DialogShell(props: DialogShellProps) {
    return (
        <Dialog.Root open={props.open} onOpenChange={(details) => props.onOpenChange(details.open)} lazyMount unmountOnExit>
            <Portal>
                <Dialog.Backdrop class="modal-backdrop" />
                <Dialog.Positioner class="modal-positioner">
                    <Dialog.Content class={`modal modal-${props.size ?? "md"}`}>
                        <header class="modal-head">
                            <Dialog.Title class="modal-title">{props.title}</Dialog.Title>
                            <Dialog.CloseTrigger class="icon-btn" aria-label="Close" title="Close">
                                ×
                            </Dialog.CloseTrigger>
                        </header>
                        <div class="modal-body">{props.children}</div>
                    </Dialog.Content>
                </Dialog.Positioner>
            </Portal>
        </Dialog.Root>
    );
}

export function ErrorDialog(props: { open: boolean; message: string; onClose: () => void }) {
    return (
        <DialogShell open={props.open} onOpenChange={(open) => !open && props.onClose()} title="Error" size="sm">
            <p class="error-text">{props.message || "Unknown error"}</p>
            <div class="row end">
                <button class="btn" onClick={props.onClose}>
                    Dismiss
                </button>
            </div>
        </DialogShell>
    );
}


// src/components/Input.jsx
import React from "react";
const Input = ({
    label,
    value,
    onChange,
    type = "text",
    placeholder,
    name,
    id,
    disabled = false,
    required = false,
    error = "",
    helpText = "",
    className = "",
    inputClassName = "",
    ...props
}) => {
    const inputId = id || name || `in-${Math.random().toString(36).slice(2)}`;
    const describedBy = [
        error ? `${inputId}-error` : null,
        helpText ? `${inputId}-help` : null,
    ].filter(Boolean).join(" ") || undefined;

    return (
        <div className={`mb-4 ${className}`}>
            {label ? (
                <label
                    htmlFor={inputId}
                    className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                >
                    {label} {required ? <span className="text-red-500">*</span> : null}
                </label>
            ) : null}

            <input
                id={inputId}
                name={name}
                type={type}
                value={value}
                onChange={onChange}
                placeholder={placeholder}
                disabled={disabled}
                aria-invalid={!!error}
                aria-describedby={describedBy}
                className={[
                    "mt-1 p-2 w-full rounded border text-sm outline-none",
                    "bg-white dark:bg-gray-800 dark:text-white",
                    error
                        ? "border-red-500 ring-1 ring-red-300"
                        : "border-gray-300 dark:border-gray-600 focus:ring-2 focus:ring-indigo-300",
                    inputClassName,
                ].join(" ")}
                {...props}
            />

            {error ? (
                <p id={`${inputId}-error`} className="mt-1 text-xs text-red-600">
                    {error}
                </p>
            ) : helpText ? (
                <p id={`${inputId}-help`} className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    {helpText}
                </p>
            ) : null}
        </div>
    );
};

export default Input;
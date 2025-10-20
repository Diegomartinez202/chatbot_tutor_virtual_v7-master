import React from "react";

const Textarea = ({
    label,
    value,
    onChange,
    rows = 3,
    placeholder = "",
    name,
    id,
    disabled = false,
    required = false,
    error = "",
    helpText = "",
    className = "",
    textareaClassName = "",
    ...props
}) => {
    const taId = id || name || `ta-${Math.random().toString(36).slice(2)}`;
    const describedBy = [
        error ? `${taId}-error` : null,
        helpText ? `${taId}-help` : null,
    ].filter(Boolean).join(" ") || undefined;

    return (
        <div className={`mb-4 ${className}`}>
            {label ? (
                <label
                    htmlFor={taId}
                    className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                >
                    {label} {required ? <span className="text-red-500">*</span> : null}
                </label>
            ) : null}

            <textarea
                id={taId}
                name={name}
                className={[
                    "mt-1 p-2 w-full rounded border text-sm outline-none resize-y",
                    "bg-white dark:bg-gray-800 dark:text-white",
                    error
                        ? "border-red-500 ring-1 ring-red-300"
                        : "border-gray-300 dark:border-gray-600 focus:ring-2 focus:ring-indigo-300",
                    textareaClassName,
                ].join(" ")}
                value={value}
                onChange={onChange}
                rows={rows}
                placeholder={placeholder}
                disabled={disabled}
                required={required}
                aria-invalid={!!error}
                aria-describedby={describedBy}
                {...props}
            />

            {error ? (
                <p id={`${taId}-error`} className="mt-1 text-xs text-red-600">
                    {error}
                </p>
            ) : helpText ? (
                <p id={`${taId}-help`} className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    {helpText}
                </p>
            ) : null}
        </div>
    );
};

export default Textarea;
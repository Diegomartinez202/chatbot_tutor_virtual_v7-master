import React from "react";

/**
 * Soporta:
 * - options: [{ value, label, disabled? }]
 * - grupos:  [{ label, options: [{ value, label, disabled? }] }]
 */
const Select = ({
    label,
    value,
    onChange,
    options = [],
    placeholder = "Selecciona…",
    name,
    id,
    disabled = false,
    required = false,
    error = "",
    helpText = "",
    className = "",
    selectClassName = "",
    ...props
}) => {
    const selId = id || name || `sel-${Math.random().toString(36).slice(2)}`;
    const describedBy = [
        error ? `${selId}-error` : null,
        helpText ? `${selId}-help` : null,
    ].filter(Boolean).join(" ") || undefined;

    const isGroup = (opt) => opt && typeof opt === "object" && Array.isArray(opt.options);

    return (
        <div className={`mb-4 ${className}`}>
            {label ? (
                <label
                    htmlFor={selId}
                    className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                >
                    {label} {required ? <span className="text-red-500">*</span> : null}
                </label>
            ) : null}

            <select
                id={selId}
                name={name}
                value={value}
                onChange={onChange}
                disabled={disabled}
                required={required}
                aria-invalid={!!error}
                aria-describedby={describedBy}
                className={[
                    "mt-1 p-2 w-full rounded border text-sm outline-none",
                    "bg-white dark:bg-gray-800 dark:text-white",
                    error
                        ? "border-red-500 ring-1 ring-red-300"
                        : "border-gray-300 dark:border-gray-600 focus:ring-2 focus:ring-indigo-300",
                    selectClassName,
                ].join(" ")}
                {...props}
            >
                {placeholder ? (
                    <option value="" disabled hidden>
                        {placeholder}
                    </option>
                ) : null}

                {options.map((opt) =>
                    isGroup(opt) ? (
                        <optgroup key={String(opt.label)} label={opt.label}>
                            {(opt.options || []).map((o) => (
                                <option
                                    key={String(o.value ?? o.label)}
                                    value={o.value ?? o.label}
                                    disabled={!!o.disabled}
                                >
                                    {o.label ?? String(o.value ?? o.label)}
                                </option>
                            ))}
                        </optgroup>
                    ) : (
                        <option
                            key={String(opt.value ?? opt.label ?? opt)}
                            value={opt.value ?? opt.label ?? opt}
                            disabled={!!opt.disabled}
                        >
                            {opt.label ?? String(opt.value ?? opt)}
                        </option>
                    )
                )}
            </select>

            {error ? (
                <p id={`${selId}-error`} className="mt-1 text-xs text-red-600">
                    {error}
                </p>
            ) : helpText ? (
                <p id={`${selId}-help`} className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    {helpText}
                </p>
            ) : null}
        </div>
    );
};

export default Select;
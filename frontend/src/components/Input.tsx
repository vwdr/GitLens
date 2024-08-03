// Input.tsx
import React from "react";
import './Input.css'
import { useState } from "react";

interface InputProps {
    placeholder: string;
    onInputChange: (value: string) => void; // Add a callback to handle input change
}

export const Input: React.FC<InputProps> = ({ placeholder, onInputChange }) => {
    const [inputValue, setInputValue] = useState<string>("");
    const [error, setError] = useState<string>("");

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const value = event.target.value;
        setInputValue(value);
        onInputChange(value); // Invoke the callback with the input value

        // Clear error when user starts typing again
        setError("");
    };

    const validateURL = (url: string): boolean => {
        const githubPrefix = "github.com/";
        // Check if the URL starts with the GitHub prefix
        if (url.startsWith(githubPrefix)) {
            // If the URL starts with the prefix, it's considered valid
            return true;
        } else {
            // If the URL doesn't start with the prefix, it's considered invalid
            return false;
        }
    };

    return (
        <div>
            <input
                type="text"
                placeholder={placeholder}
                value={inputValue}
                onChange={handleChange}
                className={error ? "input-error" : ""}
            />
            {error && <div className="error-message">{error}</div>}
        </div>
    );
};
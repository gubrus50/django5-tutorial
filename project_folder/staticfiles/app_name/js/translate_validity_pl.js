// AI Generated @ copilot.microsoft.com 26/Mar/2025 & edited by McRaZick

const validityTranslations = {
    valueMissing: "To pole jest wymagane.",
    typeMismatch: "Wprowadź poprawny typ danych (np. email lub URL).",
    patternMismatch: "Wartość nie pasuje do wzorca.",
    tooShort: "Wprowadź co najmniej {minLength} znaków.",
    tooLong: "Wartość przekracza maksymalną liczbę znaków ({maxLength}).",
    rangeUnderflow: "Wprowadź wartość większą lub równą {min}.",
    rangeOverflow: "Wprowadź wartość mniejszą lub równą {max}.",
    stepMismatch: "Wartość musi być zgodna z krokiem {step}.",
    invalidPostalCode: "Wprowadź poprawny kod pocztowy.",
    valid: ""
};

const translateValidity = (validity, input) => {
    for (let [key, message] of Object.entries(validityTranslations)) {
        if (validity[key]) {
            // Replace placeholders dynamically if applicable
            message = message
                .replace("{minLength}", input.minLength || "")
                .replace("{maxLength}", input.maxLength || "")
                .replace("{min}", input.min || "")
                .replace("{max}", input.max || "")
                .replace("{step}", input.step || "");
            return message;
        }
    }
    return "";
};
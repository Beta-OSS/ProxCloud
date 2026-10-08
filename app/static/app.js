document.addEventListener("click", async (event) => {
    const target = event.target;

    if (!(target instanceof HTMLElement)) {
        return;
    }

    // Close password reset modal.
    if (
        target.closest("#password-reset-close") ||
        target.closest("#password-reset-done")
    ) {
        document.getElementById("password-reset-modal")?.remove();
        return;
    }

    // Close when clicking the backdrop.
    if (target.id === "password-reset-modal") {
        target.remove();
        return;
    }

    // Copy generated password.
    const copyButton = target.closest("#copy-generated-password");

    if (copyButton instanceof HTMLButtonElement) {
        const passwordElement = document.getElementById("generated-password");

        if (!passwordElement) {
            return;
        }

        const password = passwordElement.textContent ?? "";

        try {
            await navigator.clipboard.writeText(password);

            copyButton.textContent = "Copied!";

            window.setTimeout(() => {
                if (document.body.contains(copyButton)) {
                    copyButton.textContent = "Copy";
                }
            }, 1500);
        } catch (error) {
            console.error("Failed to copy password:", error);

            copyButton.textContent = "Copy failed";

            window.setTimeout(() => {
                if (document.body.contains(copyButton)) {
                    copyButton.textContent = "Copy";
                }
            }, 1500);
        }
    }
});

// Escape closes the password reset modal.
document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") {
        return;
    }

    document.getElementById("password-reset-modal")?.remove();
});
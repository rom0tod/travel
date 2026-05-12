/**
 * Общая клиентская логика TripPlanner:
 *   - переключение лайка через fetch (AJAX),
 *   - копирование ссылки на поездку в буфер обмена.
 */
(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        initLikeButton();
        initCopyLinkButton();
    });

    function initLikeButton() {
        const button = document.getElementById("likeButton");
        if (!button) {
            return;
        }
        button.addEventListener("click", async function () {
            const tripId = button.dataset.tripId;
            try {
                const response = await fetch(`/trips/${tripId}/like`, {
                    method: "POST",
                    credentials: "same-origin",
                    headers: { "Accept": "application/json" }
                });
                const data = await response.json();
                if (!data.success) {
                    showFlash(data.error || "Не удалось обновить лайк.",
                              "danger");
                    return;
                }
                updateLikeButton(button, data.liked, data.likes_count);
            } catch (err) {
                showFlash("Сеть недоступна, попробуйте ещё раз.", "danger");
            }
        });
    }

    function updateLikeButton(button, liked, count) {
        const counter = document.getElementById("likeCount");
        if (counter) {
            counter.textContent = count;
        }
        button.classList.toggle("btn-danger", liked);
        button.classList.toggle("btn-outline-light", !liked);
        const icon = button.querySelector("i");
        if (icon) {
            icon.classList.toggle("bi-heart-fill", liked);
            icon.classList.toggle("bi-heart", !liked);
        }
    }

    function initCopyLinkButton() {
        const button = document.getElementById("copyLinkBtn");
        const input = document.getElementById("shareLink");
        if (!button || !input) {
            return;
        }
        button.addEventListener("click", async function () {
            try {
                await navigator.clipboard.writeText(input.value);
                button.innerHTML = '<i class="bi bi-check2"></i>';
                setTimeout(() => {
                    button.innerHTML = '<i class="bi bi-clipboard"></i>';
                }, 1500);
            } catch (err) {
                input.select();
                document.execCommand("copy");
            }
        });
    }

    function showFlash(message, category) {
        const container = document.querySelector("main .container");
        if (!container) {
            alert(message);
            return;
        }
        const alert = document.createElement("div");
        alert.className =
            `alert alert-${category} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close"
                    data-bs-dismiss="alert"></button>
        `;
        container.prepend(alert);
    }
})();

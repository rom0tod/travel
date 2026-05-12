/**
 * Работа с картой Leaflet:
 *   - отрисовка точек маршрута на странице поездки,
 *   - выбор координат точки кликом + автокодирование адреса
 *     через серверный эндпоинт /api/geocode.
 */
(function () {
    "use strict";

    const DEFAULT_CENTER = [55.7558, 37.6173];
    const DEFAULT_ZOOM = 4;
    const TILE_URL =
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
    const TILE_OPTIONS = {
        maxZoom: 18,
        attribution: "© OpenStreetMap"
    };

    document.addEventListener("DOMContentLoaded", function () {
        renderTripMap();
    });

    function renderTripMap() {
        const container = document.getElementById("tripMap");
        if (!container || typeof L === "undefined") {
            return;
        }
        const places = (window.TRIP_PLACES || []).filter(
            (place) => place.lat !== null && place.lng !== null
        );

        const map = L.map(container).setView(DEFAULT_CENTER, DEFAULT_ZOOM);
        L.tileLayer(TILE_URL, TILE_OPTIONS).addTo(map);

        if (!places.length) {
            return;
        }

        const bounds = [];
        const grouped = groupByDay(places);

        Object.keys(grouped).forEach(function (day) {
            const dayPlaces = grouped[day];
            dayPlaces.forEach(function (place, index) {
                const marker = L.marker([place.lat, place.lng], {
                    icon: buildLabelIcon(parseInt(day, 10))
                }).addTo(map);
                marker.bindPopup(
                    `<strong>День ${day}, ${index + 1}.</strong> ` +
                    escapeHtml(place.name)
                );
                bounds.push([place.lat, place.lng]);
            });

            const path = dayPlaces.map((p) => [p.lat, p.lng]);
            if (path.length > 1) {
                L.polyline(path, {
                    color: dayColor(parseInt(day, 10)),
                    weight: 3,
                    opacity: 0.7
                }).addTo(map);
            }
        });

        if (bounds.length) {
            map.fitBounds(bounds, { padding: [30, 30] });
        }
    }

    function groupByDay(places) {
        const grouped = {};
        places.forEach(function (place) {
            const day = place.day || 1;
            if (!grouped[day]) {
                grouped[day] = [];
            }
            grouped[day].push(place);
        });
        return grouped;
    }

    function buildLabelIcon(day) {
        return L.divIcon({
            className: "tp-marker-wrapper",
            html: `<div class="tp-marker-label" ` +
                  `style="background:${dayColor(day)}">${day}</div>`,
            iconSize: [28, 28],
            iconAnchor: [14, 14]
        });
    }

    const PALETTE = [
        "#2563eb", "#7c3aed", "#db2777",
        "#f97316", "#16a34a", "#0d9488", "#dc2626"
    ];

    function dayColor(day) {
        return PALETTE[(day - 1) % PALETTE.length];
    }

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    // ------------------------------------------------------------------
    // Выбор координат при создании/редактировании точки
    // ------------------------------------------------------------------

    window.initPlacePicker = function (options) {
        const container = document.getElementById(options.mapId);
        if (!container || typeof L === "undefined") {
            return;
        }
        const latInput = document.getElementById(options.latInput);
        const lngInput = document.getElementById(options.lngInput);
        const geocodeBtn = document.getElementById(options.geocodeBtn);
        const addressInput = document.getElementById(options.addressInput);
        const statusEl = document.getElementById(options.statusEl);

        const startLat = parseFloat(latInput.value);
        const startLng = parseFloat(lngInput.value);
        const startPoint = (!isNaN(startLat) && !isNaN(startLng))
            ? [startLat, startLng]
            : DEFAULT_CENTER;
        const startZoom = (!isNaN(startLat) && !isNaN(startLng)) ? 13 : 4;

        const map = L.map(container).setView(startPoint, startZoom);
        L.tileLayer(TILE_URL, TILE_OPTIONS).addTo(map);

        let marker = null;
        if (!isNaN(startLat) && !isNaN(startLng)) {
            marker = L.marker(startPoint, { draggable: true }).addTo(map);
            bindMarker(marker);
        }

        map.on("click", function (event) {
            placeMarker(event.latlng);
        });

        function placeMarker(latLng) {
            if (marker === null) {
                marker = L.marker(latLng, { draggable: true }).addTo(map);
                bindMarker(marker);
            } else {
                marker.setLatLng(latLng);
            }
            latInput.value = latLng.lat.toFixed(6);
            lngInput.value = latLng.lng.toFixed(6);
        }

        function bindMarker(m) {
            m.on("dragend", function () {
                const pos = m.getLatLng();
                latInput.value = pos.lat.toFixed(6);
                lngInput.value = pos.lng.toFixed(6);
            });
        }

        if (geocodeBtn && addressInput) {
            geocodeBtn.addEventListener("click", async function () {
                const address = (addressInput.value || "").trim();
                if (!address) {
                    setStatus("Сначала введите адрес.", "text-warning");
                    return;
                }
                setStatus("Ищем…", "text-muted");
                try {
                    const response = await fetch(
                        "/api/geocode?address=" + encodeURIComponent(address)
                    );
                    const data = await response.json();
                    if (!data.success) {
                        setStatus(data.error || "Адрес не найден.",
                                  "text-danger");
                        return;
                    }
                    const latLng = L.latLng(data.latitude, data.longitude);
                    placeMarker(latLng);
                    map.setView(latLng, 15);
                    setStatus("Найдено: " + data.display_name,
                              "text-success");
                } catch (err) {
                    setStatus("Сеть недоступна.", "text-danger");
                }
            });
        }

        function setStatus(text, cls) {
            if (statusEl) {
                statusEl.className = "small mt-1 " + cls;
                statusEl.textContent = text;
            }
        }
    };
})();

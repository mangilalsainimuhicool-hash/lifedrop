/**
 * LifeDrop - Emergency Blood Service UI Handlers
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Helper to retrieve CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const csrftoken = getCookie('csrftoken');

    // 2. Real-time Donor Availability Switcher
    const availabilityToggle = document.getElementById('btn-toggle-availability');
    if (availabilityToggle) {
        availabilityToggle.addEventListener('click', function () {
            const btn = this;
            const originalHtml = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Updating...';

            fetch('/api/donor/toggle-availability/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                btn.disabled = false;
                if (data.success) {
                    const statusBadge = document.getElementById('donor-availability-badge');
                    if (statusBadge) {
                        if (data.is_available) {
                            statusBadge.className = 'badge bg-success py-2 px-3';
                            statusBadge.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> Available to Donate';
                            btn.className = 'btn btn-outline-warning w-100';
                            btn.innerHTML = '<i class="bi bi-pause-circle me-1"></i> Pause Availability';
                        } else {
                            statusBadge.className = 'badge bg-secondary py-2 px-3';
                            statusBadge.innerHTML = '<i class="bi bi-x-circle-fill me-1"></i> Temporarily Unavailable';
                            btn.className = 'btn btn-outline-success w-100';
                            btn.innerHTML = '<i class="bi bi-play-circle me-1"></i> Resume Availability';
                        }
                    }
                } else {
                    btn.innerHTML = originalHtml;
                    alert('Error updating status: ' + (data.error || 'Server error'));
                }
            })
            .catch(err => {
                btn.disabled = false;
                btn.innerHTML = originalHtml;
                console.error('Failed to toggle availability:', err);
            });
        });
    }

    // 3. Leaflet OpenStreetMap Initialization for Blood Banks
    const mapElement = document.getElementById('bloodbank-map');
    if (mapElement && typeof L !== 'undefined') {
        const defaultLat = 20.5937;
        const defaultLng = 78.9629; // Center of India
        const defaultZoom = 5;

        const map = L.map('bloodbank-map').setView([defaultLat, defaultLng], defaultZoom);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 18
        }).addTo(map);

        // Custom red marker icon
        const redIcon = L.divIcon({
            className: 'custom-map-marker',
            html: '<div style="background-color: #c8102e; width: 28px; height: 28px; border-radius: 50%; border: 3px solid #ffffff; box-shadow: 0 3px 8px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 14px;">+</div>',
            iconSize: [28, 28],
            iconAnchor: [14, 14]
        });

        // Markers payload injected in data-markers attribute
        const markersDataRaw = mapElement.getAttribute('data-markers');
        if (markersDataRaw) {
            try {
                const markers = JSON.parse(markersDataRaw);
                const bounds = [];

                markers.forEach(function (m) {
                    if (m.lat && m.lng) {
                        bounds.push([m.lat, m.lng]);
                        const popupContent = `
                            <div style="font-family: system-ui; max-width: 240px;">
                                <h6 style="color: #c8102e; margin-bottom: 4px; font-weight: 700;">${m.name}</h6>
                                <p style="font-size: 12px; margin-bottom: 4px; color: #475569;">${m.address}, ${m.city}</p>
                                <p style="font-size: 12px; margin-bottom: 4px;"><strong>Hours:</strong> ${m.hours}</p>
                                <p style="font-size: 12px; margin-bottom: 8px;"><strong>Phone:</strong> <a href="tel:${m.phone}">${m.phone}</a></p>
                                <a href="${m.url}" class="btn btn-sm btn-outline-danger w-100" style="font-size: 12px;">View Details & Stock</a>
                            </div>
                        `;
                        L.marker([m.lat, m.lng], { icon: redIcon })
                            .addTo(map)
                            .bindPopup(popupContent);
                    }
                });

                if (bounds.length > 0) {
                    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 13 });
                }
            } catch (e) {
                console.error('Error parsing map markers:', e);
            }
        }
    }

    // 4. Quick Copy Reference ID
    const copyBtns = document.querySelectorAll('.btn-copy-ref');
    copyBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            const refText = this.getAttribute('data-ref');
            if (refText) {
                navigator.clipboard.writeText(refText).then(() => {
                    const originalText = this.innerText;
                    this.innerText = 'Copied!';
                    setTimeout(() => {
                        this.innerText = originalText;
                    }, 2000);
                });
            }
        });
    });
});

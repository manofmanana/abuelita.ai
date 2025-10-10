// About page JavaScript functionality
let isPlaying = false;
let backgroundMusic = null;

// Initialize background music (placeholder)
document.addEventListener("DOMContentLoaded", function () {
    // Placeholder for audio initialization
    // In a real implementation, you would load the mariachi music file here
    console.log("Background music initialized (placeholder)");
});

// Toggle music play/pause
function toggleMusic() {
    const playPauseBtn = document.getElementById("play-pause-btn");
    const playIcon = document.getElementById("play-icon");

    if (!isPlaying) {
        // Start playing (placeholder)
        playIcon.className = "bi bi-pause-fill";
        isPlaying = true;
        console.log("Playing mariachi music (placeholder)");

        // Show toast notification
        showToast("🎵 Playing soft mariachi music in honor of Francisca", "info");
    } else {
        // Pause playing (placeholder)
        playIcon.className = "bi bi-play-fill";
        isPlaying = false;
        console.log("Pausing mariachi music (placeholder)");
    }
}

// Volume control
document.addEventListener("DOMContentLoaded", function() {
    const volumeSlider = document.getElementById("volume-slider");
    if (volumeSlider) {
        volumeSlider.addEventListener("input", function (e) {
            const volume = e.target.value / 100;
            console.log(`Setting volume to ${volume} (placeholder)`);
            
            // In a real implementation, you would set the audio volume here
            // backgroundMusic.volume = volume;
        });
    }
});

// Show toast notification
function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast align-items-center text-bg-${type} border-0 position-fixed top-0 end-0 m-3`;
    toast.setAttribute("role", "alert");
    toast.style.zIndex = "9999";
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    document.body.appendChild(toast);

    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();

    toast.addEventListener("hidden.bs.toast", function () {
        document.body.removeChild(toast);
    });
}

// Smooth scrolling for internal links
document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener("click", function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute("href"));
            if (target) {
                target.scrollIntoView({
                    behavior: "smooth",
                    block: "start",
                });
            }
        });
    });
});
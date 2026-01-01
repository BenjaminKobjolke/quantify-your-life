/**
 * Stats chart initialization using Chart.js
 * Reads data from the chart container's data attributes
 */

document.addEventListener("DOMContentLoaded", function () {
    const chartContainer = document.getElementById("stats-chart");
    if (!chartContainer) return;

    const canvas = document.getElementById("stats-chart-canvas");
    if (!canvas) return;

    // Read data from data attributes
    const labels = JSON.parse(chartContainer.dataset.labels || "[]");
    const values = JSON.parse(chartContainer.dataset.values || "[]");

    // Convert seconds to hours for display
    const hoursData = values.map(function (seconds) {
        return (seconds / 3600).toFixed(1);
    });

    const ctx = canvas.getContext("2d");

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Hours",
                    data: hoursData,
                    backgroundColor: "rgba(0, 212, 255, 0.6)",
                    borderColor: "rgba(0, 212, 255, 1)",
                    borderWidth: 1,
                    borderRadius: 4,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const hours = parseFloat(context.raw);
                            const h = Math.floor(hours);
                            const m = Math.round((hours - h) * 60);
                            return h + "h " + m + "m";
                        },
                    },
                },
            },
            scales: {
                x: {
                    ticks: {
                        color: "#aaa",
                    },
                    grid: {
                        color: "rgba(255, 255, 255, 0.1)",
                    },
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: "#aaa",
                        callback: function (value) {
                            return value + "h";
                        },
                    },
                    grid: {
                        color: "rgba(255, 255, 255, 0.1)",
                    },
                },
            },
        },
    });
});

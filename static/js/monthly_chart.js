/**
 * Monthly comparison grouped bar chart using Chart.js
 * Reads data from the chart container's data attributes
 * Supports dropdown and arrow key navigation between months
 */

document.addEventListener("DOMContentLoaded", function () {
    var chartContainer = document.getElementById("monthly-chart");
    if (!chartContainer) return;

    var canvas = document.getElementById("monthly-chart-canvas");
    if (!canvas) return;

    var selector = document.getElementById("month-selector");

    // Read data from data attributes
    var fullLabels = JSON.parse(chartContainer.dataset.labels || "[]");
    var fullDatasets = JSON.parse(chartContainer.dataset.datasets || "[]");
    var unitLabel = chartContainer.dataset.unitLabel || "";

    // Current view state: "all" or "1"-"12"
    var currentView = "all";

    // Format value based on unit type
    function formatValue(value) {
        var upperUnit = unitLabel.toUpperCase();
        if (upperUnit === "EUR" || upperUnit === "USD" || upperUnit === "GBP" || upperUnit === "CHF") {
            // Currency - no decimals, thousands separator
            return value.toLocaleString("de-DE", { maximumFractionDigits: 0 }) + " " + unitLabel;
        }
        // Other units - 1 decimal
        return value.toLocaleString("de-DE", { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + " " + unitLabel;
    }

    var ctx = canvas.getContext("2d");

    var chart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: fullLabels.slice(),
            datasets: fullDatasets.map(function(ds) {
                return Object.assign({}, ds, { data: ds.data.slice() });
            }),
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: "top",
                    labels: {
                        color: "#aaa",
                        usePointStyle: true,
                        padding: 20,
                    },
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            var value = context.raw || 0;
                            return context.dataset.label + ": " + formatValue(value);
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
                            return value.toLocaleString("de-DE") + " " + unitLabel;
                        },
                    },
                    grid: {
                        color: "rgba(255, 255, 255, 0.1)",
                    },
                },
            },
        },
    });

    // Update chart based on selected view
    function updateChart(view) {
        currentView = view;

        // Update dropdown to match
        if (selector) {
            selector.value = view;
        }

        if (view === "all") {
            // Show all months
            chart.data.labels = fullLabels.slice();
            chart.data.datasets = fullDatasets.map(function(ds) {
                return Object.assign({}, ds, { data: ds.data.slice() });
            });
        } else {
            // Show single month
            var monthIndex = parseInt(view, 10) - 1;
            chart.data.labels = [fullLabels[monthIndex]];
            chart.data.datasets = fullDatasets.map(function(ds) {
                return Object.assign({}, ds, { data: [ds.data[monthIndex]] });
            });
        }

        chart.update();
    }

    // Navigate to next view (right arrow)
    function navigateNext() {
        if (currentView === "all") {
            updateChart("1");
        } else if (currentView === "12") {
            updateChart("all");
        } else {
            updateChart(String(parseInt(currentView, 10) + 1));
        }
    }

    // Navigate to previous view (left arrow)
    function navigatePrev() {
        if (currentView === "all") {
            updateChart("12");
        } else if (currentView === "1") {
            updateChart("all");
        } else {
            updateChart(String(parseInt(currentView, 10) - 1));
        }
    }

    // Dropdown change handler
    if (selector) {
        selector.addEventListener("change", function(e) {
            updateChart(e.target.value);
        });
    }

    // Arrow key navigation
    document.addEventListener("keydown", function(e) {
        // Only handle arrow keys if not focused on an input
        if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") {
            return;
        }

        if (e.key === "ArrowRight") {
            e.preventDefault();
            navigateNext();
        } else if (e.key === "ArrowLeft") {
            e.preventDefault();
            navigatePrev();
        }
    });
});

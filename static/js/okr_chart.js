/**
 * OKR line chart initialization using Chart.js
 * Reads data from the chart container's data attributes
 * Displays Key Result progress over time as line chart (0-100%)
 * Supports prognosis (dashed) datasets with null gaps
 */

document.addEventListener("DOMContentLoaded", function () {
    var chartContainer = document.getElementById("okr-chart");
    if (!chartContainer) return;

    var canvas = document.getElementById("okr-chart-canvas");
    if (!canvas) return;

    // Read data from data attributes
    var labels = JSON.parse(chartContainer.dataset.labels || "[]");
    var datasets = JSON.parse(chartContainer.dataset.datasets || "[]");

    var ctx = canvas.getContext("2d");

    new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: datasets,
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            spanGaps: false,
            interaction: {
                mode: "index",
                intersect: false,
            },
            plugins: {
                legend: {
                    display: true,
                    position: "top",
                    onClick: function (e, legendItem, legend) {
                        var chart = legend.chart;
                        var index = legendItem.datasetIndex;
                        // Toggle the clicked (actual) dataset
                        var meta = chart.getDatasetMeta(index);
                        meta.hidden = meta.hidden === null ? !chart.data.datasets[index].hidden : null;
                        // Also toggle the paired prognosis dataset (label + " (Prognose)")
                        var actualLabel = chart.data.datasets[index].label;
                        chart.data.datasets.forEach(function (ds, i) {
                            if (ds.label === actualLabel + " (Prognose)") {
                                var progMeta = chart.getDatasetMeta(i);
                                progMeta.hidden = meta.hidden;
                            }
                        });
                        chart.update();
                    },
                    labels: {
                        color: "#aaa",
                        usePointStyle: true,
                        padding: 20,
                        filter: function (item) {
                            // Hide prognosis entries from legend
                            return item.text.indexOf("(Prognose)") === -1;
                        },
                    },
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            if (context.raw === null || context.raw === undefined) {
                                return null;
                            }
                            var value = context.raw;
                            return context.dataset.label + ": " + value.toFixed(1) + "%";
                        },
                    },
                    filter: function (item) {
                        return item.raw !== null && item.raw !== undefined;
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
                    max: 100,
                    ticks: {
                        color: "#aaa",
                        callback: function (value) {
                            return value + "%";
                        },
                        stepSize: 10,
                    },
                    grid: {
                        color: "rgba(255, 255, 255, 0.1)",
                    },
                },
            },
        },
    });
});

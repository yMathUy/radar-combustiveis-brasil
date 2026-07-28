const DATA_PATHS = {
    metadata: "./data/metadata.json",
    nationalPrices: "./data/latest_national_prices.json",
    statePrices: "./data/latest_state_gasoline_prices.json",
    nationalTrends: "./data/weekly_national_trends.json",
};


/*
 * BRL values keep the Brazilian monetary format because
 * the dashboard displays prices collected in Brazil.
 */
const currencyFormatter = new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 3,
    maximumFractionDigits: 3,
});

const integerFormatter = new Intl.NumberFormat("en-US");

const dateFormatter = new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
});

const dateTimeFormatter = new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
});


async function fetchJson(path) {
    const response = await fetch(path);

    if (!response.ok) {
        throw new Error(
            `Could not load ${path}. HTTP status: ${response.status}`
        );
    }

    return response.json();
}


function formatDate(dateString) {
    const date = new Date(`${dateString}T00:00:00Z`);

    if (Number.isNaN(date.getTime())) {
        return "Invalid date";
    }

    return dateFormatter.format(date);
}


function formatUnit(unit) {
    if (unit.includes("m³")) {
        return "per m³";
    }

    return "per liter";
}


function createDetailItem(label, value) {
    return `
        <div>
            <dt>${label}</dt>
            <dd>${value}</dd>
        </div>
    `;
}


function createPriceCard(price) {
    const article = document.createElement("article");

    article.className = "price-card";

    article.innerHTML = `
        <div class="price-card-header">
            <h3>${price.product}</h3>

            <span class="unit-badge">
                ${formatUnit(price.measurement_unit)}
            </span>
        </div>

        <div class="price-value">
            <strong>
                ${currencyFormatter.format(price.average_price)}
            </strong>

            <span>average price</span>
        </div>

        <dl class="price-details">
            ${createDetailItem(
                "Median",
                currencyFormatter.format(price.median_price)
            )}

            ${createDetailItem(
                "Stations",
                integerFormatter.format(price.station_count)
            )}

            ${createDetailItem(
                "Minimum price",
                currencyFormatter.format(price.minimum_price)
            )}

            ${createDetailItem(
                "Maximum price",
                currencyFormatter.format(price.maximum_price)
            )}
        </dl>
    `;

    return article;
}


function renderPriceCards(prices) {
    const container = document.querySelector("#price-cards");

    container.replaceChildren();

    if (!Array.isArray(prices) || prices.length === 0) {
        container.innerHTML = `
            <p class="empty-message">
                No national price records were found.
            </p>
        `;

        return;
    }

    const fragment = document.createDocumentFragment();

    prices.forEach((price) => {
        fragment.appendChild(
            createPriceCard(price)
        );
    });

    container.appendChild(fragment);
}


function createStateRow(state, index) {
    const row = document.createElement("tr");

    row.innerHTML = `
        <td class="rank">
            ${index + 1}
        </td>

        <td>
            <span class="state-code">
                ${state.state_code}
            </span>
        </td>

        <td class="numeric-cell">
            ${currencyFormatter.format(state.average_price)}
        </td>

        <td class="numeric-cell">
            ${currencyFormatter.format(state.median_price)}
        </td>

        <td class="numeric-cell">
            ${integerFormatter.format(state.price_observations)}
        </td>

        <td class="numeric-cell">
            ${integerFormatter.format(state.station_count)}
        </td>
    `;

    return row;
}


function renderStateRanking(states) {
    const tableBody = document.querySelector(
        "#state-ranking-body"
    );

    tableBody.replaceChildren();

    if (!Array.isArray(states) || states.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="empty-table-cell">
                    No eligible state records were found.
                </td>
            </tr>
        `;

        return;
    }

    const fragment = document.createDocumentFragment();

    states.forEach((state, index) => {
        fragment.appendChild(
            createStateRow(state, index)
        );
    });

    tableBody.appendChild(fragment);
}


function renderMetadata(metadata) {
    const latestWeek = document.querySelector("#latest-week");
    const generatedAt = document.querySelector("#generated-at");
    const rankingNote = document.querySelector(
        "#state-ranking-note"
    );

    const startDate = formatDate(
        metadata.latest_complete_week.start
    );

    const endDate = formatDate(
        metadata.latest_complete_week.end
    );

    latestWeek.textContent = (
        `Reporting week: ${startDate} to ${endDate}`
    );

    const generatedDate = new Date(
        metadata.generated_at_utc
    );

    generatedAt.textContent = Number.isNaN(
        generatedDate.getTime()
    )
        ? "Export date unavailable"
        : `Data exported: ${dateTimeFormatter.format(generatedDate)}`;

    rankingNote.textContent = (
        `Only states with at least ${
            integerFormatter.format(
                metadata.state_ranking.minimum_observations
            )
        } price observations are included.`
    );
}

const SVG_NAMESPACE = "http://www.w3.org/2000/svg";

const CHART_SERIES = [
    {
        product: "GASOLINA",
        label: "Gasoline",
        color: "#176b87",
    },
    {
        product: "ETANOL",
        label: "Ethanol",
        color: "#2f855a",
    },
    {
        product: "DIESEL",
        label: "Diesel",
        color: "#b7791f",
    },
    {
        product: "DIESEL S10",
        label: "Diesel S10",
        color: "#805ad5",
    },
];


function createSvgElement(tagName, attributes = {}) {
    const element = document.createElementNS(
        SVG_NAMESPACE,
        tagName
    );

    Object.entries(attributes).forEach(([name, value]) => {
        element.setAttribute(name, String(value));
    });

    return element;
}


function groupTrendsByProduct(records) {
    return CHART_SERIES.map((series) => ({
        ...series,
        values: records
            .filter(
                (record) => record.product === series.product
            )
            .sort(
                (first, second) => (
                    first.week_start.localeCompare(
                        second.week_start
                    )
                )
            ),
    }));
}


function renderTrendLegend(seriesList) {
    const legend = document.querySelector("#trend-legend");

    legend.replaceChildren();

    seriesList.forEach((series) => {
        const item = document.createElement("span");

        item.className = "legend-item";

        item.innerHTML = `
            <span
                class="legend-marker"
                style="background: ${series.color}"
                aria-hidden="true"
            ></span>

            ${series.label}
        `;

        legend.appendChild(item);
    });
}


function showChartTooltip(event, series, record) {
    const tooltip = document.querySelector("#chart-tooltip");

    tooltip.innerHTML = `
        <strong>${series.label}</strong><br>
        Week starting ${formatDate(record.week_start)}<br>
        Average: ${currencyFormatter.format(
            record.average_price
        )} per liter
    `;

    tooltip.hidden = false;

    const horizontalOffset = 14;
    const verticalOffset = 14;

    tooltip.style.left = (
        `${event.clientX + horizontalOffset}px`
    );

    tooltip.style.top = (
        `${event.clientY + verticalOffset}px`
    );
}


function hideChartTooltip() {
    document.querySelector("#chart-tooltip").hidden = true;
}


function renderTrendChart(records) {
    const svg = document.querySelector("#trend-chart");

    if (!Array.isArray(records) || records.length === 0) {
        svg.replaceChildren();

        const message = createSvgElement("text", {
            x: 400,
            y: 180,
            "text-anchor": "middle",
            class: "chart-error",
        });

        message.textContent = "No weekly trend records were found.";

        svg.setAttribute("viewBox", "0 0 800 360");
        svg.appendChild(message);

        return;
    }

    const width = 1100;
    const height = 520;

    const margin = {
        top: 24,
        right: 34,
        bottom: 72,
        left: 74,
    };

    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;

    const seriesList = groupTrendsByProduct(records);

    const dates = [
        ...new Set(
            records.map((record) => record.week_start)
        ),
    ].sort();

    const prices = records.map(
        (record) => Number(record.average_price)
    );

    const minimumPrice = Math.floor(
        Math.min(...prices) * 2
    ) / 2;

    const maximumPrice = Math.ceil(
        Math.max(...prices) * 2
    ) / 2;

    const xPosition = (date) => {
        const index = dates.indexOf(date);

        if (dates.length === 1) {
            return margin.left + plotWidth / 2;
        }

        return (
            margin.left
            + (index / (dates.length - 1)) * plotWidth
        );
    };

    const yPosition = (price) => (
        margin.top
        + (
            (maximumPrice - price)
            / (maximumPrice - minimumPrice)
        ) * plotHeight
    );

    svg.replaceChildren();
    svg.setAttribute(
        "viewBox",
        `0 0 ${width} ${height}`
    );

    const verticalTicks = 6;

    for (
        let tickIndex = 0;
        tickIndex <= verticalTicks;
        tickIndex += 1
    ) {
        const ratio = tickIndex / verticalTicks;

        const price = (
            maximumPrice
            - ratio * (maximumPrice - minimumPrice)
        );

        const y = (
            margin.top
            + ratio * plotHeight
        );

        const gridLine = createSvgElement("line", {
            x1: margin.left,
            y1: y,
            x2: width - margin.right,
            y2: y,
            class: "chart-grid-line",
        });

        const label = createSvgElement("text", {
            x: margin.left - 12,
            y: y + 4,
            "text-anchor": "end",
            class: "chart-axis-label",
        });

        label.textContent = currencyFormatter.format(price);

        svg.appendChild(gridLine);
        svg.appendChild(label);
    }

    const horizontalAxis = createSvgElement("line", {
        x1: margin.left,
        y1: height - margin.bottom,
        x2: width - margin.right,
        y2: height - margin.bottom,
        class: "chart-axis-line",
    });

    svg.appendChild(horizontalAxis);

    const dateStep = Math.max(
        1,
        Math.ceil(dates.length / 8)
    );

    dates.forEach((date, index) => {
        if (
            index % dateStep !== 0
            && index !== dates.length - 1
        ) {
            return;
        }

        const x = xPosition(date);

        const label = createSvgElement("text", {
            x,
            y: height - margin.bottom + 28,
            "text-anchor": "middle",
            class: "chart-axis-label",
        });

        label.textContent = formatDate(date);

        svg.appendChild(label);
    });

    seriesList.forEach((series) => {
        const pathData = series.values
            .map((record, index) => {
                const command = index === 0 ? "M" : "L";

                return (
                    `${command} `
                    + `${xPosition(record.week_start)} `
                    + `${yPosition(record.average_price)}`
                );
            })
            .join(" ");

        const path = createSvgElement("path", {
            d: pathData,
            stroke: series.color,
            class: "chart-series-line",
        });

        svg.appendChild(path);

        series.values.forEach((record) => {
            const point = createSvgElement("circle", {
                cx: xPosition(record.week_start),
                cy: yPosition(record.average_price),
                r: 4,
                fill: series.color,
                class: "chart-point",
                tabindex: 0,
                role: "button",
                "aria-label": (
                    `${series.label}, `
                    + `${formatDate(record.week_start)}, `
                    + `${currencyFormatter.format(
                        record.average_price
                    )} per liter`
                ),
            });

            point.addEventListener(
                "mouseenter",
                (event) => {
                    showChartTooltip(
                        event,
                        series,
                        record
                    );
                }
            );

            point.addEventListener(
                "mousemove",
                (event) => {
                    showChartTooltip(
                        event,
                        series,
                        record
                    );
                }
            );

            point.addEventListener(
                "mouseleave",
                hideChartTooltip
            );

            point.addEventListener(
                "focus",
                (event) => {
                    const bounds = (
                        event.target.getBoundingClientRect()
                    );

                    showChartTooltip(
                        {
                            clientX: bounds.left,
                            clientY: bounds.top,
                        },
                        series,
                        record
                    );
                }
            );

            point.addEventListener(
                "blur",
                hideChartTooltip
            );

            svg.appendChild(point);
        });
    });

    renderTrendLegend(seriesList);
}

function renderError(error) {
    console.error(error);

    const priceContainer = document.querySelector("#price-cards");

    priceContainer.innerHTML = `
        <p class="error-message">
            Dashboard data could not be loaded.
            Verify that the JSON files were generated correctly
            and that the page is running through a local server.
        </p>
    `;

    const tableBody = document.querySelector(
        "#state-ranking-body"
    );

    tableBody.innerHTML = `
        <tr>
            <td colspan="6" class="error-table-cell">
                State ranking could not be loaded.
            </td>
        </tr>
    `;

    document.querySelector("#latest-week").textContent = (
        "Reporting period unavailable"
    );

    document.querySelector("#generated-at").textContent = (
        "Update information unavailable"
    );
}


async function initializeDashboard() {
    try {
        const [
    metadata,
    nationalPrices,
    statePrices,
    nationalTrends,
] = await Promise.all([
    fetchJson(DATA_PATHS.metadata),
    fetchJson(DATA_PATHS.nationalPrices),
    fetchJson(DATA_PATHS.statePrices),
    fetchJson(DATA_PATHS.nationalTrends),
]);

        renderMetadata(metadata);
        renderPriceCards(nationalPrices);
        renderStateRanking(statePrices);
        renderTrendChart(nationalTrends);
    } catch (error) {
        renderError(error);
    }
}


document.addEventListener(
    "DOMContentLoaded",
    initializeDashboard
);
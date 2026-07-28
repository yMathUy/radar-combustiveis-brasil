const DATA_PATHS = {
    metadata: "./data/metadata.json",
    nationalPrices: "./data/latest_national_prices.json",
    statePrices: "./data/latest_state_gasoline_prices.json",
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
        ] = await Promise.all([
            fetchJson(DATA_PATHS.metadata),
            fetchJson(DATA_PATHS.nationalPrices),
            fetchJson(DATA_PATHS.statePrices),
        ]);

        renderMetadata(metadata);
        renderPriceCards(nationalPrices);
        renderStateRanking(statePrices);
    } catch (error) {
        renderError(error);
    }
}


document.addEventListener(
    "DOMContentLoaded",
    initializeDashboard
);
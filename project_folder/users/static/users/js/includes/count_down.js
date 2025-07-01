/** 
 *  REQUIRES
 *    countDown.date = date_object (ISO 8601 format)
 *    countDown.elements = list[] OF elements NOT child nodes
 * 
 *  Load this <script> before initializing above properties.
 *  Specify date and elements (that will display countDown).
 *  Interval will activate once both values are provided.
 *
 *  You can use formatCountdownElements({ element, date });
 *  TO just format and display date without counting it down. 
 * 
 *  ≥1 day left → "N day(s) N hour(s)"                (Time left)
 *  <1 day left → "N hour(s) N minute(s) N second(s)" (Time left)
 */

const countDown = {
    date: null,
    elements: null,
    interval: null,
}


/**
 * Returns a Date object representing a future point in time based on the number of days from now.
 * Supports fractional day values (e.g., 0.5 for 12 hours).
 *
 * @param {number} days - The number of days (can be fractional) to add to the current time.
 * @returns {Date} A new Date object representing the computed future date and time.
 */
const getFutureDate = (days) => {
    const now = new Date();
    return new Date(now.getTime() + days * 24 * 60 * 60 * 1000);
};




/**
 *  Formats a value with pluralized label
 *  @param {number} value - The numeric value
 *  @param {string} label - The singular unit label (e.g., "hour")
 *  @returns {object} Returns {value, noun} where noun is pluralized if needed
 */
const formatValueWithPlural = (value, label) => {
    const noun = `${label}${value !== 1 ? 's' : ''}`;
    return {value, noun};
};



/**
 *  Converts milliseconds into a human-readable time string
 *  @param {number} milliseconds - Time remaining in milliseconds
 *  @returns {list} Returns [{value, noun}, {value, noun}, {value, noun}]
 *  think of it like: [ Hours{}, Minutes{}, Seconds{} ]
 */
const formatRemainingTime = (milliseconds) =>
{
    const totalSeconds = Math.floor(milliseconds / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    return [
        formatValueWithPlural(hours, 'hour'),
        formatValueWithPlural(minutes, 'minute'),
        formatValueWithPlural(seconds, 'second')
    ];
};



/**
 * Updates all countdown elements with the remaining time
 */
const formatCountdownElements = ({ elements, date } = {}) => {

    if (!elements || !date) return;

    const now = new Date();
    const timeRemainingMs = date - now;
    const fullDaysRemaining = Math.floor(timeRemainingMs / (24 * 60 * 60 * 1000));

    elements.forEach(element => {
        if (timeRemainingMs <= 0) {
            element.textContent = 'Deletion window has closed.';
        } 
        else {
            // NOTE: Days = Hours = Minutes = Seconds
            // (Same time but different unit)
            const [h, m, s] = formatRemainingTime(timeRemainingMs);
            const d = formatValueWithPlural(fullDaysRemaining, 'day');

            if (fullDaysRemaining >= 1) {
                // Take away a day(s) from 'h' IF possible, ELSE → false
                // Then format: N hour(s), IF hours is NOT false, ELSE → ''
                let hours = (h.value - 24 * d.value) || false;
                    hours = hours ? `${hours} ${hours === 1 ? 'hour' : 'hours'}` : ''

                // ≥1 day left → "N day(s) N hour(s)" (Time left)
                element.textContent = `${d.value} ${d.noun} ${hours}`;
            }
            else {
                // <1 day left → "N hour(s) N minute(s) N second(s)" (Time left)
                element.textContent = `${h.value} ${h.noun} ${m.value} ${m.noun} ${s.value} ${s.noun}`;
            }
        }
    });

};



/**
 *  Waits until a condition is met (polling with setTimeout).
 *  @param {Function} condition - A function that returns `true` when ready.
 *  @param {number} interval - Polling interval in ms (default: 100ms).
 *  @returns {Promise<void>}
 */
function waitForCondition(condition, interval = 100) {
    return new Promise((resolve) => {
        const check = () => {
            if (condition()) resolve();
            else setTimeout(check, interval);
        };
        check();
    });
}





/* ------- MAIN SCRIPT ------- */


if (typeof countDown.interval !== 'undefined') {
    clearInterval(countDown.interval);
}

// Initialize when DOM is fully loaded
document.addEventListener('DOMContentLoaded', async () => {
    if (countDown.interval) return; // Prevent duplicate intervals

    // Wait until both `countDown.elements` and `countDown.date` are set
    await waitForCondition(() => 
        countDown.elements !== null && 
        countDown.date !== null
    );

    // Start the countdown interval
    countDown.interval = setInterval(() => {
        formatCountdownElements({
            'elements': countDown.elements,
            'date': countDown.date,
        });
    }, 1000);
});
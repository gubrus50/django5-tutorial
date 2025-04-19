// location - localhost:port/?param1=a&param2=b...
// location.search - param1=a&param2=b...

// Get search parameters into Map Object with their values
const search = document.location.search.slice(1).split('&');

// searchMap - Map(param1 -> a, param2 -> b...)
const searchMap = new Map(search.map(s => {
    const [key, value] = s.split('=');
    return [key, decodeURIComponent(value)];
}));





const filters = document.querySelector('#filters');


// hides all #creator_value inputs at #filters
showOnlySpecifiedCreatorInput();

function showOnlySpecifiedCreatorInput(input_id, value) {
    /* Summary of this function: 
    /
    / Hides all creator inputs,
    / Shows creator input specified by input_id, and
    / It optionally updates creator input's value if provided
    */

    let creatorInputs = filters.querySelectorAll('#creator_value');
    [...creatorInputs].map(input => {
        input.disabled = true;
        input.hidden = true;
    });

    if (input_id == undefined) return;

    let input = filters.querySelector(`#creator_value[name=${input_id}]`);
    input.disabled = false;
    input.hidden = false;

    if (value != undefined) input.value = value;
}






// Populate filters if location.search has expected parameters
for (const [key, value] of searchMap) {
    switch (key)
    {
        case 'search':
            document.querySelector('input[name=search_query]').value = searchMap.get('search');
            break;

        case 'creator':
            filters.querySelector('#creator_username').checked = true;
            // shows #creator_value[name=creator_username_value] and update its value
            showOnlySpecifiedCreatorInput('creator_username_value', value);
            break;

        case 'creator_id':
            filters.querySelector('#creator_id').checked = true;
            // shows #creator_value[name=creator_username_value] and update its value
            showOnlySpecifiedCreatorInput('creator_id_value', value);
            break;

        case 'country_code':
            filters.querySelector('#country_code').checked = true;
            filters.querySelector('#country_code_value').disabled = false;
            filters.querySelector('#country_code_value').value = value;
            break;
    }
}





// Make radio filters for #creator_value inputs work
const radios = filters.querySelectorAll('input[name=creator]');
[...radios].map(radio => {
    radio.addEventListener('change', () => {
        if (radio.checked && radio.id != 'creator_empty') {
            // shows #creator_value input of filter option: #radio.id
            showOnlySpecifiedCreatorInput(radio.id + '_value'); 
        } else {
            // hides all filter: #creator_value, inputs
            showOnlySpecifiedCreatorInput();
        }
    });
});



// Toggle country code input's active state
let checkbox = filters.querySelector('#country_code');
checkbox.addEventListener('change', () => {
    if (checkbox.checked) {
        filters.querySelector('#country_code_value').disabled = false;
    } else {
        filters.querySelector('#country_code_value').disabled = true;
    }
});
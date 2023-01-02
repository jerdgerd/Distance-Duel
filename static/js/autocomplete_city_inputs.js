// Set up the autocomplete functionality
$('#cityName1').autocomplete({
  // The source of the autocomplete suggestions
  source: function(request, response) {
    // Filter the list of cities based on the term being typed in the input field
    var filtered_cities = cities.filter(function(city) {
      return city[1].toLowerCase().indexOf(request.term.toLowerCase()) > -1;
    });
    response(filtered_cities.map(function(city) {
      return {
	label: city[1] + ', ' + city[7] +', ' + city[4] + ' - Population: ' + city[6], // The label to display in the suggestion list
        value: city[1] + ', ' + city[7] +', ' + city[4], // The value to set in the input field when a suggestion is selected
	city_id: city[0], // Additional fields to use in the event handler 
        population: city[6], // Additional fields to use in the event handler
        country: city[4]
      };
    }));
  },
  // The minimum number of characters required before the autocomplete functionality is triggered
  minLength: 3,
  // The element to display the autocomplete results in
  appendTo: '#cityName1-autocomplete-results',
  // Set the value of the hidden field to the city_id value when a suggestion is selected
  select: function(event, ui) {
    $('#hiddenCityId1').val(ui.item.city_id);
  }
});

// Set up the autocomplete functionality
$('#cityName2').autocomplete({
  // The source of the autocomplete suggestions
  source: function(request, response) {
    // Filter the list of cities based on the term being typed in the input field
    var filtered_cities = cities.filter(function(city) {
      return city[1].toLowerCase().indexOf(request.term.toLowerCase()) > -1;
    });
    response(filtered_cities.map(function(city) {
      return {
	label: city[1] + ', ' + city[7] +', ' + city[4] + ' - Population: ' + city[6], // The label to display in the suggestion list
        value: city[1] + ', ' + city[7] +', ' + city[4], // The value to set in the input field when a suggestion is selected
	city_id: city[0], // Additional fields to use in the event handler 
        population: city[6], // Additional fields to use in the event handler
        country: city[4]
      };
    }));
  },
  // The minimum number of characters required before the autocomplete functionality is triggered
  minLength: 3,
  // The element to display the autocomplete results in
  appendTo: '#cityName2-autocomplete-results',
  // Set the value of the hidden field to the city_id value when a suggestion is selected
  select: function(event, ui) {
    $('#hiddenCityId2').val(ui.item.city_id);
  }
});

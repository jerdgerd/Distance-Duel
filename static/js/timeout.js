const form = document.querySelector('form');
const timeoutCounter = document.querySelector('.timeout-counter');

// Get the timeout duration from the data-timeout attribute of the script tag
const timeoutDurationSec = document.querySelector('script[src="/static/js/timeout.js"]').dataset.timeout;
const timeRemainingField = document.querySelector('#time-remaining-id');

console.log(timeoutDurationSec)
console.log(timeRemainingField.value)

// Set the initial value of the timeout counter
timeoutCounter.textContent = timeoutDurationSec;
form.elements['time_remaining'].value = timeoutDurationSec;

if (timeoutDurationSec !== -1) {
    const timeoutDuration = document.querySelector('script[src="/static/js/timeout.js"]').dataset.timeout * 1000;
    // Set a timeout
    const timeoutId = setTimeout(() => {
      // If the form has not been submitted yet
      if (!form.hasAttribute('data-submitted')) {
        // Set the form values to your pre-programmed inputs
        form.elements['hiddenCityId1'].value = '00000';
        form.elements['hiddenCityId2'].value = '00000';
        form.elements['time_remaining'].value = '0';
    
        // Submit the form
        form.submit();
      }
    }, timeoutDuration);
    
    // Update the timeout counter every second
    setInterval(() => {
      // Decrement the timeout counter
      timeoutCounter.textContent -= 1;
      timeRemainingField.value -= 1;
    }, 1000);
    
    // Add a listener to the form's submit event
    form.addEventListener('submit', () => {
      // Clear the timeout
      clearTimeout(timeoutId);
    
      // Set a custom attribute to indicate that the form has been submitted
      form.setAttribute('data-submitted', true);
    });
}

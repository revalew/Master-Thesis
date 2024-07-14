var tempOpts = {
	angle: 0, // The span of the gauge arc
	lineWidth: 0.2, // The line thickness
	radiusScale: 0.97, // Relative radius
	pointer: {
		length: 0.41, // // Relative to gauge radius
		strokeWidth: 0.082, // The thickness
		color: '#000000', // Fill color
	},
	limitMax: true, // If false, max value increases automatically if value > maxValue
	limitMin: true, // If true, the min value of the gauge will be fixed
	highDpiSupport: true, // High resolution support
	staticLabels: {
		font: '10px sans-serif', // Specifies font
		labels: [0, 5, 10, 15, 20, 25, 30, 35, 40], // Print labels at these values
		color: '#000000', // Optional: Label text color
		fractionDigits: 0, // Optional: Numerical precision. 0=round off.
	},
	staticZones: [
		{ strokeStyle: '#0000a0', min: 0, max: 15, height: 1 }, // blue
		{ strokeStyle: '#30B32D', min: 15, max: 25, height: 1.4 }, // Green
		{ strokeStyle: '#F03E3E', min: 25, max: 40, height: 1 }, // Red
	],
	renderTicks: {
		divisions: 8,
		divWidth: 1.1,
		divLength: 0.7,
		divColor: '#333333',
		subDivisions: 5,
		subLength: 0.5,
		subWidth: 0.6,
		subColor: '#666666',
	},
}
var tempTarget = document.getElementById('tempGauge')
var tempGauge = new Gauge(tempTarget).setOptions(tempOpts)
tempGauge.maxValue = 40
tempGauge.minValue = 0
tempGauge.animationSpeed = 60
tempGauge.set(0)

let gatherDataAjaxRunning = false

async function gatherData() {
	// stop overlapping requests
	if (gatherDataAjaxRunning) return

	gatherDataAjaxRunning = true
	let postData = {
		action: 'readData',
	}

	try {
		let response = await fetch('/api', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify(postData),
		})

		if (response.ok) {
			let data = await response.json()

			// handle temp gauge
			let temp = parseFloat(data.temp_value)
			tempGauge.set(temp) // Assuming tempGauge is defined elsewhere
			document.getElementById('tempValue').innerHTML = temp.toFixed(1)
			document.getElementById('tempValue').classList.remove('bg-success', 'bg-warning', 'bg-danger')
			if (temp <= 15) {
				document.getElementById('tempValue').classList.add('bg-primary')
			} else if (temp <= 25) {
				document.getElementById('tempValue').classList.add('bg-success')
			} else {
				document.getElementById('tempValue').classList.add('bg-danger')
			}

			// handle rgb leds
			let colour = data.onboard_led ? 'rgb(0, 255, 0)' : 'rgb(255, 0, 0)'
			document.getElementById('onboard_led').style.backgroundColor = colour
		} else {
			console.log('Network response was not ok.')
		}
	} catch (error) {
		console.log('Fetch error:', error)
	} finally {
		// allow next data gather call
		gatherDataAjaxRunning = false
	}
}

async function setLedColour(colour) {
	let postData = {
		action: 'setLedColour',
		colour: colour,
	}

	try {
		let response = await fetch('/api', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify(postData),
		})

		if (response.ok) {
			let data = await response.json()
			console.log(data)
			if (data.status == 'OK') {
				// set colour from json array
				let colour = data.onboard_led ? 'rgb(0, 255, 0)' : 'rgb(255, 0, 0)'
				document.getElementById('onboard_led').style.backgroundColor = colour
			} else {
				alert('Error setting led colour')
			}
		} else {
			console.log('Network response was not ok.')
		}
	} catch (error) {
		console.log('Fetch error:', error)
	}
}

var dataTimer
document.addEventListener('DOMContentLoaded', function () {
	dataTimer = setInterval(gatherData, 1000) // call data every 1 second
})

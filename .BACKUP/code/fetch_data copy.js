// Initialize the temp gauge at startup
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
		labels: [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60], // Print labels at these values
		color: '#000000', // Optional: Label text color
		fractionDigits: 0, // Optional: Numerical precision. 0=round off.
	},
	staticZones: [
		{ strokeStyle: '#0000a0', min: 0, max: 20, height: 1 }, // blue
		{ strokeStyle: '#30B32D', min: 20, max: 40, height: 1.4 }, // Green
		{ strokeStyle: '#F03E3E', min: 40, max: 60, height: 1 }, // Red
	],
	renderTicks: {
		divisions: 12,
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
tempGauge.maxValue = 60
tempGauge.minValue = 0
tempGauge.animationSpeed = 60
tempGauge.set(0)
let gatherDataAjaxRunning = false
async function gatherData() {
	if (gatherDataAjaxRunning) return
	gatherDataAjaxRunning = true
	let postData = { action: 'readData' }
	try {
		let response = await fetch('/api', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(postData),
		})
		if (response.ok) {
			let data = await response.json()
			let temp = parseFloat(data.temp_value)
			tempGauge.set(temp)
			document.getElementById('tempValue').innerHTML = temp.toFixed(1)
			let colour = data.onboard_led ? 'rgb(0, 255, 0)' : 'rgb(255, 0, 0)'
			document.getElementById('onboard_led').style.backgroundColor = colour
		} else {
			console.log('Network response was not ok.')
		}
	} catch (error) {
		console.log('Fetch error:', error)
	} finally {
		gatherDataAjaxRunning = false
	}
}
let gatherIMUDataAjaxRunning = false
async function gatherIMUData() {
	if (gatherIMUDataAjaxRunning) return
	gatherIMUDataAjaxRunning = true
	let postData = { action: 'readIMU' }
	try {
		let response = await fetch('/api', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(postData),
		})
		if (response.ok) {
			let data = await response.json()
			let accelX = parseFloat(data.acceleration.X)
			document.getElementById('accelX').innerHTML = accelX.toFixed(2)
			let accelY = parseFloat(data.acceleration.Y)
			document.getElementById('accelY').innerHTML = accelY.toFixed(2)
			let accelZ = parseFloat(data.acceleration.Z)
			document.getElementById('accelZ').innerHTML = accelZ.toFixed(2)
			let gyroX = parseFloat(data.gyro.X)
			document.getElementById('gyroX').innerHTML = gyroX.toFixed(2)
			let gyroY = parseFloat(data.gyro.Y)
			document.getElementById('gyroY').innerHTML = gyroY.toFixed(2)
			let gyroZ = parseFloat(data.gyro.Z)
			document.getElementById('gyroZ').innerHTML = gyroZ.toFixed(2)
			let magnetX = parseFloat(data.magnetic.X)
			document.getElementById('magnetX').innerHTML = magnetX.toFixed(2)
			let magnetY = parseFloat(data.magnetic.Y)
			document.getElementById('magnetY').innerHTML = magnetY.toFixed(2)
			let magnetZ = parseFloat(data.magnetic.Z)
			document.getElementById('magnetZ').innerHTML = magnetZ.toFixed(2)
		} else {
			console.log('Network response was not ok.')
		}
	} catch (error) {
		console.log('Fetch error:', error)
	} finally {
		gatherIMUDataAjaxRunning = false
	}
}
let setLedAjaxRunning = false
async function setLedColour(colour) {
	if (setLedAjaxRunning) return
	setLedAjaxRunning = true
	let postData = { action: 'setLedColour', colour: colour }
	try {
		let response = await fetch('/api', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(postData),
		})
		if (response.ok) {
			let data = await response.json()
			if (data.status == 'OK') {
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
	} finally {
		setLedAjaxRunning = false
	}
}
document.addEventListener('DOMContentLoaded', function () {
	setInterval(gatherData, 500)
})
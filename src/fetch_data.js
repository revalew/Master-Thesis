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
		console.log(response)
		if (response.ok) {
			let data = await response.json()
			let temp = parseFloat(data.temp_value)
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
	let interval = 700
	setInterval(gatherData, interval)
	setInterval(gatherIMUData, interval)
})

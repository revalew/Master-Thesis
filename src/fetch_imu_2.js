let gatherIMUDataAjaxRunning_2=false;async function gatherIMUData_2() {if (gatherIMUDataAjaxRunning_2) return;gatherIMUDataAjaxRunning_2=true;let postData={ action: 'WavReadIMU' };try {let response=await fetch('/api',{method: 'POST',headers: { 'Content-Type': 'application/json' },body: JSON.stringify(postData),});if (response.ok) {let data=await response.json();let accelX=parseFloat(data.acceleration.X);document.getElementById('accelX_2').innerHTML=accelX.toFixed(2);let accelY=parseFloat(data.acceleration.Y);document.getElementById('accelY_2').innerHTML=accelY.toFixed(2);let accelZ=parseFloat(data.acceleration.Z);document.getElementById('accelZ_2').innerHTML=accelZ.toFixed(2);let gyroX=parseFloat(data.gyro.X);document.getElementById('gyroX_2').innerHTML=gyroX.toFixed(2);let gyroY=parseFloat(data.gyro.Y);document.getElementById('gyroY_2').innerHTML=gyroY.toFixed(2);let gyroZ=parseFloat(data.gyro.Z);document.getElementById('gyroZ_2').innerHTML=gyroZ.toFixed(2);let magnetX=parseFloat(data.magnetic.X);document.getElementById('magnetX_2').innerHTML=magnetX.toFixed(2);let magnetY=parseFloat(data.magnetic.Y);document.getElementById('magnetY_2').innerHTML=magnetY.toFixed(2);let magnetZ=parseFloat(data.magnetic.Z);document.getElementById('magnetZ_2').innerHTML=magnetZ.toFixed(2);} else {console.log('Network response was not ok.');}} catch (error) {console.log('Fetch error:',error);} finally {gatherIMUDataAjaxRunning_2=false;}};
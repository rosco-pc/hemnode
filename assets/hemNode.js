const base="http://homPie:8000"

window.onload = function showDevices() {
  devices = document.getElementById('devices');
  getDevices()
}

function createDeviceTable(devList) {
  console.log(devList)
  devList.forEach(device =>{
    row = document.createElement('tr');
    c1 = document.createElement('td');
    row.append(device.name, c1);
    btn = document.createElement('button');
    btn.classList.add("fa");
    btn.classList.add("fa-lightbulb");
    btn.classList.add("switch");
    btn.classList.add(device.state);
    btn.addEventListener("click", event => { toggleSwitch(event.target, device.deviceId); }, false)
    c2 = document.createElement('td');
    c2.append(btn);
    row.append(c2);
    devices.append(row);
  })
}

function getDevices() {
  request = fetch(base+"/hemnode/devices")
    .then(response => response.json())
    .then(data => createDeviceTable(data))
    .catch(error => {
      console.error(error);
    });
}

function toggleSwitch(elem, deviceId) {
  oldState = elem.classList.contains("Off")?"Off":"On"
  state = (oldState=="Off")?"On":"Off" // Togle state
  request = fetch(`${base}/hemnode/device/${deviceId}/${state}`,{"method":"put"})
    .then (response => response.json())
    .then (data => {
      console.log(data)
      if (state === data.newState) {
        elem.classList.remove(oldState)
        elem.classList.add(state)
    }})
    .catch(error => {
      console.log.error(error)
    })
  
}

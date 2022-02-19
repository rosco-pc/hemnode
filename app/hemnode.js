// Constants
const debug=false
const Actions = ['Off', 'On', 'Random']
const Days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const selected = ['Device', 'Day','Sun ON event','Sun OFF event'];
const sunevents = ["","nauticalDawn","dawn","nadir","sunrise","sunriseEnd",
                   "goldenHourEnd","solarNoon","goldenHour","sunsetStart",
                   "sunset","dusk","nauticalDusk","night","nightEnd"]

function findDevice(devs, id){
    for (let dev in devs) {
        if (devs[dev].id-1 == id)
            return dev;
    }
    return undefined;
}

// Get saved data
let schedule = flow.get('schedule');
let dev = flow.get('device');
let devId = schedule[dev].id-1;

let now = new Date();
let day = Number.isInteger(flow.get('day'))?flow.get('day'):now.getDay();
let selector = Number.isInteger(flow.get('selector'))?flow.get('selector'):now.getHours();
let hour = selector<24?(day*24)+selector:0;    // Get index into schedule
let action = schedule[dev].day[hour];

let sun_on = 0
let sun_off = 7
let sunon = schedule[dev].sunevent[sun_on+day];
let sunoff = schedule[dev].sunevent[sun_off+day];

let dLen = Object.keys(schedule).length;
let sLen = sunevents.length;
let aLen = Actions.length;

// Handle requested action
let payload = msg.payload;
if (debug) node.warn(`msg: ${JSON.stringify(msg)}`)
if (debug) node.warn(`${payload}: ${dev}, ${action}, ${selector}`);
if (!payload || msg.redraw) return
  
msg = {};
save = false;

switch (payload) {
  case '':
    node.warn('Refresh page')
    flow.set('day',day)
    flow.set('selector',selector )
    msg.redraw = true
    break
  case "u":
    save = true
    if ((selector < 24)) {
      schedule[dev].day[hour] = (action+1)%aLen;        // Next Hour action 
      //msg.status = Actions[schedule[devId][hour]];
    } else if (selector == 24) {
      devId = (devId+1)%dLen;                         // Next Device
      node.log('Next device: '+devId)
      //msg.status = "Next Device"; 
    } else if (selector == 25) {
      day = (day+1)%7;                                // Next Day
      //msg.status = "Next Day"; 
    } else if (selector == 26) {
      schedule[dev].sunevent[sun_on+day] = (sunon+1)%sLen;      // Next Sun ON Eevent
      //msg.status = "Next Sun Event"; 
    } else if (selector == 27) {
      schedule[dev].sunevent[sun_off+day] = (sunoff+1)%sLen;     // Next SUn OFF Event
      //msg.status = "Next Sun Event";
    }
    break;
  case "d":
    save = true
    if (selector < 24) {
      schedule[dev].day[hour] = ((action-1)+aLen)%aLen; // Previous Hour action
      //msg.status = Actions[schedule[devId][hour]];
    } else if (selector == 24) {
      devId = ((devId-1)+dLen)%dLen;                  // Previous Device
      //msg.status = "Previous Device";
    } else if (selector == 25) { 
      day = ((day-1)+7)%7;                            // Previous day
      //msg.status = "Previous day"; 
    } else if (selector == 26) {
      schedule[dev].sunevent[sun_on+day] = ((sunon-1)+sLen)%sLen;  // Previous Sun On Event
      //msg.status = "Previous Sun On Event"; 
    } else if (selector == 27) {
      schedule[dev].sunevent[sun_off+day] = ((sunoff-1)+sLen)%sLen; // Previous Sun Off Event
      //msg.status = "Previous Sun Off Event";
    }
    break;
  case 'c':
    save = true
    //node.log('Selector: '+selector)
    if (selector < 24) {                            // Copy action to next hour
      schedule[dev].day[(hour+1)%168] = schedule[dev].day[hour];
      selector = (selector+1)%24;                   // Update selector        
      if (!selector) day = (day+1)%7                // Update day if roillover 
      msg.status = "Action copied to the next hour";
    } else if (selector == 25) {                    // Copy schedule to next day
      let next_day = ((day+1)%7)
      for (let a = 0; a < 24; a++)
        schedule[dev].day[next_day*24+a] = schedule[dev].day[(day*24)+a];
      schedule[dev].sunevent[sun_on+next_day] = schedule[dev].sunevent[sun_on+day]
      schedule[dev].sunevent[sun_off+next_day] = schedule[dev].sunevent[sun_off+day]
      day = next_day;                           // Next day
      msg.status = "Schedule copied to" + Days[day];
    } else {
      msg.status="Action not implemented";
    }
    break;
  case 's':
    msg.payload = JSON.stringify(schedule);
    node.send([null, msg, null]);                 // Save and continue
    msg.payload = '';
    msg.status = "Saved Settings";
    break;
  case 'q':
    msg.payload = '';
    msg.status = "Changes canceled";
    return [null, null, msg];                     // Read old schedule
  default:
    //node.log('default: '+payload+' '+parseInt(payload))
    selector = parseInt(payload);
    flow.set('selector', selector)
    if (selector < 24) {
      msg.status = "Changing Hour " + selector;
    } else {
      msg.status = 'Changing ' + selected[selector-24];
    }
}

// Save data if there was a payload
dev = findDevice(schedule,devId);
if (save) {
  //node.warn('Saving data')
  flow.set('schedule', schedule);
  flow.set('device',dev);
  flow.set('day', day);
  flow.set('selector', selector)
}

// Send data to GUI
msg.schedule = schedule[dev];            // Just the current devices data
msg.day = Days[day]; //
msg.device = dev;
msg.selector = selector;

if (debug) node.log('sending msg')
if (debug) node.log('msg: '+JSON.stringify(msg))

return [msg, null, null];



function setAction(action) {
  
function toggleSwitch(device) {
  state = button.hasClass("On")?"Off":"On"
  button.toggleClass("Off")
  button.toggleCalss("On")
  request = new Request(`https://192.168.11.10/hemnode/{device}/{state}`, 
                        {method: 'POST'});
  state  = send(request)
  
function send(request) {
  fetch(request)
    .then(response => {
      if (response.status === 200) {
        return response.json();
      } else {
        throw new Error('Something went wrong on api server!');
      }
    })
    .then(response => {
      console.debug(response);
      // ...
    }).catch(error => {
      console.error(error);
    });
}
request = new Request('https://192.168.11.10/hemnode/devices', {method: 'GET'});

try {
  devices = send(request)
  foreach (device in devices) {
    // <div>
    //   <span>{device.name'}</span>
    //   <button id='"switch"+{device.id}' onclick="toggleSwitch({device.id})><i></i></button>
    //   <button onclick="schedule({device})"><i></i></button>
    // </div>
  }

  div('switches).addClass("show")
} catch {}

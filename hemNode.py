#!/usr/bin/env python3

from fastapi import FastAPI, Body, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import logging

import asyncio
import json
import time

import sqlite3
from influxdb import InfluxDBClient

import tellcore.telldus as td
import tellcore.constants as const

from pydantic import BaseModel
from datetime import date, datetime
from typing import Any, Dict, AnyStr, List, Union, Optional
from enum import IntEnum

# data model
# Generic JSON object
JSONObject = Dict[Any, Any]
JSONArray = List[Any]
JSONStructure = Union[JSONArray, JSONObject]

# Device model 
class Device(BaseModel):
  deviceId: str
  name: str
  state: str
  
# Schedule model
class Actions(IntEnum):
  off = 0
  on = 1
  rnd = 2
  
class sunEvent(IntEnum):
  off = 0
  astronomical_dawn = 1
  nautical_dawn = 2
  dawn = 3
  sunrise = 4
  solar_noon = 5
  dusk = 6
  nautical_dusk = 7
  astronomical_dusk = 8
  night = 9
  

class Schedule(BaseModel):
  scheduleId: int
  device: Device
  start: Union[datetime, sunEvent]
  end: Optional[datetime] = None
  repeat: str
  action: Actions


core = None                                                     # Telldus API
client = None                                                   # Sensor time series DB  
logger = None                                                   # Uvicorn logger instance

# schedule DB
# Create schedule table if needed
conn = sqlite3.connect('/var/db/hemnode.db')                            # connect to DB for schedule info
db = conn.cursor()
db.execute('CREATE TABLE IF NOT EXISTS schedule (id PRIMARY KEY, schedule)')
db.execute('CREATE TABLE IF NOT EXISTS sensors (id PRIMARY KEY, name, data)')        

# TO be replaced with logic to detect sensors, then added to SQLITE table
sensor_id = {'167': 'computer room',
             '199': 'down stairs',
             '135': 'outside - back'}
sensor_keys = ['protocol', 'model', 'id', 'dataType', 
               'value', 'timestamp', 'cid']
data_type = {1: 'temperature',
             2: 'humidity'}
    

# create server app    
app = FastAPI()  
app.mount("/hemnode/assets", StaticFiles(directory="assets"), name="assets")

def sensor(*values):
  sensor_data = dict(zip(sensor_keys, values))

  if sensor_data['model']!='temperaturehumidity':                       # only store temperature and humidity
    # TODO: add logic for other events (like bell/proximity)
    return
  _store(sensor_data)
  
def _store(data):
  ts = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(data['timestamp']))
  dt = data_type[data['dataType']]
  request = [{"measurement": dt,
              "tags": {"place": sensor_id[data['id']]},
              "time": ts,
              "fields": { dt: data['value']}
            }]
  print("influxDB:",client)
  if client is not None:
    client.write_points(request)
    
def telldus_events(data, controller_id, cid):
  sensor_data = dict([x.split(':') for x in data[:-1].split(';')])      # remove last ';'
  if sensor_data['id'] in sensor_id:
    _store_raw (sensor_data)
  
def _store_raw(data):
  global client
  now = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
  if data['model']!='temperaturehumidity':                       # only store temperature and humidity
    # TODO: add logic for other events (like bell/proximity)
    return

  request = [{"measurement": "humidity",
              "tags": {"place": sensor_id[data['id']]},
              "time": now,
              "fields": {"humidity": data['humidity']}
              },
              {"measurement": "temperature",
              "tags": {"place": sensor_id[data['id']]},
              "time": now,
              "fields": {"temperature": data['temp']}
              }]
  if client is not None:
    try:
      client.write_points(request)
    except:
      client = None
              
def _findDevice(device, devices):
  ''' find telldus device based on id or name
  '''
  for d in devices:
    if str(d.id) == device or d.name == device:
      return d
  return None
  
def _getDevice(device):
  return {"deviceId": device.id, 
          "name": device.name,
          "state": _getState(device),
          "schedule": _getSchedule(device.id)
         }
         
cmdAction = {const.TELLSTICK_TURNON: 'On',                              # telldus action table
             const.TELLSTICK_TURNOFF: 'Off',
             const.TELLSTICK_DIM: 'Dimmed {}'
            }
            
def _getState(device):
  ''' find device state
  '''
  cmd = device.last_sent_command(const.TELLSTICK_TURNON
                                 | const.TELLSTICK_TURNOFF
                                 | const.TELLSTICK_DIM)
  try:
    state = cmdAction[cmd]
    if '{' in state:
      state.format(device.last_sent_value())
  except KeyError:
    state = "Unknown: {}".format(cmd)
  return state
  
def _getSchedule(device_id):
  result = db.execute('SELECT schedule FROM schedule WHERE id=?',(device_id,))
  data = result.fetchone()
  #print(data)
  if data is not None:                                                # get save schedule
    print('Found: {}'.format(data[0]))
    schedule = json.loads(data[0])
  else:                                                               # no schedule saved, use default
    schedule = [{"scheduleId":0,
                 "deviceId":0, 
                 "start": datetime.now(),
                 "end":"",
                 "repeat":"daily",
                 "action":0}
               ]
  return schedule
  
@app.get("/hemnode/devices", response_model=List[Device])
async def getDevices():
  devices = []
  for d in core.devices():
    device = _getDevice(d)
    devices.append(Device(**device))
  return devices
    
@app.get("/hemnode/device/{device_id}", response_model=Device)
async def getState(device_id):
  d = _findDevice(device_id, core.devices())
  if d is None:
    raise HTTPException(status_code=404, detail="Device not found")

  device = _getDevice(d)
  return Device(**device)

@app.put("/hemnode/device/{device_id}/{state}")
async def setState(device_id, state):
  d = _findDevice(device_id, core.devices())
  if d is None:
    raise HTTPException(status_code=404, detail="Device not found")
  
  if state == 'On':
    logger.info('Turning {} - {}'.format(state, d.name))
    d.turn_on()
  elif state == 'Off':
    logger.info('Turning off - {}'.format(d.name))
    d.turn_off()
  else:
    raise HTTPException(status_code=404, detail="Unknown state")

  return {"newState": state}

@app.get("/hemnode/schedule/{device_id}", response_model=List[Schedule])
async def getSchedule(device_id):
  if _findDevice(device_id,core.devices()) is None:                     # Check if valid device
    raise HTTPException(status_code=404, detail="Device not found")
  schedule = _getSchedule(device_id)
  return Schedule(**schedule)

@app.post("/hemnode/schedule/{device_id}", status_code=201)
async def setSchedule(device_id, schedule: Schedule):
  if _findDevice(device_id,core.devices()) is None:                     # Check if valid device
    raise HTTPException(status_code=404, detail="Device not found")

  try:
    schedule = json.dumps(schedule.dict())
    db.execute('''INSERT INTO schedule(id, schedule) VALUES(?,?) 
                  ON CONFLICT (id) DO UPDATE SET schedule=?''',
               (device_id, schedule, schedule))
    conn.commit()
  except:
    raise HTTPException(status_code=404, detail="Schedule could not be updated")
  
  return 

@app.get("/hemnode", response_class=HTMLResponse)
async def getHome():
  return open("assets/hemNode.html",'r').read()


@app.on_event("startup")
async def startup_event():
  global core, client, logger
  logger = logging.getLogger("uvicorn.error")
  try: 
    client = InfluxDBClient(host='192.168.11.10', port=8086)                # connect to influxDB on home server
    client.switch_database('sensors')                                       # select correct DB
  except:
    logger.error("Can not reach influxDB at 192.168.11.10:8086")

  loop = asyncio.get_running_loop()                     # get fastapi asyncio loop
  dispatcher = td.AsyncioCallbackDispatcher(loop)       # create dispatcher
  core = td.TelldusCore(callback_dispatcher=dispatcher) # get tellcore                  
  core.register_raw_device_event(telldus_events)        # get raw event data
  #core.register_sensor_event(sensor)                    # get sensor event data


uvicorn.run(app, host="0.0.0.0", port=8000)

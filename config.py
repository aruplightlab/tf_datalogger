from os.path import join

HOST = "localhost"
PORT = 4223
UID = "xZh" # Change XYZ to the UID of your Color Bricklet "oy6"
REDBRICK_UID = "2QnPSH"
MASTERBRICK_UID = "6e8Qg4"
ROOTDIR = "/home/tf"
FILENAMEINST = join(ROOTDIR,"dataINST.csv")
FILENAMEAVG = join(ROOTDIR,"dataAVG.csv")
INTERVAL = 5 # Instantaneous interval in seconds
INTEGRATIONTIME = 20 # Integration interval in seconds

useInflux = False
INFLUXserver = 'put here address of influxdb server'
INFLUXport =  '8086'
INFLUXdbname = 'put here dbname'
INFLUXdbuser = 'put here dbuser'
INFLUXdbuser_password = 'put here dbpassword'

SENSORNAME = 'colour_temperature_sensor'

try:
    config_module = __import__('config_local',
                               globals(), locals())

    for setting in dir(config_module):
        locals()[setting] = getattr(config_module, setting)
except Exception:
    pass




#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from urllib3.exceptions import InsecureRequestWarning
import requests
import time
import _thread
from datetime import datetime, timedelta
from tzlocal import get_localzone
import threading
import socket
import os
import subprocess
import uuid
import ssl
import sys
import re
import json
import os.path
import argparse
from time import time, sleep, localtime, strftime
from collections import OrderedDict
from colorama import init as colorama_init
from colorama import Fore, Back, Style
from configparser import ConfigParser
from unidecode import unidecode
import paho.mqtt.client as mqtt
import sdnotify
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE, SIG_DFL)

apt_available = True
try:
    import apt
except ImportError:
    apt_available = False

script_version = "1.9.x"
script_name = 'ISP-RPi-mqtt-daemon.py'
script_info = '{} v{}'.format(script_name, script_version)
project_name = 'RPi Reporter MQTT2HA Daemon'
project_url = 'https://github.com/ironsheep/RPi-Reporter-MQTT2HA-Daemon'

# we'll use this throughout
local_tz = get_localzone()

# turn off insecure connection warnings (our KZ0Q site has bad certs)
# REF: https://www.geeksforgeeks.org/how-to-disable-security-certificate-checks-for-requests-in-python/
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# TODO:
#  - add announcement of free-space and temperatore endpoints

if False:
    # will be caught by python 2.7 to be illegal syntax
    print_line(
        'Sorry, this script requires a python3 runtime environment.', file=sys.stderr)
    os._exit(1)

# Argparse
opt_debug = False
opt_verbose = False

# Systemd Service Notifications - https://github.com/bb4242/sdnotify
sd_notifier = sdnotify.SystemdNotifier()

# Logging function


def print_line(text, error=False, warning=False, info=False, verbose=False, debug=False, console=True, sd_notify=False):
    timestamp = strftime('%Y-%m-%d %H:%M:%S', localtime())
    if (sd_notify):
        text = '* NOTIFY: {}'.format(text)
    if console:
        if error:
            print(Fore.RED + Style.BRIGHT + '[{}] '.format(
                timestamp) + Style.RESET_ALL + '{}'.format(text) + Style.RESET_ALL, file=sys.stderr)
        elif warning:
            print(Fore.YELLOW + '[{}] '.format(timestamp) +
                  Style.RESET_ALL + '{}'.format(text) + Style.RESET_ALL)
        elif info or verbose:
            if opt_verbose:
                print(Fore.GREEN + '[{}] '.format(timestamp) +
                      Fore.YELLOW + '- ' + '{}'.format(text) + Style.RESET_ALL)
        elif debug:
            if opt_debug:
                print(Fore.CYAN + '[{}] '.format(timestamp) +
                      '- (DBG): ' + '{}'.format(text) + Style.RESET_ALL)
        else:
            print(Fore.GREEN + '[{}] '.format(timestamp) +
                  Style.RESET_ALL + '{}'.format(text) + Style.RESET_ALL)

    timestamp_sd = strftime('%b %d %H:%M:%S', localtime())
    if sd_notify:
        sd_notifier.notify(
            'STATUS={} - {}.'.format(timestamp_sd, unidecode(text)))

# Identifier cleanup


def clean_identifier(name):
    clean = name.strip()
    for this, that in [
        [' ', '-'],
        ['ä', 'ae'],
        ['Ä', 'Ae'],
        ['ö', 'oe'],
        ['Ö', 'Oe'],
        ['ü', 'ue'],
        ['Ü', 'Ue'],
            ['ß', 'ss']]:
        clean = clean.replace(this, that)
    clean = unidecode(clean)
    return clean


# Argparse
parser = argparse.ArgumentParser(
    description=project_name, epilog='For further details see: ' + project_url)
parser.add_argument("-v", "--verbose",
                    help="increase output verbosity", action="store_true")
parser.add_argument(
    "-d", "--debug", help="show debug output", action="store_true")
parser.add_argument(
    "-s", "--stall", help="TEST: report only the first time", action="store_true")
parser.add_argument("-c", '--config_dir',
                    help='set directory where config.ini is located', default=sys.path[0])
parse_args = parser.parse_args()

config_dir = parse_args.config_dir
opt_debug = parse_args.debug
opt_verbose = parse_args.verbose
opt_stall = parse_args.stall

print_line('--------------------------------------------------------------------', debug=True)
print_line(script_info, info=True)
if opt_verbose:
    print_line('Verbose enabled', info=True)
if opt_debug:
    print_line('Debug enabled', debug=True)
if opt_stall:
    print_line('TEST: Stall (no-re-reporting) enabled', debug=True)

# -----------------------------------------------------------------------------
#  MQTT handlers
# -----------------------------------------------------------------------------

# Eclipse Paho callbacks - http://www.eclipse.org/paho/clients/python/docs/#callbacks

mqtt_client_connected = False
print_line(
    '* init mqtt_client_connected=[{}]'.format(mqtt_client_connected), debug=True)
mqtt_client_should_attempt_reconnect = True


def on_connect(client, userdata, flags, rc):
    global mqtt_client_connected
    if rc == 0:
        print_line('* MQTT connection established', console=True, sd_notify=True)
        print_line('')  # blank line?!
        # _thread.start_new_thread(afterMQTTConnect, ())
        mqtt_client_connected = True
        print_line('on_connect() mqtt_client_connected=[{}]'.format(
            mqtt_client_connected), debug=True)

        # -------------------------------------------------------------------------
        # Commands Subscription
        if (len(commands) > 0):
            print_line('MQTT subscription to {}/+ enabled'.format(command_base_topic), console=True, sd_notify=True)
            mqtt_client.subscribe('{}/+'.format(command_base_topic))
        else:
            print_line('MQTT subscripton to {}/+ disabled'.format(command_base_topic), console=True, sd_notify=True)
        # -------------------------------------------------------------------------

    else:
        print_line('! Connection error with result code {} - {}'.format(str(rc),
                   mqtt.connack_string(rc)), error=True)
        print_line('MQTT Connection error with result code {} - {}'.format(str(rc),
                   mqtt.connack_string(rc)), error=True, sd_notify=True)
        # technically NOT useful but readying possible new shape...
        mqtt_client_connected = False
        print_line('on_connect() mqtt_client_connected=[{}]'.format(
            mqtt_client_connected), debug=True, error=True)
        # kill main thread
        os._exit(1)


def on_disconnect(client, userdata, mid):
    global mqtt_client_connected
    mqtt_client_connected = False
    print_line('* MQTT connection lost', console=True, sd_notify=True)
    print_line('on_disconnect() mqtt_client_connected=[{}]'.format(
        mqtt_client_connected), debug=True)
    pass


def on_publish(client, userdata, mid):
    # print_line('* Data successfully published.')
    pass

# -----------------------------------------------------------------------------
# Commands - MQTT Subscription Callback
# -----------------------------------------------------------------------------
# Command catalog


def on_subscribe(client, userdata, mid, granted_qos):
    print_line('on_subscribe() - {} - {}'.format(str(mid), str(granted_qos)), debug=True, sd_notify=True)


shell_cmd_fspec = ''


def on_message(client, userdata, message):
    global shell_cmd_fspec
    if shell_cmd_fspec == '':
        shell_cmd_fspec = getShellCmd()
        if shell_cmd_fspec == '':
            print_line('* Failed to locate shell Command!', error=True)
            # kill main thread
            os._exit(1)

    decoded_payload = message.payload.decode('utf-8')
    command = message.topic.split('/')[-1]
    print_line('on_message() Topic=[{}] payload=[{}] command=[{}]'.format(
        message.topic, message.payload, command), console=True, sd_notify=True, debug=True)

    if command != 'status':
        if command in commands:
            print_line('- Command "{}" Received - Run {} {} -'.format(command,
                       commands[command], decoded_payload), console=True, debug=True)
            pHandle = subprocess.Popen([shell_cmd_fspec, "-c", commands[command].format(decoded_payload)])
            output, errors = pHandle.communicate()
            if errors or pHandle.returncode:
                print_line('- Command exec says: errors=[{}]'.format(errors or output), console=True, debug=True)
        else:
            print_line('* Invalid Command received.', error=True)


# -----------------------------------------------------------------------------
# Load configuration file
config = ConfigParser(delimiters=(
    '=', ), inline_comment_prefixes=('#'), interpolation=None)
config.optionxform = str
try:
    with open(os.path.join(config_dir, 'config.ini')) as config_file:
        config.read_file(config_file)
except IOError:
    print_line('No configuration file "config.ini"',
               error=True, sd_notify=True)
    sys.exit(1)

daemon_enabled = config['Daemon'].getboolean('enabled', True)

# This script uses a flag file containing a date/timestamp of when the system was last updated
default_update_flag_filespec = '/home/pi/bin/lastupd.date'
update_flag_filespec = config['Daemon'].get(
    'update_flag_filespec', default_update_flag_filespec)

default_base_topic = 'home/nodes'
base_topic = config['MQTT'].get('base_topic', default_base_topic).lower()

default_sensor_name = 'rpi-reporter'
# Sensor name could be set either via configuration file or `MQTT_SENSOR_NAME`
# environment variable, the latter takes precedence
sensor_name = os.environ.get(
    "MQTT_SENSOR_NAME", config['MQTT'].get('sensor_name', default_sensor_name)
).lower()

# by default Home Assistant listens to the /homeassistant but it can be changed for a given installation
default_discovery_prefix = 'homeassistant'
discovery_prefix = config['MQTT'].get(
    'discovery_prefix', default_discovery_prefix).lower()

# report our RPi values every 5min
min_interval_in_minutes = 1
max_interval_in_minutes = 30
default_interval_in_minutes = 5
interval_in_minutes = config['Daemon'].getint(
    'interval_in_minutes', default_interval_in_minutes)

# check our RPi pending-updates every 4 hours
min_check_interval_in_hours = 2
max_check_interval_in_hours = 24
default_check_interval_in_hours = 4
check_interval_in_hours = config['Daemon'].getint(
    'check_updates_in_hours', default_check_interval_in_hours)

# default domain when hostname -f doesn't return it
default_domain = ''
fallback_domain = config['Daemon'].get(
    'fallback_domain', default_domain).lower()

commands = OrderedDict([])
if config.has_section('Commands'):
    commandSet = dict(config['Commands'].items())
    if len(commandSet) > 0:
        commands.update(commandSet)

# -----------------------------------------------------------------------------
#  Commands Subscription
# -----------------------------------------------------------------------------

# Check configuration
#
if (interval_in_minutes < min_interval_in_minutes) or (interval_in_minutes > max_interval_in_minutes):
    print_line('ERROR: Invalid "interval_in_minutes" found in configuration file: "config.ini"! Must be [{}-{}] Fix and try again... Aborting'.format(
        min_interval_in_minutes, max_interval_in_minutes), error=True, sd_notify=True)
    sys.exit(1)

if (check_interval_in_hours < min_check_interval_in_hours) or (check_interval_in_hours > max_check_interval_in_hours):
    print_line('ERROR: Invalid "check_updates_in_hours" found in configuration file: "config.ini"! Must be [{}-{}] Fix and try again... Aborting'.format(
        min_check_interval_in_hours, max_check_interval_in_hours), error=True, sd_notify=True)
    sys.exit(1)

# Ensure required values within sections of our config are present
if not config['MQTT']:
    print_line('ERROR: No MQTT settings found in configuration file "config.ini"! Fix and try again... Aborting',
               error=True, sd_notify=True)
    sys.exit(1)

print_line('Configuration accepted', console=False, sd_notify=True)

# -----------------------------------------------------------------------------
#  Daemon variables monitored
# -----------------------------------------------------------------------------

daemon_version_list = ['NOT-LOADED']
daemon_last_fetch_time = 0.0


def getDaemonReleases():
    # retrieve latest formal release versions list from repo
    global daemon_version_list
    global daemon_last_fetch_time

    newVersionList = []
    latestVersion = ''

    daemon_version_list = ['NOT-LOADED']  # mark as NOT fetched
    error = False
    try:
        response = requests.request('GET', 'http://kz0q.com/daemon-releases', verify=False, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        print_line('- getDaemonReleases() RQST exception=({})'.format(exc), error=True)
        error = True

    if not error:
        content = response.text
        lines = content.split('\n')
        for line in lines:
            if len(line) > 0:
                # print_line('- RLS Line=[{}]'.format(line), debug=True)
                lineParts = line.split(' ')
                # print_line('- RLS lineParts=[{}]'.format(lineParts), debug=True)
                if len(lineParts) >= 2:
                    currVersion = lineParts[0]
                    rlsType = lineParts[1]
                    if not currVersion in newVersionList:
                        if not 'latest' in rlsType.lower():
                            newVersionList.append(currVersion)  # append to list
                        else:
                            latestVersion = currVersion

        if len(newVersionList) > 1:
            newVersionList.sort()
        if len(latestVersion) > 0:
            if not latestVersion in newVersionList:
                newVersionList.insert(0, latestVersion)  # append to list

        daemon_version_list = newVersionList
        print_line('- RQST daemon_version_list=({})'.format(daemon_version_list), debug=True)
        daemon_last_fetch_time = time()    # record when we last fetched the versions


getDaemonReleases()  # and load them!
print_line('* daemon_last_fetch_time=({})'.format(daemon_last_fetch_time), debug=True)


# -----------------------------------------------------------------------------
#  Command invocation thru shell
def invoke_shell_cmd(cmd):
    # Setting `pipefail` prior to command ensures the command will exit with
    # non-zero status if any command in pipe (if any) fails.
    # Using `Popen` with `args` being list setting such shell option there
    # doesn't work for some shells, presumably due to argument processing
    # order, so invoking shell needs to be specified explicitly with the option
    # follows.
    out = subprocess.Popen(['bash', '-o', 'pipefail', '-c', cmd],
                           shell=False,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
    stdout, stderr = out.communicate()

    return stdout, stderr, out.returncode


# -----------------------------------------------------------------------------
#  RPi variables monitored
# -----------------------------------------------------------------------------

rpi_mac = ''
rpi_model_raw = ''
rpi_model = ''
rpi_connections = ''
rpi_hostname = ''
rpi_fqdn = ''
rpi_linux_release = ''
rpi_linux_version = ''
rpi_uptime_raw = ''
rpi_uptime = ''
rpi_uptime_sec = 0
rpi_last_update_date = datetime.min
# rpi_last_update_date_v2 = datetime.min
rpi_filesystem_space_raw = ''
rpi_filesystem_space = ''
rpi_filesystem_percent = ''
rpi_system_temp = ''
rpi_gpu_temp = ''
rpi_cpu_temp = ''
rpi_mqtt_script = script_info
rpi_interfaces = []
rpi_filesystem = []
# Tuple (Total, Free, Avail., Swap Total, Swap Free)
rpi_memory_tuple = ''
# Tuple (Hardware, Model Name, NbrCores, BogoMIPS, Serial)
rpi_cpu_tuple = ''
# for thermal status reporting
rpi_throttle_status = []
# new cpu loads
rpi_cpuload1 = ''
rpi_cpuload5 = ''
rpi_cpuload15 = ''
rpi_update_count = 0

if apt_available == False:
    rpi_update_count = -1   # if packaging system not avail. report -1

# Time for network transfer calculation
previous_time = time()

# -----------------------------------------------------------------------------
#  monitor variable fetch routines
#


def getDeviceCpuInfo():
    global rpi_cpu_tuple
    #  cat /proc/cpuinfo | /bin/egrep -i "processor|model|bogo|hardware|serial"
    # MULTI-CORE
    #  processor	: 0
    #  model name	: ARMv7 Processor rev 4 (v7l)
    #  BogoMIPS	: 38.40
    #  processor	: 1
    #  model name	: ARMv7 Processor rev 4 (v7l)
    #  BogoMIPS	: 38.40
    #  processor	: 2
    #  model name	: ARMv7 Processor rev 4 (v7l)
    #  BogoMIPS	: 38.40
    #  processor	: 3
    #  model name	: ARMv7 Processor rev 4 (v7l)
    #  BogoMIPS	: 38.40
    #  Hardware	: BCM2835
    #  Serial		: 00000000a8d11642
    #
    # SINGLE CORE
    #  processor	: 0
    #  model name	: ARMv6-compatible processor rev 7 (v6l)
    #  BogoMIPS	: 697.95
    #  Hardware	: BCM2835
    #  Serial		: 00000000131030c0
    #  Model		: Raspberry Pi Zero W Rev 1.1
    stdout, _, returncode = invoke_shell_cmd("cat /proc/cpuinfo | /bin/egrep -i 'processor|model|bogo|hardware|serial'")
    print_line('getDvcCPUinfo() stdout=[{}], retCode=({})'.format(stdout, returncode), debug=True)
    lines = []
    if not returncode:
        lines = stdout.decode('utf-8').split("\n")
    trimmedLines = []
    for currLine in lines:
        trimmedLine = currLine.lstrip().rstrip()
        trimmedLines.append(trimmedLine)
    cpu_hardware = ''   # 'hardware'
    cpu_cores = 0       # count of 'processor' lines
    cpu_model = ''      # 'model name'
    cpu_bogoMIPS = 0.0  # sum of 'BogoMIPS' lines
    cpu_serial = ''     # 'serial'
    for currLine in trimmedLines:
        lineParts = currLine.split(':')
        currValue = '{?unk?}'
        if len(lineParts) >= 2:
            currValue = lineParts[1].lstrip().rstrip()
        if 'Hardware' in currLine:
            cpu_hardware = currValue
        if 'model name' in currLine:
            cpu_model = currValue
        if 'BogoMIPS' in currLine:
            cpu_bogoMIPS += float(currValue)
        if 'processor' in currLine:
            cpu_cores += 1
        if 'Serial' in currLine:
            cpu_serial = currValue

    stdout, _, returncode = invoke_shell_cmd('/bin/cat /proc/loadavg')
    print_line('getDvcCPUinfo() stdout=[{}], retCode=({})'.format(stdout, returncode), debug=True)
    cpu_loads_raw = [-1.0] * 3
    if not returncode:
        cpu_loads_raw = stdout.decode('utf-8').split()
    print_line('cpu_loads_raw=[{}]'.format(cpu_loads_raw), debug=True)
    cpu_load1 = round(float(float(cpu_loads_raw[0]) / int(cpu_cores) * 100), 1)
    cpu_load5 = round(float(float(cpu_loads_raw[1]) / int(cpu_cores) * 100), 1)
    cpu_load15 = round(float(float(cpu_loads_raw[2]) / int(cpu_cores) * 100), 1)

    # Tuple (Hardware, Model Name, NbrCores, BogoMIPS, Serial)
    rpi_cpu_tuple = (cpu_hardware, cpu_model, cpu_cores,
                     cpu_bogoMIPS, cpu_serial, cpu_load1, cpu_load5, cpu_load15)
    print_line('rpi_cpu_tuple=[{}]'.format(rpi_cpu_tuple), debug=True)


def getDeviceMemory():
    global rpi_memory_tuple
    #  $ cat /proc/meminfo | /bin/egrep -i "mem[TFA]"
    #  MemTotal:         948304 kB
    #  MemFree:           40632 kB
    #  MemAvailable:     513332 kB
    stdout, _, returncode = invoke_shell_cmd('cat /proc/meminfo')
    lines = []
    if not returncode:
        lines = stdout.decode('utf-8').split("\n")
    trimmedLines = []
    for currLine in lines:
        trimmedLine = currLine.lstrip().rstrip()
        trimmedLines.append(trimmedLine)
    mem_total = ''
    mem_free = ''
    mem_avail = ''
    swap_total = ''
    swap_free = ''
    for currLine in trimmedLines:
        lineParts = currLine.split()
        if 'MemTotal' in currLine:
            mem_total = float(lineParts[1]) / 1024
        if 'MemFree' in currLine:
            mem_free = float(lineParts[1]) / 1024
        if 'MemAvail' in currLine:
            mem_avail = float(lineParts[1]) / 1024
        if 'SwapTotal' in currLine:
            swap_total = float(lineParts[1]) / 1024
        if 'SwapFree' in currLine:
            swap_free = float(lineParts[1]) / 1024

    # Tuple (Total, Free, Avail., Swap Total, Swap Free)
    # [0]=total, [1]=free, [2]=avail., [3]=swap total, [4]=swap free
    rpi_memory_tuple = (mem_total, mem_free, mem_avail, swap_total, swap_free)
    print_line('rpi_memory_tuple=[{}]'.format(rpi_memory_tuple), debug=True)


def getDeviceModel():
    global rpi_model
    global rpi_model_raw
    global rpi_connections
    stdout, _, returncode = invoke_shell_cmd("/bin/cat /proc/device-tree/model | /bin/sed -e 's/\\x0//g'")
    rpi_model_raw = 'N/A'
    if not returncode:
        rpi_model_raw = stdout.decode('utf-8')
    # now reduce string length (just more compact, same info)
    rpi_model = rpi_model_raw.replace('Raspberry ', 'R').replace(
        'i Model ', 'i 1 Model').replace('Rev ', 'r').replace(' Plus ', '+')

    # now decode interfaces
    rpi_connections = 'e,w,b'  # default
    if 'Pi 3 ' in rpi_model:
        if ' A ' in rpi_model:
            rpi_connections = 'w,b'
        else:
            rpi_connections = 'e,w,b'
    elif 'Pi 2 ' in rpi_model:
        rpi_connections = 'e'
    elif 'Pi 1 ' in rpi_model:
        if ' A ' in rpi_model:
            rpi_connections = ''
        else:
            rpi_connections = 'e'

    print_line('rpi_model_raw=[{}]'.format(rpi_model_raw), debug=True)
    print_line('rpi_model=[{}]'.format(rpi_model), debug=True)
    print_line('rpi_connections=[{}]'.format(rpi_connections), debug=True)


def getLinuxRelease():
    global rpi_linux_release
    stdout, _, returncode = invoke_shell_cmd(
        "/bin/cat /etc/apt/sources.list | /bin/egrep -v '#' | /usr/bin/awk '{ print $3 }' | /bin/sed -e 's/-/ /g' | /usr/bin/cut -f1 -d' ' | /bin/grep . | /usr/bin/sort -u")
    rpi_linux_release = 'N/A'
    if not returncode:
        rpi_linux_release = stdout.decode('utf-8').rstrip()
    print_line('rpi_linux_release=[{}]'.format(rpi_linux_release), debug=True)


def getLinuxVersion():
    global rpi_linux_version
    stdout, _, returncode = invoke_shell_cmd('/bin/uname -r')
    rpi_linux_version = 'N/A'
    if not returncode:
        rpi_linux_version = stdout.decode('utf-8').rstrip()
    print_line('rpi_linux_version=[{}]'.format(rpi_linux_version), debug=True)


def getHostnames():
    global rpi_hostname
    global rpi_fqdn
    stdout, _, returncode = invoke_shell_cmd('/bin/hostname -f')
    fqdn_from_hostname = stdout.decode('utf-8').rstrip() if not returncode else 'N/A'
    # Allow overriding the sensor host name via `MQTT_SENSOR_HOSTNAME`
    # environment variable
    fqdn_raw = os.environ.get('MQTT_SENSOR_HOSTNAME', fqdn_from_hostname)
    print_line('fqdn_raw=[{}]'.format(fqdn_raw), debug=True)
    rpi_hostname = fqdn_raw
    if '.' in fqdn_raw:
        # have good fqdn
        nameParts = fqdn_raw.split('.')
        rpi_fqdn = fqdn_raw
        rpi_hostname = nameParts[0]
    else:
        # missing domain, if we have a fallback apply it
        if len(fallback_domain) > 0:
            rpi_fqdn = '{}.{}'.format(fqdn_raw, fallback_domain)
        else:
            rpi_fqdn = rpi_hostname

    print_line('rpi_fqdn=[{}]'.format(rpi_fqdn), debug=True)
    print_line('rpi_hostname=[{}]'.format(rpi_hostname), debug=True)


def getUptime():
    global rpi_uptime_raw
    global rpi_uptime
    global rpi_uptime_sec
    stdout, _, returncode = invoke_shell_cmd('/usr/bin/uptime')
    rpi_uptime_raw = 'N/A'
    if not returncode:
        rpi_uptime_raw = stdout.decode('utf-8').rstrip().lstrip()
    print_line('rpi_uptime_raw=[{}]'.format(rpi_uptime_raw), debug=True)
    basicParts = rpi_uptime_raw.split()
    timeStamp = basicParts[0]
    lineParts = rpi_uptime_raw.split(',')
    if ('user' in lineParts[1]):
        rpi_uptime_raw = lineParts[0]
    else:
        rpi_uptime_raw = '{}, {}'.format(lineParts[0], lineParts[1])
    rpi_uptime = rpi_uptime_raw.replace(
        timeStamp, '').lstrip().replace('up ', '')
    print_line('rpi_uptime=[{}]'.format(rpi_uptime), debug=True)
    # Ex: 10 days, 23:57
    # Ex: 27 days, 27 min
    # Ex: 0 min
    bHasColon = (':' in rpi_uptime)
    uptimeParts = rpi_uptime.split(',')
    print_line('- uptimeParts=[{}]'.format(uptimeParts), debug=True)
    if len(uptimeParts) > 1:
        # have days and time
        dayParts = uptimeParts[0].strip().split(' ')
        daysVal = int(dayParts[0])
        timeStr = uptimeParts[1].strip()
    else:
        # have time only
        daysVal = 0
        timeStr = uptimeParts[0].strip()
    print_line('- days=({}), timeStr=[{}]'.format(daysVal, timeStr), debug=True)
    if ':' in timeStr:
        # timeStr = '23:57'
        timeParts = timeStr.split(':')
        hoursVal = int(timeParts[0])
        minsVal = int(timeParts[1])
    else:
        # timeStr = 27 of: '27 min'
        hoursVal = 0
        timeParts = timeStr.split(' ')
        minsVal = int(timeParts[0])
    print_line('- hoursVal=({}), minsVal=({})'.format(hoursVal, minsVal), debug=True)
    rpi_uptime_sec = (minsVal * 60) + (hoursVal * 60 * 60) + (daysVal * 24 * 60 * 60)
    print_line('rpi_uptime_sec=({})'.format(rpi_uptime_sec), debug=True)


def getNetworkIFsUsingIP(ip_cmd):
    cmd_str = '{} link show | /bin/egrep -v "link" | /bin/egrep " eth| wlan"'.format(
        ip_cmd)
    stdout, _, returncode = invoke_shell_cmd(cmd_str)
    lines = []
    if not returncode:
        lines = stdout.decode('utf-8').split("\n")
    interfaceNames = []
    line_count = len(lines)
    if line_count > 2:
        line_count = 2
    if line_count == 0:
        print_line('ERROR no lines left by ip(8) filter!', error=True)
        sys.exit(1)

    for lineIdx in range(line_count):
        trimmedLine = lines[lineIdx].lstrip().rstrip()
        if len(trimmedLine) > 0:
            lineParts = trimmedLine.split()
            # if interface is within a  container then we have eth0@if77, so
            # take the leftmost part up to '@' in that case
            interfaceName = lineParts[1].replace(':', '').split('@')[0]
            interfaceNames.append(interfaceName)

    print_line('interfaceNames=[{}]'.format(interfaceNames), debug=True)

    trimmedLines = []
    for interface in interfaceNames:
        lines = getSingleInterfaceDetails(interface)
        for currLine in lines:
            trimmedLines.append(currLine)

    loadNetworkIFDetailsFromLines(trimmedLines)


def getSingleInterfaceDetails(interfaceName):
    cmdString = '/sbin/ifconfig {} | /bin/egrep "Link|flags|inet |ether |TX packets |RX packets "'.format(
        interfaceName)
    stdout, _, returncode = invoke_shell_cmd(cmdString)
    lines = []
    if not returncode:
        lines = stdout.decode('utf-8').split("\n")
    trimmedLines = []
    for currLine in lines:
        trimmedLine = currLine.lstrip().rstrip()
        if len(trimmedLine) > 0:
            trimmedLines.append(trimmedLine)

    # print_line('interface:[{}] trimmedLines=[{}]'.format(interfaceName, trimmedLines), debug=True)
    return trimmedLines


def loadNetworkIFDetailsFromLines(ifConfigLines):
    global rpi_interfaces
    global rpi_mac
    global previous_time
    #
    # OLDER SYSTEMS
    #  eth0      Link encap:Ethernet  HWaddr b8:27:eb:c8:81:f2
    #    inet addr:192.168.100.41  Bcast:192.168.100.255  Mask:255.255.255.0
    #  wlan0     Link encap:Ethernet  HWaddr 00:0f:60:03:e6:dd
    # NEWER SYSTEMS
    #  The following means eth0 (wired is NOT connected, and WiFi is connected)
    #  eth0: flags=4099<UP,BROADCAST,MULTICAST>  mtu 1500
    #    ether b8:27:eb:1a:f3:bc  txqueuelen 1000  (Ethernet)
    #    RX packets 0  bytes 0 (0.0 B)
    #    TX packets 0  bytes 0 (0.0 B)
    #  wlan0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
    #    inet 192.168.100.189  netmask 255.255.255.0  broadcast 192.168.100.255
    #    ether b8:27:eb:4f:a6:e9  txqueuelen 1000  (Ethernet)
    #    RX packets 1358790  bytes 1197368205 (1.1 GiB)
    #    TX packets 916361  bytes 150440804 (143.4 MiB)
    #
    tmpInterfaces = []
    haveIF = False
    imterfc = ''
    rpi_mac = ''
    current_time = time()
    if current_time == previous_time:
        current_time += 1

    for currLine in ifConfigLines:
        lineParts = currLine.split()
        # print_line('- currLine=[{}]'.format(currLine), debug=True)
        # print_line('- lineParts=[{}]'.format(lineParts), debug=True)
        if len(lineParts) > 0:
            # skip interfaces generated by Home Assistant on RPi
            if 'docker' in currLine or 'veth' in currLine or 'hassio' in currLine:
                haveIF = False
                continue
            # let's evaluate remaining interfaces
            if 'flags' in currLine:  # NEWER ONLY
                haveIF = True
                imterfc = lineParts[0].replace(':', '')
                # print_line('newIF=[{}]'.format(imterfc), debug=True)
            # OLDER ONLY, using 'Link ' (notice space) prevent from tripping on
            # IPv6 ('Scope:Link')
            elif 'Link ' in currLine:
                haveIF = True
                imterfc = lineParts[0].replace(':', '')
                newTuple = (imterfc, 'mac', lineParts[4])
                if rpi_mac == '':
                    rpi_mac = lineParts[4]
                    print_line('rpi_mac=[{}]'.format(rpi_mac), debug=True)
                tmpInterfaces.append(newTuple)
                print_line('newTuple=[{}]'.format(newTuple), debug=True)
            elif haveIF == True:
                print_line('IF=[{}], lineParts=[{}]'.format(
                    imterfc, lineParts), debug=True)
                if 'inet' in currLine:  # OLDER & NEWER
                    newTuple = (imterfc, 'IP',
                                lineParts[1].replace('addr:', ''))
                    tmpInterfaces.append(newTuple)
                    print_line('newTuple=[{}]'.format(newTuple), debug=True)
                elif 'ether' in currLine:  # NEWER ONLY
                    newTuple = (imterfc, 'mac', lineParts[1])
                    tmpInterfaces.append(newTuple)
                    if rpi_mac == '':
                        rpi_mac = lineParts[1]
                        print_line('rpi_mac=[{}]'.format(rpi_mac), debug=True)
                    print_line('newTuple=[{}]'.format(newTuple), debug=True)
                elif 'RX' in currLine:  # NEWER ONLY
                    previous_value = getPreviousNetworkData(imterfc, 'rx_data')
                    current_value = int(lineParts[4])
                    rx_data = round((current_value - previous_value) / (current_time - previous_time) * 8 / 1024)
                    newTuple = (imterfc, 'rx_data', rx_data)
                    tmpInterfaces.append(newTuple)
                    print_line('newTuple=[{}]'.format(newTuple), debug=True)
                elif 'TX' in currLine:  # NEWER ONLY
                    previous_value = getPreviousNetworkData(imterfc, 'tx_data')
                    current_value = int(lineParts[4])
                    tx_data = round((current_value - previous_value) / (current_time - previous_time) * 8 / 1024)
                    newTuple = (imterfc, 'tx_data', tx_data)
                    tmpInterfaces.append(newTuple)
                    print_line('newTuple=[{}]'.format(newTuple), debug=True)
                    haveIF = False

    rpi_interfaces = tmpInterfaces
    print_line('rpi_interfaces=[{}]'.format(rpi_interfaces), debug=True)
    print_line('rpi_mac=[{}]'.format(rpi_mac), debug=True)


def getPreviousNetworkData(interface, field):
    global rpi_interfaces
    value = [item for item in rpi_interfaces if item[0] == interface and item[1] == field]
    if len(value) > 0:
        return value[0][2]
    else:
        return 0


def getNetworkIFs():
    ip_cmd = getIPCmd()
    if ip_cmd != '':
        getNetworkIFsUsingIP(ip_cmd)
    else:
        stdout, _, returncode = invoke_shell_cmd(
            '/sbin/ifconfig | /bin/egrep "Link|flags|inet |ether " | /bin/egrep -v -i "lo:|loopback|inet6|\:\:1|127\.0\.0\.1"')
        lines = []
        if not returncode:
            lines = stdout.decode('utf-8').split("\n")
        trimmedLines = []
        for currLine in lines:
            trimmedLine = currLine.lstrip().rstrip()
            if len(trimmedLine) > 0:
                trimmedLines.append(trimmedLine)

        print_line('trimmedLines=[{}]'.format(trimmedLines), debug=True)

        loadNetworkIFDetailsFromLines(trimmedLines)


def getFileSystemDrives():
    global rpi_filesystem_space_raw
    global rpi_filesystem_space
    global rpi_filesystem_percent
    global rpi_filesystem
    stdout, _, returncode = invoke_shell_cmd("/bin/df -m | /usr/bin/tail -n +2 | /bin/egrep -v 'tmpfs|boot'")
    lines = []
    if not returncode:
        lines = stdout.decode('utf-8').split("\n")
    trimmedLines = []
    for currLine in lines:
        trimmedLine = currLine.lstrip().rstrip()
        if len(trimmedLine) > 0:
            trimmedLines.append(trimmedLine)

    print_line('getFileSystemDrives() trimmedLines=[{}]'.format(
        trimmedLines), debug=True)

    #  EXAMPLES
    #
    #  Filesystem     1M-blocks  Used Available Use% Mounted on
    #  /dev/root          59998   9290     48208  17% /
    #  /dev/sda1         937872 177420    712743  20% /media/data
    # or
    #  /dev/root          59647  3328     53847   6% /
    #  /dev/sda1           3703    25      3472   1% /media/pi/SANDISK
    # or
    #  xxx.xxx.xxx.xxx:/srv/c2db7b94 200561 148655 41651 79% /

    # FAILING Case v1.4.0:
    # Here is the output of 'df -m'

    # Sys. de fichiers blocs de 1M Utilisé Disponible Uti% Monté sur
    # /dev/root 119774 41519 73358 37% /
    # devtmpfs 1570 0 1570 0% /dev
    # tmpfs 1699 0 1699 0% /dev/shm
    # tmpfs 1699 33 1667 2% /run
    # tmpfs 5 1 5 1% /run/lock
    # tmpfs 1699 0 1699 0% /sys/fs/cgroup
    # /dev/mmcblk0p1 253 55 198 22% /boot
    # tmpfs 340 0 340 0% /run/user/1000

    # FAILING Case v1.6.x (issue #61)
    # [[/bin/df: /mnt/sabrent: No such device or address',
    #   '/dev/root         119756  19503     95346  17% /',
    #   '/dev/sda1         953868 882178     71690  93% /media/usb0',
    #   '/dev/sdb1         976761  93684    883078  10% /media/pi/SSD']]

    tmpDrives = []
    for currLine in trimmedLines:
        if 'no such device' in currLine.lower():
            print_line('BAD LINE FORMAT, Skipped=[{}]'.format(currLine), debug=True, warning=True)
            continue
        lineParts = currLine.split()
        print_line('lineParts({})=[{}]'.format(
            len(lineParts), lineParts), debug=True)
        if len(lineParts) < 6:
            print_line('BAD LINE FORMAT, Skipped=[{}]'.format(
                lineParts), debug=True, warning=True)
            continue
        # tuple { total blocks, used%, mountPoint, device }
        #
        # new mech:
        #  Filesystem     1M-blocks  Used Available Use% Mounted on
        #     [0]           [1]       [2]     [3]    [4]   [5]
        #     [--]         [n-3]     [n-2]   [n-1]   [n]   [--]
        #  where  percent_field_index  is 'n'
        #

        # locate our % used field...
        for percent_field_index in range(len(lineParts) - 2, 1, -1):
            if '%' in lineParts[percent_field_index]:
                break
        print_line('percent_field_index=[{}]'.format(
            percent_field_index), debug=True)

        total_size_idx = percent_field_index - 3
        mount_idx = percent_field_index + 1

        # do we have a two part device name?
        device = lineParts[0]
        if total_size_idx != 1:
            device = '{} {}'.format(lineParts[0], lineParts[1])
        print_line('device=[{}]'.format(device), debug=True)

        # do we have a two part mount point?
        mount_point = lineParts[mount_idx]
        if len(lineParts) - 1 > mount_idx:
            mount_point = '{} {}'.format(
                lineParts[mount_idx], lineParts[mount_idx + 1])
        print_line('mount_point=[{}]'.format(mount_point), debug=True)

        total_size_in_gb = '{:.0f}'.format(
            next_power_of_2(lineParts[total_size_idx]))
        newTuple = (total_size_in_gb, lineParts[percent_field_index].replace(
            '%', ''),  mount_point, device)
        tmpDrives.append(newTuple)
        print_line('newTuple=[{}]'.format(newTuple), debug=True)
        if newTuple[2] == '/':
            rpi_filesystem_space_raw = currLine
            rpi_filesystem_space = newTuple[0]
            rpi_filesystem_percent = newTuple[1]
            print_line('rpi_filesystem_space=[{}GB]'.format(
                newTuple[0]), debug=True)
            print_line('rpi_filesystem_percent=[{}]'.format(
                newTuple[1]), debug=True)

    rpi_filesystem = tmpDrives
    print_line('rpi_filesystem=[{}]'.format(rpi_filesystem), debug=True)


def next_power_of_2(size):
    size_as_nbr = int(size) - 1
    return 1 if size == 0 else (1 << size_as_nbr.bit_length()) / 1024


def getVcGenCmd():
    cmd_locn1 = '/usr/bin/vcgencmd'
    cmd_locn2 = '/opt/vc/bin/vcgencmd'
    desiredCommand = cmd_locn1
    if os.path.exists(desiredCommand) == False:
        desiredCommand = cmd_locn2
    if os.path.exists(desiredCommand) == False:
        desiredCommand = ''
    if desiredCommand != '':
        print_line('Found vcgencmd(1)=[{}]'.format(desiredCommand), debug=True)
    return desiredCommand


def getShellCmd():
    cmd_locn1 = '/usr/bin/sh'
    cmd_locn2 = '/bin/sh'
    desiredCommand = cmd_locn1
    if os.path.exists(desiredCommand) == False:
        desiredCommand = cmd_locn2
    if os.path.exists(desiredCommand) == False:
        desiredCommand = ''
    if desiredCommand != '':
        print_line('Found sh(1)=[{}]'.format(desiredCommand), debug=True)
    return desiredCommand


def getIPCmd():
    cmd_locn1 = '/bin/ip'
    cmd_locn2 = '/sbin/ip'
    desiredCommand = ''
    if os.path.exists(cmd_locn1) == True:
        desiredCommand = cmd_locn1
    elif os.path.exists(cmd_locn2) == True:
        desiredCommand = cmd_locn2
    if desiredCommand != '':
        print_line('Found IP(8)=[{}]'.format(desiredCommand), debug=True)
    return desiredCommand


def getSystemTemperature():
    global rpi_system_temp
    global rpi_gpu_temp
    global rpi_cpu_temp
    rpi_gpu_temp_raw = 'failed'
    cmd_fspec = getVcGenCmd()
    if cmd_fspec == '':
        rpi_system_temp = float('-1.0')
        rpi_gpu_temp = float('-1.0')
        rpi_cpu_temp = getSystemCPUTemperature()
        if rpi_cpu_temp != -1.0:
            rpi_system_temp = rpi_cpu_temp
    else:
        retry_count = 3
        while retry_count > 0 and 'failed' in rpi_gpu_temp_raw:

            cmd_string = "{} measure_temp | /bin/sed -e 's/\\x0//g'".format(
                cmd_fspec)
            stdout, _, returncode = invoke_shell_cmd(cmd_string)
            rpi_gpu_temp_raw = 'failed'
            if not returncode:
                rpi_gpu_temp_raw = stdout.decode(
                    'utf-8').rstrip().replace('temp=', '').replace('\'C', '')
            retry_count -= 1
            sleep(1)

        if 'failed' in rpi_gpu_temp_raw:
            interpretedTemp = float('-1.0')
        else:
            interpretedTemp = float(rpi_gpu_temp_raw)
        rpi_gpu_temp = interpretedTemp
        print_line('rpi_gpu_temp=[{}]'.format(rpi_gpu_temp), debug=True)

        rpi_cpu_temp = getSystemCPUTemperature()

        # fallback to CPU temp is GPU not available
        rpi_system_temp = rpi_gpu_temp
        if rpi_gpu_temp == -1.0:
            rpi_system_temp = rpi_cpu_temp


def getSystemCPUTemperature():
    cmd_locn1 = '/sys/class/thermal/thermal_zone0/temp'
    cmdString = '/bin/cat {}'.format(
        cmd_locn1)

    rpi_cpu_temp = float('-1.0')
    if os.path.exists(cmd_locn1):
        stdout, _, returncode = invoke_shell_cmd(cmdString)
        if not returncode:
            rpi_cpu_temp_raw = stdout.decode('utf-8').rstrip()
            rpi_cpu_temp = float(rpi_cpu_temp_raw) / 1000.0
    print_line('rpi_cpu_temp=[{}]'.format(rpi_cpu_temp), debug=True)
    return rpi_cpu_temp


def getSystemThermalStatus():
    global rpi_throttle_status
    # sudo vcgencmd get_throttled
    #   throttled=0x0
    #
    #  REF: https://harlemsquirrel.github.io/shell/2019/01/05/monitoring-raspberry-pi-power-and-thermal-issues.html
    #
    rpi_throttle_status = []
    cmd_fspec = getVcGenCmd()
    if cmd_fspec == '':
        rpi_throttle_status.append('Not Available')
    else:
        cmd_string = "{} get_throttled".format(cmd_fspec)
        stdout, _, returncode = invoke_shell_cmd(cmd_string)
        rpi_throttle_status_raw = ''
        if not returncode:
            rpi_throttle_status_raw = stdout.decode('utf-8').rstrip()
        print_line('rpi_throttle_status_raw=[{}]'.format(
            rpi_throttle_status_raw), debug=True)

        if len(rpi_throttle_status_raw) and not 'throttled' in rpi_throttle_status_raw:
            rpi_throttle_status.append(
                'bad response [{}] from vcgencmd'.format(rpi_throttle_status_raw))
        else:
            values = []
            lineParts = rpi_throttle_status_raw.split('=')
            print_line('lineParts=[{}]'.format(lineParts), debug=True)
            rpi_throttle_value_raw = ''
            if len(lineParts) > 1:
                rpi_throttle_value_raw = lineParts[1]
            rpi_throttle_value = int(0)
            if len(rpi_throttle_value_raw) > 0:
                values.append('throttled = {}'.format(rpi_throttle_value_raw))
                if rpi_throttle_value_raw.startswith('0x'):
                    rpi_throttle_value = int(rpi_throttle_value_raw, 16)
                else:
                    rpi_throttle_value = int(rpi_throttle_value_raw, 10)
                # decode test code
                # rpi_throttle_value = int('0x50002', 16)
                if rpi_throttle_value > 0:
                    values = interpretThrottleValue(rpi_throttle_value)
                else:
                    values.append('Not throttled')
            if len(values) > 0:
                rpi_throttle_status = values

    print_line('rpi_throttle_status=[{}]'.format(
        rpi_throttle_status), debug=True)


def interpretThrottleValue(throttleValue):
    """
    01110000000000000010
    ||||            ||||_ Under-voltage detected
    ||||            |||_ Arm frequency capped
    ||||            ||_ Currently throttled
    ||||            |_ Soft temperature limit active
    ||||_ Under-voltage has occurred since last reboot
    |||_ Arm frequency capped has occurred
    ||_ Throttling has occurred
    |_ Soft temperature limit has occurred
    """
    print_line('throttleValue=[{}]'.format(bin(throttleValue)), debug=True)
    interpResult = []
    meanings = [
        (2**0, 'Under-voltage detected'),
        (2**1, 'Arm frequency capped'),
        (2**2, 'Currently throttled'),
        (2**3, 'Soft temperature limit active'),
        (2**16, 'Under-voltage has occurred'),
        (2**17, 'Arm frequency capped has occurred'),
        (2**18, 'Throttling has occurred'),
        (2**19, 'Soft temperature limit has occurred'),
    ]

    for meaningIndex in range(len(meanings)):
        bitTuple = meanings[meaningIndex]
        if throttleValue & bitTuple[0] > 0:
            interpResult.append(bitTuple[1])

    print_line('interpResult=[{}]'.format(interpResult), debug=True)
    return interpResult


def getLastUpdateDate():
    global rpi_last_update_date
    # apt-get update writes to following dir (so date changes on update)
    apt_listdir_filespec = '/var/lib/apt/lists/partial'
    # apt-get dist-upgrade | autoremove update the following file when actions are taken
    apt_lockdir_filespec = '/var/lib/dpkg/lock'
    cmdString = '/bin/ls -ltrd {} {}'.format(
        apt_listdir_filespec, apt_lockdir_filespec)
    stdout, _, returncode = invoke_shell_cmd(cmdString)
    lines = []
    if not returncode:
        lines = stdout.decode('utf-8').split("\n")
    trimmedLines = []
    for currLine in lines:
        trimmedLine = currLine.lstrip().rstrip()
        if len(trimmedLine) > 0:
            trimmedLines.append(trimmedLine)
    print_line('trimmedLines=[{}]'.format(trimmedLines), debug=True)

    fileSpec_latest = None
    if len(trimmedLines) > 0:
        lastLineIdx = len(trimmedLines) - 1
        lineParts = trimmedLines[lastLineIdx].split()
        if len(lineParts) > 0:
            lastPartIdx = len(lineParts) - 1
            fileSpec_latest = lineParts[lastPartIdx]
        print_line('fileSpec_latest=[{}]'.format(fileSpec_latest), debug=True)

    rpi_last_update_date = None
    if fileSpec_latest:
        fileModDateInSeconds = os.path.getmtime(fileSpec_latest)
        fileModDate = datetime.fromtimestamp(fileModDateInSeconds)
        rpi_last_update_date = fileModDate.replace(tzinfo=local_tz)
        print_line('rpi_last_update_date=[{}]'.format(
            rpi_last_update_date), debug=True)


def to_datetime(time):
    return datetime.fromordinal(int(time)) + datetime.timedelta(time % 1)


def getLastInstallDate():
    global rpi_last_update_date
    # apt_log_filespec = '/var/log/dpkg.log'
    # apt_log_filespec2 = '/var/log/dpkg.log.1'
    stdout, _, returncode = invoke_shell_cmd(
        "/bin/grep --binary-files=text 'status installed' /var/log/dpkg.log /var/log/dpkg.log.1 2>/dev/null | sort | tail -1")
    last_installed_pkg_raw = ''
    if not returncode:
        last_installed_pkg_raw = stdout.decode(
            'utf-8').rstrip().replace('/var/log/dpkg.log:', '').replace('/var/log/dpkg.log.1:', '')
    print_line('last_installed_pkg_raw=[{}]'.format(
        last_installed_pkg_raw), debug=True)
    line_parts = last_installed_pkg_raw.split()
    if len(line_parts) > 1:
        pkg_date_string = '{} {}'.format(line_parts[0], line_parts[1])
        print_line('pkg_date_string=[{}]'.format(pkg_date_string), debug=True)
        # Example:
        #   2020-07-22 17:08:26 status installed python3-tzlocal:all 1.3-1

        pkg_install_date = datetime.strptime(
            pkg_date_string, '%Y-%m-%d %H:%M:%S').replace(tzinfo=local_tz)
        rpi_last_update_date = pkg_install_date

    print_line('rpi_last_update_date=[{}]'.format(
        rpi_last_update_date), debug=True)


update_last_fetch_time = 0.0


def getNumberOfAvailableUpdates():
    global rpi_update_count
    global update_last_fetch_time
    if apt_available:
        cache = apt.Cache()
        cache.open(None)
        cache.upgrade()
        changes = cache.get_changes()
        print_line('APT changes=[{}]'.format(changes), debug=True)
        print_line('APT Avail Updates: ({})'.format(len(changes)), info=True)
        # return str(cache.get_changes().len())
        rpi_update_count = len(changes)
        update_last_fetch_time = time()


# get our hostnames so we can setup MQTT
getHostnames()
sensor_name = 'rpi-{}'.format(rpi_hostname)

# get model so we can use it too in MQTT
getDeviceModel()
getDeviceCpuInfo()
getLinuxRelease()
getLinuxVersion()
getFileSystemDrives()
if apt_available:
    getNumberOfAvailableUpdates()

# -----------------------------------------------------------------------------
#  MQTT Topic def's
# -----------------------------------------------------------------------------

command_base_topic = '{}/command/{}'.format(base_topic, sensor_name.lower())

# -----------------------------------------------------------------------------
#  timer and timer funcs for ALIVE MQTT Notices handling
# -----------------------------------------------------------------------------

K_ALIVE_TIMOUT_IN_SECONDS = 60


def publishAliveStatus():
    print_line('- SEND: yes, still alive -', debug=True)
    mqtt_client.publish(lwt_sensor_topic, payload=lwt_online_val, retain=False)
    mqtt_client.publish(lwt_command_topic, payload=lwt_online_val, retain=False)


def publishShuttingDownStatus():
    print_line('- SEND: shutting down -', debug=True)
    mqtt_client.publish(lwt_sensor_topic, payload=lwt_offline_val, retain=False)
    mqtt_client.publish(lwt_command_topic, payload=lwt_offline_val, retain=False)


def aliveTimeoutHandler():
    print_line('- MQTT TIMER INTERRUPT -', debug=True)
    _thread.start_new_thread(publishAliveStatus, ())
    startAliveTimer()


def startAliveTimer():
    global aliveTimer
    global aliveTimerRunningStatus
    stopAliveTimer()
    aliveTimer = threading.Timer(K_ALIVE_TIMOUT_IN_SECONDS, aliveTimeoutHandler)
    aliveTimer.start()
    aliveTimerRunningStatus = True
    print_line(
        '- started MQTT timer - every {} seconds'.format(K_ALIVE_TIMOUT_IN_SECONDS), debug=True)


def stopAliveTimer():
    global aliveTimer
    global aliveTimerRunningStatus
    aliveTimer.cancel()
    aliveTimerRunningStatus = False
    print_line('- stopped MQTT timer', debug=True)


def isAliveTimerRunning():
    global aliveTimerRunningStatus
    return aliveTimerRunningStatus


# our ALIVE TIMER
aliveTimer = threading.Timer(K_ALIVE_TIMOUT_IN_SECONDS, aliveTimeoutHandler)
# our BOOL tracking state of ALIVE TIMER
aliveTimerRunningStatus = False


# -----------------------------------------------------------------------------
#  MQTT setup and startup
# -----------------------------------------------------------------------------

# MQTT connection
lwt_sensor_topic = '{}/sensor/{}/status'.format(base_topic, sensor_name.lower())
lwt_command_topic = '{}/command/{}/status'.format(base_topic, sensor_name.lower())
lwt_online_val = 'online'
lwt_offline_val = 'offline'

print_line('Connecting to MQTT broker ...', verbose=True)
# ensure backward compatibility with older versions of paho-mqtt (<=2.0.0)
# ToDo: Need to update to VERSION2 at some point
try:
    mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
except AttributeError:
    mqtt_client = mqtt.Client()

# hook up MQTT callbacks
mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.on_publish = on_publish
mqtt_client.on_message = on_message

mqtt_client.will_set(lwt_sensor_topic, payload=lwt_offline_val, retain=True)
mqtt_client.will_set(lwt_command_topic, payload=lwt_offline_val, retain=True)

if config['MQTT'].getboolean('tls', False):
    # According to the docs, setting PROTOCOL_SSLv23 "Selects the highest protocol version
    # that both the client and server support. Despite the name, this option can select
    # “TLS” protocols as well as “SSL”" - so this seems like a resonable default
    mqtt_client.tls_set(
        ca_certs=config['MQTT'].get('tls_ca_cert', None),
        keyfile=config['MQTT'].get('tls_keyfile', None),
        certfile=config['MQTT'].get('tls_certfile', None),
        tls_version=ssl.PROTOCOL_SSLv23
    )
    # Allow skipping TLS verification if `tls_insecure` configuration option is
    # set, see https://pypi.org/project/paho-mqtt/#tls-insecure-set for details
    mqtt_client.tls_insecure_set(config['MQTT'].get('tls_insecure', False))

mqtt_username = os.environ.get("MQTT_USERNAME", config['MQTT'].get('username'))
mqtt_password = os.environ.get(
    "MQTT_PASSWORD", config['MQTT'].get('password', None))

if mqtt_username:
    mqtt_client.username_pw_set(mqtt_username, mqtt_password)
try:
    mqtt_client.connect(os.environ.get('MQTT_HOSTNAME', config['MQTT'].get('hostname', 'localhost')),
                        port=int(os.environ.get(
                            'MQTT_PORT', config['MQTT'].get('port', '1883'))),
                        keepalive=config['MQTT'].getint('keepalive', 60))
except:
    print_line('MQTT connection error. Please check your settings in the configuration file "config.ini"',
               error=True, sd_notify=True)
    sys.exit(1)
else:
    mqtt_client.publish(lwt_sensor_topic, payload=lwt_online_val, retain=False)
    mqtt_client.publish(lwt_command_topic, payload=lwt_online_val, retain=False)
    mqtt_client.loop_start()

    while mqtt_client_connected == False:  # wait in loop
        print_line(
            '* Wait on mqtt_client_connected=[{}]'.format(mqtt_client_connected), debug=True)
        sleep(1.0)  # some slack to establish the connection

    startAliveTimer()

sd_notifier.notify('READY=1')

# -----------------------------------------------------------------------------
#  Perform our MQTT Discovery Announcement...
# -----------------------------------------------------------------------------

# what RPi device are we on?
# get our hostnames so we can setup MQTT
getNetworkIFs()  # this will fill-in rpi_mac

mac_basic = rpi_mac.lower().replace(":", "")
mac_left = mac_basic[:6]
mac_right = mac_basic[6:]
print_line('mac lt=[{}], rt=[{}], mac=[{}]'.format(
    mac_left, mac_right, mac_basic), debug=True)
uniqID = "RPi-{}Mon{}".format(mac_left, mac_right)

# our RPi Reporter device
# KeyError: 'home310/sensor/rpi-pi3plus/values' let's not use this 'values' as topic
K_LD_MONITOR = "monitor"
K_LD_SYS_TEMP = "temperature"
K_LD_FS_USED = "disk_used"
K_LD_PAYLOAD_NAME = "info"
K_LD_CPU_USE = "cpu_load"
K_LD_MEM_USED = "mem_used"

if interval_in_minutes < 5:
    K_LD_CPU_USE_JSON = "cpu.load_1min_prcnt"
elif interval_in_minutes < 15:
    K_LD_CPU_USE_JSON = "cpu.load_5min_prcnt"
else:
    K_LD_CPU_USE_JSON = "cpu.load_15min_prcnt"

# determine CPU model
if len(rpi_cpu_tuple) > 0:
    cpu_model = rpi_cpu_tuple[1]
else:
    cpu_model = ''

if cpu_model.find("ARMv7") >= 0 or cpu_model.find("ARMv6") >= 0:
    cpu_use_icon = "mdi:cpu-32-bit"
else:
    cpu_use_icon = "mdi:cpu-64-bit"

print_line('Announcing RPi Monitoring device to MQTT broker for auto-discovery ...')

# Publish our MQTT auto discovery
#  table of key items to publish:
detectorValues = OrderedDict([
    (K_LD_MONITOR, dict(
        title="Monitor",
        topic_category="sensor",
        device_class="timestamp",
        device_ident="RPi-{}".format(rpi_fqdn),
        no_title_prefix="yes",
        icon='mdi:raspberry-pi',
        json_attr="yes",
        json_value="timestamp",
    )),
    (K_LD_SYS_TEMP, dict(
        title="Temperature",
        topic_category="sensor",
        device_class="temperature",
        state_class="measurement",
        no_title_prefix="yes",
        unit="°C",
        icon='mdi:thermometer',
        json_value="temperature_c",
    )),
    (K_LD_FS_USED, dict(
        title="Disk Used",
        topic_category="sensor",
        state_class="measurement",
        no_title_prefix="yes",
        unit="%",
        icon='mdi:sd',
        json_value="fs_used_prcnt",
    )),
    (K_LD_CPU_USE, dict(
        title="CPU Use",
        topic_category="sensor",
        state_class="measurement",
        no_title_prefix="yes",
        unit="%",
        icon=cpu_use_icon,
        json_value=K_LD_CPU_USE_JSON,
    )),
    (K_LD_MEM_USED, dict(
        title="Memory Used",
        topic_category="sensor",
        state_class="measurement",
        no_title_prefix="yes",
        json_value="mem_used_prcnt",
        unit="%",
        icon='mdi:memory'
    ))
])

for [command, _] in commands.items():
    # print_line('- REGISTER command: [{}]'.format(command), debug=True)
    iconName = 'mdi:gesture-tap'
    if 'reboot' in command:
        iconName = 'mdi:restart'
    elif 'shutdown' in command:
        iconName = 'mdi:power-sleep'
    elif 'service' in command:
        iconName = 'mdi:cog-counterclockwise'
    detectorValues.update({
        command: dict(
            title=command,
            topic_category='button',
            no_title_prefix='yes',
            icon=iconName,
            command=command,
            command_topic='{}/{}'.format(command_base_topic, command)
        )
    })

# print_line('- detectorValues=[{}]'.format(detectorValues), debug=True)

sensor_base_topic = '{}/sensor/{}'.format(base_topic, sensor_name.lower())
values_topic_rel = '{}/{}'.format('~', K_LD_MONITOR)
values_topic = '{}/{}'.format(sensor_base_topic, K_LD_MONITOR)
activity_topic_rel = '{}/status'.format('~')     # vs. LWT
activity_topic = '{}/status'.format(sensor_base_topic)    # vs. LWT

command_topic_rel = '~/set'

# discovery_topic = '{}/sensor/{}/{}/config'.format(discovery_prefix, sensor_name.lower(), sensor)
for [sensor, params] in detectorValues.items():
    discovery_topic = '{}/{}/{}/{}/config'.format(discovery_prefix,
                                                  params['topic_category'], sensor_name.lower(), sensor)
    payload = OrderedDict()
    if 'no_title_prefix' in params:
        payload['name'] = "{}".format(params['title'].title())
    else:
        payload['name'] = "{} {}".format(
            sensor_name.title(), params['title'].title())
    payload['uniq_id'] = "{}_{}".format(uniqID, sensor.lower())
    if 'device_class' in params:
        payload['dev_cla'] = params['device_class']
    if 'unit' in params:
        payload['unit_of_measurement'] = params['unit']
    if 'json_value' in params:
        payload['stat_t'] = values_topic_rel
        payload['val_tpl'] = "{{{{ value_json.{}.{} }}}}".format(K_LD_PAYLOAD_NAME, params['json_value'])
    if 'command' in params:
        payload['~'] = command_base_topic
        payload['cmd_t'] = '~/{}'.format(params['command'])
        payload['json_attr_t'] = '~/{}/attributes'.format(params['command'])
    else:
        payload['~'] = sensor_base_topic
    payload['avty_t'] = activity_topic_rel
    payload['pl_avail'] = lwt_online_val
    payload['pl_not_avail'] = lwt_offline_val
    if 'trigger_type' in params:
        payload['type'] = params['trigger_type']
    if 'trigger_subtype' in params:
        payload['subtype'] = params['trigger_subtype']
    if 'icon' in params:
        payload['ic'] = params['icon']
    if 'json_attr' in params:
        payload['json_attr_t'] = values_topic_rel
        payload['json_attr_tpl'] = '{{{{ value_json.{} | tojson }}}}'.format(K_LD_PAYLOAD_NAME)
    if 'device_ident' in params:
        payload['dev'] = {
            'identifiers': ["{}".format(uniqID)],
            'manufacturer': 'Raspberry Pi (Trading) Ltd.',
            'name': params['device_ident'],
            'model': '{}'.format(rpi_model),
            'sw_version': "{} {}".format(rpi_linux_release, rpi_linux_version)
        }
    else:
        payload['dev'] = {
            'identifiers': ["{}".format(uniqID)],
        }
    mqtt_client.publish(discovery_topic, json.dumps(payload), 1, retain=True)

    # remove connections as test:                  'connections' : [["mac", mac.lower()], [interface, ipaddr]],

# -----------------------------------------------------------------------------
#  timer and timer funcs for period handling
# -----------------------------------------------------------------------------

TIMER_INTERRUPT = (-1)
TEST_INTERRUPT = (-2)


def periodTimeoutHandler():
    print_line('- PERIOD TIMER INTERRUPT -', debug=True)
    handle_interrupt(TIMER_INTERRUPT)  # '0' means we have a timer interrupt!!!
    startPeriodTimer()


def startPeriodTimer():
    global endPeriodTimer
    global periodTimeRunningStatus
    stopPeriodTimer()
    endPeriodTimer = threading.Timer(
        interval_in_minutes * 60.0, periodTimeoutHandler)
    endPeriodTimer.start()
    periodTimeRunningStatus = True
    print_line(
        '- started PERIOD timer - every {} seconds'.format(interval_in_minutes * 60.0), debug=True)


def stopPeriodTimer():
    global endPeriodTimer
    global periodTimeRunningStatus
    endPeriodTimer.cancel()
    periodTimeRunningStatus = False
    print_line('- stopped PERIOD timer', debug=True)


def isPeriodTimerRunning():
    global periodTimeRunningStatus
    return periodTimeRunningStatus


# our TIMER
endPeriodTimer = threading.Timer(
    interval_in_minutes * 60.0, periodTimeoutHandler)
# our BOOL tracking state of TIMER
periodTimeRunningStatus = False
reported_first_time = False

# -----------------------------------------------------------------------------
#  MQTT Transmit Helper Routines
# -----------------------------------------------------------------------------
SCRIPT_TIMESTAMP = "timestamp"
K_RPI_MODEL = "rpi_model"
K_RPI_CONNECTIONS = "ifaces"
K_RPI_HOSTNAME = "host_name"
K_RPI_FQDN = "fqdn"
K_RPI_LINUX_RELEASE = "ux_release"
K_RPI_LINUX_VERSION = "ux_version"
K_RPI_LINUX_AVAIL_UPD = "ux_updates"
K_RPI_UPTIME = "up_time"
K_RPI_UPTIME_SECONDS = "up_time_secs"
K_RPI_DATE_LAST_UPDATE = "last_update"
K_RPI_FS_SPACE = 'fs_total_gb'  # "fs_space_gbytes"
K_RPI_FS_AVAIL = 'fs_free_prcnt'  # "fs_available_prcnt"
K_RPI_FS_USED = 'fs_used_prcnt'  # "fs_used_prcnt"
K_RPI_RAM_USED = 'mem_used_prcnt'  # "mem_used_prcnt"
K_RPI_SYSTEM_TEMP = "temperature_c"
K_RPI_GPU_TEMP = "temp_gpu_c"
K_RPI_CPU_TEMP = "temp_cpu_c"
K_RPI_SCRIPT = "reporter"
K_RPI_SCRIPT_VERSIONS = "reporter_releases"
K_RPI_NETWORK = "networking"
K_RPI_INTERFACE = "interface"
SCRIPT_REPORT_INTERVAL = "report_interval"
# new drives dictionary
K_RPI_DRIVES = "drives"
K_RPI_DRV_BLOCKS = "size_gb"
K_RPI_DRV_USED = "used_prcnt"
K_RPI_DRV_MOUNT = "mount_pt"
K_RPI_DRV_DEVICE = "device"
K_RPI_DRV_NFS = "device-nfs"
K_RPI_DVC_IP = "ip"
K_RPI_DVC_PATH = "dvc"
# new block devices dictionary
K_RPI_BLK_DEVICES = "block_devices"
K_RPI_BLK_DEV_TEMP = "temperature_c"
# new memory dictionary
K_RPI_MEMORY = "memory"
K_RPI_MEM_TOTAL = "size_mb"
K_RPI_MEM_FREE = "free_mb"
K_RPI_SWAP_TOTAL = "size_swap"
K_RPI_SWAP_FREE = "free_swap"
# Tuple (Hardware, Model Name, NbrCores, BogoMIPS, Serial)
K_RPI_CPU = "cpu"
K_RPI_CPU_HARDWARE = "hardware"
K_RPI_CPU_MODEL = "model"
K_RPI_CPU_CORES = "number_cores"
K_RPI_CPU_BOGOMIPS = "bogo_mips"
K_RPI_CPU_SERIAL = "serial"
#  add new CPU Load
K_RPI_CPU_LOAD1 = "load_1min_prcnt"
K_RPI_CPU_LOAD5 = "load_5min_prcnt"
K_RPI_CPU_LOAD15 = "load_15min_prcnt"
# list of throttle status
K_RPI_THROTTLE = "throttle"


def send_status(timestamp, nothing):
    rpiData = OrderedDict()
    rpiData[SCRIPT_TIMESTAMP] = timestamp.astimezone().replace(
        microsecond=0).isoformat()
    rpiData[K_RPI_MODEL] = rpi_model
    rpiData[K_RPI_CONNECTIONS] = rpi_connections
    rpiData[K_RPI_HOSTNAME] = rpi_hostname
    rpiData[K_RPI_FQDN] = rpi_fqdn
    rpiData[K_RPI_LINUX_RELEASE] = rpi_linux_release
    rpiData[K_RPI_LINUX_VERSION] = rpi_linux_version
    rpiData[K_RPI_LINUX_AVAIL_UPD] = rpi_update_count
    rpiData[K_RPI_UPTIME] = rpi_uptime
    rpiData[K_RPI_UPTIME_SECONDS] = rpi_uptime_sec

    #  DON'T use V1 form of getting date (my dashbord mech)
    # actualDate = datetime.strptime(rpi_last_update_date, '%y%m%d%H%M%S')
    # actualDate.replace(tzinfo=local_tz)
    # rpiData[K_RPI_DATE_LAST_UPDATE] = actualDate.astimezone().replace(microsecond=0).isoformat()
    # also don't use V2 form...
    # if rpi_last_update_date_v2 != datetime.min:
    #    rpiData[K_RPI_DATE_LAST_UPDATE] = rpi_last_update_date_v2.astimezone().replace(microsecond=0).isoformat()
    # else:
    #    rpiData[K_RPI_DATE_LAST_UPDATE] = ''
    if rpi_last_update_date and rpi_last_update_date != datetime.min:
        rpiData[K_RPI_DATE_LAST_UPDATE] = rpi_last_update_date.astimezone().replace(
            microsecond=0).isoformat()
    else:
        rpiData[K_RPI_DATE_LAST_UPDATE] = ''
    rpiData[K_RPI_FS_SPACE] = int(rpi_filesystem_space.replace('GB', ''), 10)
    # TODO: consider eliminating K_RPI_FS_AVAIL/fs_free_prcnt as used is needed but free is not... (can be calculated)
    rpiData[K_RPI_FS_AVAIL] = 100 - int(rpi_filesystem_percent, 10)
    rpiData[K_RPI_FS_USED] = int(rpi_filesystem_percent, 10)

    rpiData[K_RPI_NETWORK] = getNetworkDictionary()

    rpiBlockDevices = getBlockDevicesDictionary()
    if len(rpiBlockDevices) > 0:
        rpiData[K_RPI_BLK_DEVICES] = rpiBlockDevices

    rpiDrives = getDrivesDictionary()
    if len(rpiDrives) > 0:
        rpiData[K_RPI_DRIVES] = rpiDrives

    rpiRam = getMemoryDictionary()
    if len(rpiRam) > 0:
        rpiData[K_RPI_MEMORY] = rpiRam
        ramSizeMB = int('{:.0f}'.format(rpi_memory_tuple[0], 10))  # "mem_space_mbytes"
        # used is total - free
        ramUsedMB = int('{:.0f}'.format(rpi_memory_tuple[0] - rpi_memory_tuple[2]), 10)
        ramUsedPercent = int((ramUsedMB / ramSizeMB) * 100)
        rpiData[K_RPI_RAM_USED] = ramUsedPercent  # "mem_used_prcnt"

    rpiCpu = getCPUDictionary()
    if len(rpiCpu) > 0:
        rpiData[K_RPI_CPU] = rpiCpu

    if len(rpi_throttle_status) > 0:
        rpiData[K_RPI_THROTTLE] = rpi_throttle_status

    rpiData[K_RPI_SYSTEM_TEMP] = forceSingleDigit(rpi_system_temp)
    rpiData[K_RPI_GPU_TEMP] = forceSingleDigit(rpi_gpu_temp)
    rpiData[K_RPI_CPU_TEMP] = forceSingleDigit(rpi_cpu_temp)

    rpiData[K_RPI_SCRIPT] = rpi_mqtt_script.replace('.py', '')
    rpiData[K_RPI_SCRIPT_VERSIONS] = ','.join(daemon_version_list)
    rpiData[SCRIPT_REPORT_INTERVAL] = interval_in_minutes

    rpiTopDict = OrderedDict()
    rpiTopDict[K_LD_PAYLOAD_NAME] = rpiData

    _thread.start_new_thread(publishMonitorData, (rpiTopDict, values_topic))


def forceSingleDigit(temperature):
    tempInterp = '{:.1f}'.format(temperature)
    return float(tempInterp)

def getBlockDevicesDictionary():
    rpiDevices = OrderedDict()

    smartctlHelper = os.path.join(os.path.dirname(__file__), 'smartctl-helper')
    stdout, stderr, returncode = invoke_shell_cmd("sudo " + smartctlHelper)
    if returncode != 0:
        print_line('Could not query SMART data: {}'.format(stderr), warning=True)
        return rpiDevices

    for device in stdout.decode('utf-8').splitlines():
        [ name, temp ] = device.split(':')
        if len(temp) > 0:
            rpiDevices[name] = { K_RPI_BLK_DEV_TEMP: float(temp) }
    return rpiDevices


def getDrivesDictionary():
    global rpi_filesystem
    rpiDrives = OrderedDict()

    # tuple { total blocks, used%, mountPoint, device }
    for driveTuple in rpi_filesystem:
        rpiSingleDrive = OrderedDict()
        rpiSingleDrive[K_RPI_DRV_BLOCKS] = int(driveTuple[0])
        rpiSingleDrive[K_RPI_DRV_USED] = int(driveTuple[1])
        device = driveTuple[3]
        if ':' in device:
            rpiDevice = OrderedDict()
            lineParts = device.split(':')
            rpiDevice[K_RPI_DVC_IP] = lineParts[0]
            rpiDevice[K_RPI_DVC_PATH] = lineParts[1]
            rpiSingleDrive[K_RPI_DRV_NFS] = rpiDevice
        else:
            rpiSingleDrive[K_RPI_DRV_DEVICE] = device
            # rpiTest = OrderedDict()
            # rpiTest[K_RPI_DVC_IP] = '255.255.255.255'
            # rpiTest[K_RPI_DVC_PATH] = '/srv/c2db7b94'
            # rpiSingleDrive[K_RPI_DRV_NFS] = rpiTest
        rpiSingleDrive[K_RPI_DRV_MOUNT] = driveTuple[2]
        driveKey = driveTuple[2].replace('/', '-').replace('-', '', 1)
        if len(driveKey) == 0:
            driveKey = "root"
        rpiDrives[driveKey] = rpiSingleDrive

        # TEST NFS
    return rpiDrives


def getNetworkDictionary():
    global rpi_interfaces
    # TYPICAL:
    # rpi_interfaces=[[
    #   ('eth0', 'mac', 'b8:27:eb:1a:f3:bc'),
    #   ('wlan0', 'IP', '192.168.100.189'),
    #   ('wlan0', 'mac', 'b8:27:eb:4f:a6:e9')
    # ]]
    networkData = OrderedDict()

    priorIFKey = ''
    tmpData = OrderedDict()
    for currTuple in rpi_interfaces:
        currIFKey = currTuple[0]
        if priorIFKey == '':
            priorIFKey = currIFKey
        if currIFKey != priorIFKey:
            # save off prior if exists
            if priorIFKey != '':
                networkData[priorIFKey] = tmpData
                tmpData = OrderedDict()
                priorIFKey = currIFKey
        subKey = currTuple[1]
        subValue = currTuple[2]
        tmpData[subKey] = subValue
    networkData[priorIFKey] = tmpData
    print_line('networkData:{}"'.format(networkData), debug=True)
    return networkData


def getMemoryDictionary():
    # TYPICAL:
    #   Tuple (Total, Free, Avail.)
    memoryData = OrderedDict()
    if rpi_memory_tuple != '':
        # TODO: remove free fr
        memoryData[K_RPI_MEM_TOTAL] = round(rpi_memory_tuple[0])
        memoryData[K_RPI_MEM_FREE] = round(rpi_memory_tuple[2])
        memoryData[K_RPI_SWAP_TOTAL] = round(rpi_memory_tuple[3])
        memoryData[K_RPI_SWAP_FREE] = round(rpi_memory_tuple[4])
    # print_line('memoryData:{}"'.format(memoryData), debug=True)
    return memoryData


def getCPUDictionary():
    # TYPICAL:
    #   Tuple (Hardware, Model Name, NbrCores, BogoMIPS, Serial)
    cpuDict = OrderedDict()
    # print_line('rpi_cpu_tuple:{}"'.format(rpi_cpu_tuple), debug=True)
    if rpi_cpu_tuple != '':
        cpuDict[K_RPI_CPU_HARDWARE] = rpi_cpu_tuple[0]
        cpuDict[K_RPI_CPU_MODEL] = rpi_cpu_tuple[1]
        cpuDict[K_RPI_CPU_CORES] = rpi_cpu_tuple[2]
        cpuDict[K_RPI_CPU_BOGOMIPS] = '{:.2f}'.format(rpi_cpu_tuple[3])
        cpuDict[K_RPI_CPU_SERIAL] = rpi_cpu_tuple[4]
        cpuDict[K_RPI_CPU_LOAD1] = rpi_cpu_tuple[5]
        cpuDict[K_RPI_CPU_LOAD5] = rpi_cpu_tuple[6]
        cpuDict[K_RPI_CPU_LOAD15] = rpi_cpu_tuple[7]
    print_line('cpuDict:{}"'.format(cpuDict), debug=True)
    return cpuDict


def publishMonitorData(latestData, topic):
    print_line('Publishing to MQTT topic "{}, Data:{}"'.format(
        topic, json.dumps(latestData)))
    mqtt_client.publish('{}'.format(topic), json.dumps(
        latestData), 1, retain=False)
    sleep(0.5)  # some slack for the publish roundtrip and callback function


def update_values():
    # run get latest values for all
    getDeviceCpuInfo()
    getUptime()
    getFileSystemDrives()
    getSystemTemperature()
    getSystemThermalStatus()
    getLastUpdateDate()
    getDeviceMemory()
    getNetworkIFs()

# -----------------------------------------------------------------------------

# Interrupt handler


def handle_interrupt(channel):
    global reported_first_time
    sourceID = "<< INTR(" + str(channel) + ")"
    current_timestamp = datetime.now(local_tz)
    print_line(sourceID + " >> Time to report! (%s)" %
               current_timestamp.strftime('%H:%M:%S - %Y/%m/%d'), verbose=True)
    # ----------------------------------
    # have PERIOD interrupt!
    update_values()

    if (opt_stall == False or reported_first_time == False and opt_stall == True):
        # ok, report our new detection to MQTT
        _thread.start_new_thread(send_status, (current_timestamp, ''))
        reported_first_time = True
    else:
        print_line(sourceID + " >> Time to report! (%s) but SKIPPED (TEST: stall)" %
                   current_timestamp.strftime('%H:%M:%S - %Y/%m/%d'), verbose=True)


def afterMQTTConnect():
    print_line('* afterMQTTConnect()', verbose=True)
    #  NOTE: this is run after MQTT connects
    # start our interval timer
    startPeriodTimer()
    # do our first report
    handle_interrupt(0)

# TESTING AGAIN
# getNetworkIFs()
# getLastUpdateDate()

# TESTING, early abort
# stopAliveTimer()
# exit(0)


afterMQTTConnect()  # now instead of after?

# check every 12 hours (twice a day) = 12 hours * 60 minutes * 60 seconds
kVersionCheckIntervalInSeconds = (12 * 60 * 60)
# check every 4 hours (6 times a day) = 4 hours * 60 minutes * 60 seconds
kUpdateCheckIntervalInSeconds = (check_interval_in_hours * 60 * 60)

# now just hang in forever loop until script is stopped externally
try:
    while True:
        #  our INTERVAL timer does the work
        sleep(10000)

        timeNow = time()
        if timeNow > daemon_last_fetch_time + kVersionCheckIntervalInSeconds:
            getDaemonReleases()  # and load them!

        if apt_available:
            if timeNow > update_last_fetch_time + kUpdateCheckIntervalInSeconds:
                getNumberOfAvailableUpdates()  # and count them!

finally:
    # cleanup used pins... just because we like cleaning up after us
    publishShuttingDownStatus()
    stopPeriodTimer()   # don't leave our timers running!
    stopAliveTimer()
    mqtt_client.disconnect()
    print_line('* MQTT Disconnect()', verbose=True)

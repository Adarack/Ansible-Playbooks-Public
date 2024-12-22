In this Playbook I merged https://github.com/ironsheep/RPi-Reporter-MQTT2HA-Daemon/pull/149/ and https://github.com/ironsheep/RPi-Reporter-MQTT2HA-Daemon/pull/154 into my local and they are copied from the /files directory. THIS DOES NOT PULL FROM GITHUB

This Ansible Playbook worked in my environment with 12 Raspberry Pi 4's all running Bookworm on 2024-12-21. It will need to be adjusted for your environment.

  You will need to install ansible for this to work. https://docs.ansible.com/

  After cloning this repo you need to will need to

```
cd Ansible-Playbooks-Public/RPi-Reporter-MQTT2HA-Daemon-Custom
```
```
cp /inventory/hosts.yml.example /inventory/hosts.yml
```
```
nano /inventory/hosts.yml
```
Configure the hosts file for your devices. 

ctrl O to save then ctrl X to exit
```
cp /templates/config.ini.j2.example /templates/config.ini.j2
```
```
nano /templates/config.ini.j2
```
edit as required

Ansible will fill in sensor_name = rpi-{{ ansible_hostname }} with the Pi's host name.

Or you could replace rpi-{{ ansible_hostname }} with a custom one.

ctrl and o to save then ctrl x to exit

Next you need to figure out how to edit the smartctl-helper bash script.

This is the original version of the script.
```

#!/bin/bash

smartctl --scan | awk '{ print $1 }' | while read dev; do
    temp="$(smartctl -a $dev | grep "Temperature:" | awk '{ print $2 }')"
    echo "$dev:$temp"
done

```
And here is what I needed for my pi's
```

#!/bin/bash

smartctl --scan | awk '{ print $1 }' | while read dev; do
    temp="$(smartctl -a $dev | grep "Temperature_Celsius" | awk '{ print $10 }')"
    echo "$dev:$temp"
done
```

As you can see I had to change grep "Temperature:" to grep "Temperature_Celsius" I also needed to change the { print $2 } to { print $10 }

To get here I needed to
```
smartctl -a /dev/sda
```
Then in the SMART Attributes Data section I found
```
194 Temperature_Celsius 0x0022 038 038 000 Old_age Always - 38 (Min/Max 10/50)
```
This gives me the value to grep and the location to awk print $. For the awk print you just need to count over each group.
```
 1            2           3     4   5   6     7       8   9 10    11      12
194 Temperature_Celsius 0x0022 038 038 000 Old_age Always - 38 (Min/Max 10/50)
```
Once you have this you can
```
nano smartl-helper
```
And make the required changes. ctrl O to save ctrl X to exit.

Finally
```
ansible-playbook install.yml
```

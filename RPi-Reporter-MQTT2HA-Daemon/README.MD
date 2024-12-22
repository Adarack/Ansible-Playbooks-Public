This Ansible Playbook worked in my environment with 12 Raspberry Pi 4's all running Bookworm on 2024-12-16.  It will need to be adjusted for your environment. 

You will need to install ansible for this to work. https://docs.ansible.com/

After cloning this repo you need to will need to 

cd Ansible-Playbooks-Public/RPi-Reporter-MQTT2HA-Daemon

cp /inventory/hosts.yml.example /inventory/hosts.yml

nano /inventory/hosts.yml

Configure the hosts file for your devices.

ctrl O to save then ctrl X to exit

cp /templates/config.ini.j2.example /templates/config.ini.j2

nano /templates/config.ini.j2

edit as required 
Ansible will fill in sensor_name = rpi-{{ ansible_hostname }} with the Pi's host name.
Or you could replace rpi-{{ ansible_hostname }} with a custom one.

ctrl and o to save then ctrl x to exit

ansible-playbook instal.yml

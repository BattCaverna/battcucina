# battcucina

## Come creare una SD da zero

 - Scaricare l'ultima immagine del Raspberry PI OS Lite
 - Dentro la directory `boot` della SD fare un `touch ssh` per abilitare il server ssh
 - Dentro la directory `boot` della SD creare il file `wpa_supplicant.conf` con questo contenuto:
```
 country=IT
 ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
 update_config=1

 network={
  ssid="<SSID>"
  psk="<PASSWORD>"
 }
```
 
 - Una volta avviata la raspberry da SD:
   - `ssh pi@raspberry`
   - Cambiare la password con `passwd`
   - `vi /etc/hostname` e cambiare l'hostname
   - `sudo apt update`
   - `sudo apt upgrade`
   - `sudo apt install vim git`
   - `mkdir src; cd src`
   - `git clone https://github.com/BattCaverna/battcucina.git`
   - `battcucina/install_dep.sh`
   - `battcucina/install_service.sh`
   - `sudo reboot`
   
## Mettere il filesystem read only:
 - https://medium.com/swlh/make-your-raspberry-pi-file-system-read-only-raspbian-buster-c558694de79

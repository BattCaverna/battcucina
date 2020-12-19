# battcucina

## Come creare una SD

 - Scaricare l'ultima immagine del raspberry pi os
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
   - Cambiare la password con `passwd`
   - Fare un `vi /etc/hostname` e cambiare l'hostname

 
 - Una volta riavviato:
    - `sudo apt update`
    - `sudo apt upgrade`
    - `sudo apt install vim git`
    - `mkdir src; cd src`
    - `git clone `
    - Riavviare `sudo reboot`
    
   
## Raspberry with read only FS:
 - https://medium.com/swlh/make-your-raspberry-pi-file-system-read-only-raspbian-buster-c558694de79

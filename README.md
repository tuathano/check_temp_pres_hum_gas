Environmental monitoring with Raspberry Pi and BME680 and Nagios / NRPE

Python3 script run by NRPE. Assumes the BME680 device is already attached to the Raspberry Pi.

1. Software setup
 
Install the required library:

    sudo pip3 install adafruit-circuitpython-bme680 

Enable i2c:

    sudo raspi-config
    Use the down arrow to select 5 Interfacing Options.
    Arrow down to P5 I2C .
    Select yes when it asks you to enable I2C.
    Also select yes if it asks about automatically loading the kernel module.
    Use the right arrow to select the Finish button.

To correct permission error you need to add your user to i2c group:

    sudo usermod -a -G i2c <username> 

and also nagios / NRPE user:

    sudo usermod -a -G i2c nagios 

Log out and back in for group change to take effect and/or reboot the Raspberry Pi:

    sudo reboot 
    
2. Add NRPE check

Save check_temp_pres_hum_gas.py file to /usr/lib/nagios/plugins/
 
Add to NRPE (/etc/nagios/nrpe.cfg):

command[check_environ]=python3 /usr/lib/nagios/plugins/check_temp_pres_hum_gas.py 12 28 18 25 10 100 20 80 10000 10000000 500000 9000000 900 1070 920 1060 5 1

and restart NRPE:

    sudo /etc/init.d/nagios-nrpe-server restart 
    
3. Add Nagios service (with optional nagiosgraph)

On Nagios server (e.g. add the service definition on frp-nagios01):

define service{
        use                     rp3-service
        host_name               frp-nagios01
        service_description     Enviromental Monitoring BME680
        check_command           check_nrpe!check_environ -t 90 -n
        #action_url              /nagiosgraph/cgi-bin/show.cgi?host=$HOSTNAME$&service=$SERVICEDESC$&geom=1000x200'$.....
        }

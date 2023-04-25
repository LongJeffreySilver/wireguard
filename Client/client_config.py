

#Arg[server_Pu.key, server_public_ip, server_port]

from argparse import Namespace
import fileinput
import subprocess
import sys
import time

class conf_functions:

    def generate_keys(self):
        client_config_file = open("/etc/wireguard/generate_keys.py","r")
        subprocess.Popen("/usr/bin/python3", stdin=client_config_file, shell=True)
        time.sleep(3)
        client_config_file.close()

    def write_config_file(self, server_pub_key,server_pub_ip, server_port):
        client_priv_key_file = open("/etc/wireguard/private_key.key",'r')
        client_priv_key = client_priv_key_file.readline()
        client_priv_key_file.close()

        client_pub_key_file = open("/etc/wireguard/public_key.key.pub",'r')
        client_pub_key = client_pub_key_file.readline()
        client_pub_key_file.close

        client_interface = "wg0"
        client_conf_file = open(client_interface+ ".conf","a")

        client_conf_file.write("[Interface]\n" 
        + "Address = \n" #FIXME Esto lo rellenaria despues
        + "PrivateKey = " + client_priv_key
		+ "DNS = 8.8.8.8\n"## En caso de querer que salga a la red
        + "\n"
		+ "[Peer]\n"
		+ "PublicKey = " + server_pub_key + "\n"
		+ "Endpoint = " + server_pub_ip + ":" + server_port + "\n"
		# Route only vpn trafic through vpn
		#AllowedIPs = 10.8.0.0/24 ## En caso de haber añadido el rango de IPs en el servidor y que todos los servicios estén en ese rango
		# Route ALL traffic through vpn
		+ "AllowedIPs = 0.0.0.0/0\n"
		+ "PersistentKeepalive = 25")
        client_conf_file.close()
        print("Your public key is: " + client_pub_key)

    def finalize_setup(self,priv_ip):
        interface = "wg0"
        client_conf_file = fileinput.input(interface + ".conf", inplace=1)
        for line in client_conf_file:
            if "Address = " in line:
                new_line = "Address = " + priv_ip + "\n"
                old_line = line
                line = line.replace(old_line, new_line)
            sys.stdout.write(line) 
        client_conf_file.close()
        subprocess.Popen(["systemctl", "start", "wg-quick@" + interface])

class client_config:

    def main(args: Namespace) -> None:
        
        #peticion get_data al servidor
        functions = conf_functions()
        functions.generate_keys()
        functions.write_config_file(server_pub_key = args[1],server_pub_ip = args[2], server_port = args[3])
        priv_ip = input("Introduce your private IP: ")
        functions.finalize_setup(priv_ip)
        
    if __name__ == "__main__":
        main(sys.argv)

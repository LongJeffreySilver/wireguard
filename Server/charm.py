#pip install ops

#! /usr/bin/env python3
import fileinput
import time

'''
from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus, BlockedStatus
'''
import subprocess


class wg_services:

    def __init__(self, *args) -> None:
        self.server_name = "wg0"
        self.free_IP_list = list()
        for i in range(1,11):
            ip = "192.168.1."
            aux = 200 + i
            ip = ip + str(aux)
            self.free_IP_list.append(ip)

        """Initialize charm and configure states and events to observe."""
        super().__init__(*args)

    '''
        FIXME Esto se incluye cuando meta el jujucharm en el futuro
        self.framework.observe(self.on.init_config_action, self._on_init_config_action)
        self.framework.observe(self.on.get_server_data_action,self._on_get_server_data_action)
        self.framework.observe(self.on.get_private_IP_action, self._on_get_private_IP_action)
        self.framework.observe(self.on.dissconnect_client_action, self._on_dissconnect_client_action)
        self.framework.observe()

    '''

    def checkInterface(self, interface_list):
        result = subprocess.run(["ls","/sys/class/net"], check=True, capture_output=True, text=True)
        output = result.stdout.split('\n')
        interface = ""
        for interface in output: #Wired: en (enps1, eno1 or ens1) and eth (eth0) | Wifi: wl (wlan wlp)
            if (("en" in interface) or ("wl" in interface)  or ("eth" in interface)) and (len(interface) < 8):
            
                for current_interface in interface_list:
                    if current_interface in interface:
                        interface_path = "/sys/class/net/" + interface + "/operstate"
                        cat_process = subprocess.Popen(["cat", interface_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE,text=True)
                        output,err = cat_process.communicate()
                        interface_status = output.split(sep="\n")
                        if interface_status[0] == "up":
                            return interface                    
        return "-1"

    def generate_keys(self):
        file = open("/etc/wireguard/generate_keys.py","r")
        subprocess.Popen("/usr/bin/python3", stdin=file, shell=True)
        time.sleep(3)
        file.close()


    def _on_init_config_action(self):

        interface_list = ["enp","eno","ens","eth"] #Tipos de redes cableadas
        iface_name = self.checkInterface(interface_list)
        server_listening_port = "41194"
        if(iface_name != None):
            try:
                file_server_priv_key = open("/etc/wireguard/private_key.key",'r')
                server_priv_key = file_server_priv_key.readline()
                file_server_priv_key.close()

                
                conf_file = open("/etc/wireguard/"+ self.server_name + ".conf","w")
                conf_file.write(
                "[Interface]\n"
                + "Address = 192.168.1.200\n"
                + "PrivateKey = " + server_priv_key
                + "ListenPort = " + server_listening_port + "\n"
                + "#PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT; iptables -t nat -A POSTROUTING -o " + iface_name + " -j MASQUERADE\n"## Cambiar la interfaz de red enp0s3 por la que tenga el servidor
                + "#PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT; iptables -t nat -D POSTROUTING -o " + iface_name + "-j MASQUERADE" ## Cambiar la interfaz de red enp0s3 por la que tenga el servidor
                )
                conf_file.close()

                subprocess.Popen(["systemctl", "start", "wg-quick@" + self.server_name])
                time.sleep(5)

                wg_command = subprocess.run(["sudo", "wg"], capture_output=True, text=True)
                wg_text = wg_command.stdout.splitlines()
                print("output:" f"Server started successfully:")
                for param in wg_text:
                    print(param)

                '''event.set_results({
                    "output": f"Server started successfully: \n {wg_text}"
                })'''


            except Exception as e:
                #event.fail(f"Server initiation failed due an unespected exception named: {e}")
                print(f"Server initiation failed due an unespected exception named: {e}")
        else:
            #event.fail(f"Server initiation failed due an unespected exception named: {e}")
            print(f"Server initiation failed due a problem with network interfaces")

    def _on_get_server_data_action(self):
        try:

            wg_command = subprocess.run(["sudo", "wg"], capture_output=True, text=True)
            wg_text = wg_command.stdout.splitlines()
            
            process_dig = subprocess.run(["dig", "+short", "myip.opendns.com", "@resolver1.opendns.com"], capture_output=True, text=True)
            server_public_ip = process_dig.stdout.splitlines()[0] 

            for param in wg_text:
                print(param)
            print("Public IP of the server: " + server_public_ip) #return the first element of the list

            '''event.set_results({
                    "output": f"Server started successfully: \n {wg_text}"
            })'''
        except Exception as e:
            #event.fail(f"Server data failed due an unespected exception named: {e}")
            print(f"Server data failed due an unespected exception named: {e}")


    def _on_get_private_IP_action(self): #El cliente pasa su clave publica y se le genera una IP privada. Ademas, ya se le añade con esa IP privada
        try:
                        
            client_key_string = input("Introduce your public key: ")
            client_ip = self.free_IP_list.pop(0)
            
            server_conf_file = open("/etc/wireguard/"+ self.server_name + ".conf","a")
            new_client = "[Peer]\n" + "PublicKey = " + client_key_string + "\n"+ "AllowedIPs = " + client_ip + "/32\n" + "PersistentKeepAlive = 25\n" + "\n"

            server_conf_file.write(new_client)

            server_conf_file.close()
            time.sleep(5)
            subprocess.Popen(["systemctl", "restart", "wg-quick@" + self.server_name])
            time.sleep(5)

            print("Client added")
            
            '''event.set_results({
                    "output": f"Server started successfully: \n {new_client}"
            })'''
        except Exception as e:
            #event.fail(f"Server data failed due an unespected exception named: {e}")
            print(f"Server data failed due an unespected exception named: {e}")


        def _on_dissconnect_client_action(self): #Si el cliente quiere desconectar su tunel le debe enviar su clave publica y la IP asignada, servidor comprueba parametros, los borra del fichero y actualiza la lista de IPs disponibles
            client_key_string = input("Introduce your public key: ")
            client_priv_ip = input("Introduce your asigned private IP: ")

            with open(self.server_name, "r") as server_conf_file:
                lines = server_conf_file.readlines()

            index = 0
            for line in lines:
                if client_key_string in line:
                    key_index = index
                    if client_priv_ip in lines[key_index+1]:
                        key_index -= 1
                        for i in range(0,5):
                            lines.pop(key_index)
                        continue
                index += 1

            with open(self.server_name, "w") as server_conf_file:
                for line in lines:
                    server_conf_file.write(line)



class charm:

    def main():
        wireguard = wg_services()
        wireguard.generate_keys()
        wireguard._on_init_config_action()
        wireguard._on_get_server_data_action()
        wireguard._on_get_private_IP_action()
        '''
        wireguard._on_dissconnect_client_action()
        '''

    if __name__ == "__main__":
        main()

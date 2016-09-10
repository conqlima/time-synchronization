#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright 2016 Ronitti Juner da S. Rodrigues <ronittijuner@gmail.com>
#                 Robson Araujo Lima            <robson@zeus>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#
import socket
import time
import datetime
import threading
import os
import sys
import pygtk
import pango
pygtk.require("2.0")
import gtk



class TSGUI:
    
    def __init__(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window.set_title("TimeSinc")
        
        menubar = gtk.MenuBar()
        self.init_menu(menubar)
        
        
        
        self.timelbl = gtk.Label()
        self.timelbl.set_size_request(320, 50)
        self.timelbl.set_use_markup(True)
        self.timelbl.modify_font(pango.FontDescription("FreeMono Bold 20"))
        
        
        vbox = gtk.VBox(False)
        
        vbox.add(menubar)
        vbox.add(self.timelbl)
        
        # cria a caixa para lista de ips sincronizados
        self.scrollbox = gtk.ScrolledWindow()
        self.scrollbox.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        vbox.add(self.scrollbox)
        
        
        self.model = gtk.ListStore(str)
        
        treeview = gtk.TreeView(self.model)
        
        col = gtk.TreeViewColumn("Ip's sincronizados")
        treeview.append_column(col)
        cell = gtk.CellRendererText()
        col.pack_start(cell, expand=False)
        col.set_attributes(cell, text=0)
        
        
        
        self.scrollbox.add(treeview)
        self.scrollbox.set_size_request(320, 200)
        
        
        self.statuslbl = gtk.Label()
        self.statuslbl.set_markup('<span foreground="red"><b>Parado</b></span>')
        self.statuslbl.set_size_request(320, 20)
        self.statuslbl.set_use_markup(True)
        
        
        vbox.add(self.statuslbl)
        
        
        
        self.window.add(vbox)
        
        self.window.connect("destroy", self.destroy)
        
        self.window.show_all()
        
    def destroy(self, widget, data=None):
        gtk.main_quit()
        
    def init_menu(self, menubar):
        filemenu = gtk.Menu()
        sfilemenu = gtk.MenuItem("File")
        sfilemenu.set_submenu(filemenu)
        
        sincmenuitem = gtk.ImageMenuItem("Sincronizar")
        exitmenuitem = gtk.ImageMenuItem("Sair")
        filemenu.append(sincmenuitem)
        filemenu.append(exitmenuitem)
        
        aboutmenuitem = gtk.MenuItem("Sobre")
        
        sincmenuitem.set_image(gtk.image_new_from_stock(gtk.STOCK_CONNECT, gtk.ICON_SIZE_MENU))
        exitmenuitem.set_image(gtk.image_new_from_stock(gtk.STOCK_QUIT, gtk.ICON_SIZE_MENU))
        
        
        menubar.append(sfilemenu)
        menubar.append(aboutmenuitem)
        
        sincmenuitem.connect("activate", self.activate_syncronize)
        exitmenuitem.connect("activate", self.destroy)
        aboutmenuitem.connect("activate", self.activate_about)
        
    
    def activate_syncronize(self, widget):
        try:
            TSServer().start()
            TSClient().start()
            self.statuslbl.set_markup('<span foreground="green"><b>Em execução com IP: %s </b></span>' % (get_lan_ip()))
        except:
            print("Error when starting synchronization.")
            
    def activate_about(self, widget):
        about = gtk.AboutDialog()
        about.set_program_name("TimeSinc")
        about.set_version("0.1")
        about.set_copyright("(c) Rônitti J. S. Rodrigues, Robson A. Lima")
        about.set_comments("TimeSinc é um aplicativo para sincronização distribuida de hora")
        about.run()
        about.destroy()
        
    
    
    def update_list_of_ip(self):
        self.model.clear()
        ip_list = TSServer().hosts
        ip_list.sort()
        for ip in ip_list:
            self.model.append([ip])
            
    def auto_update_ip(self):
        while True:
            self.update_list_of_ip()
            time.sleep(1)
            
    def start_update_ip(self):
        try:
            c = threading.Thread(target=self.auto_update_ip, name="GUIListIp")
            c.daemon = True
            c.start()
            print("Listing ip's")
        except:
            print("Error on GUIListIp")
            
    def update_time(self):
        while True:
            self.timelbl.set_text(datetime.datetime.now().strftime('%d/%m/%y %H:%M:%S'))  
            time.sleep(0.05)
            
    def start_update_time(self):
        try:
            c = threading.Thread(target=self.update_time, name="TimeUpdate")
            c.daemon = True
            c.start()
            print("Update Time")
        except:
            print("Error on UpdateTimeLabel")
    
        
        
        


class TSClient:
    
    _inner = None
    
    class inner:
    
        def __init__(self, server_port=3838):
            self.server_port = server_port
            self.run = False
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
        
        def request(self, timeout=1):
            
            self.sock.settimeout(timeout)
            try:
                current_time = time.time()
                time_send = time.time()
                self.sock.sendto(("%0.4f" % current_time).encode(), ('255.255.255.255', self.server_port))
                self.save_log("Client: Sending my time. %0.4f" % current_time)
                data, server = self.sock.recvfrom(1024)
                time_rcv = time.time()
                time_delay = (time_rcv-time_send)/2
                server_time = float(data) #+ time_delay
                current_time = time.time()
                self.save_log("Response:  ServerTime %0.4f - MyTime %0.4f - Delay%0.4f" % (server_time, current_time, time_delay))
                if server_time > current_time:
                    os.system("date -s \"@%0.4f\"" % (server_time))
                    self.save_log("Client: sincronized with %s"  % (server[0]))

            except socket.timeout:
                self.save_log("Client: Time out. No reply.")
                
        def save_log(self, msg):
            os.system("echo \"%s\" >> client.log" % msg)
                
                
        def execute(self):
            while True:
                self.request()
                time.sleep(5)
                
        def start(self):
            try:
                if not self.run: 
                    c = threading.Thread(target=self.execute, name="TSClient")
                    c.daemon = True
                    c.start()
                    self.run = True
                    print("TSClient started.")
            except:
                print("Error when starting TSClient.")

    def __init__(self):
        if TSClient._inner is None:
            TSClient._inner = TSClient.inner()
            
    def __getattr__(self, name):
        return getattr(self._inner, name)
    def __setattr__(self, name, value):
        return setattr(self._inner, name, value)


class TSServer:
    
    _inner = None
    
    class inner:
        
    
        def __init__(self, host='', port=3838):
            self.sock_addr = (host, port)
            self.run = False
            self.hosts = []
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind(self.sock_addr)
            
            self.myip = get_lan_ip();
            
        def waitdata(self):
            while True:
                data, client_addr = self.sock.recvfrom(1024)
                time_from_client = float(data)+0.1
                server_time = time.time()
                
                if str(client_addr)[str(client_addr).find("'")+1:str(client_addr).rfind("'")] != self.myip:
                    self.save_log("Server: %s sent to me %0.4f, mine is %0.4f" % (client_addr[0], time_from_client, server_time))
                    if time_from_client < server_time:
                        self.sock.sendto(("%0.4f" % (time.time())).encode(), client_addr)
                        self.save_log("Server: %s is delayed. I'm answering." % (client_addr[0]))
                    self.add_host(client_addr[0])
                    
                    
        def save_log(self, msg):
            os.system("echo \"%s\" >> server.log" % msg)
                
                
        def start(self):
            try:
                if not self.run:
                    s = threading.Thread(target=self.waitdata, name="TSServer")
                    s.daemon = True
                    s.start()
                    self.run = True
                    print("TSServer started.")
            except:
                print("Error when starting TSServer.")       
            
        def add_host(self, ip):
            if not ip in self.hosts:
                self.hosts.append(ip)
            
    def __init__(self):
        if TSServer._inner is None:
            TSServer._inner = TSServer.inner()
            
    def __getattr__(self, name):
        return getattr(self._inner, name)
    def __setattr__(self, name, value):
        return setattr(self._inner, name, value)


#  
#  name: get_lan_ip()
#  @param 
#  @return ip
#  Função para obter o ip da rede local da maquina de todas as interfaces. 
#  Funciona independente da plataforma.

def get_lan_ip():
    ip = socket.gethostbyname(socket.gethostname())
    if ip.startswith("127.") and os.name != "nt":
        interfaces = ["eth0","eth1","eth2","wlan0","wlan1","wifi0","ath0","ath1","ppp0", "wlp7s0", "enp9s0", "enp2s0"]
        for ifname in interfaces:
            try:
                ip = get_interface_ip(ifname)
                break;
            except IOError:
                pass
    return ip


#  
#  name: get_interface_ip(ifname)
#  @param (ifname)
#  @return
#  Função auxiliar da função get_lan_ip() para obter as interfaces de rede com ip.
#  Funciona independente da plataforma/SO.

if os.name != "nt":
    import fcntl
    import struct
    def get_interface_ip(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', bytes(ifname[:15]))
                # Python 2.7: remove the second argument for the bytes call
            )[20:24])



if __name__ == "__main__":
    
    server = TSServer()
    client = TSClient()
    gui = TSGUI()    
    gui.start_update_ip()
    gui.start_update_time()
    gtk.threads_init()
    gtk.main()
    
  
    


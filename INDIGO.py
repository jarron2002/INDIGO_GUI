import socket
import threading
import time
import xml.etree.ElementTree as ET
import random




class INDIGODevice:
    name = None
    server = None
    properties = None
    
    # Should not be used by the client. The INDIGOServer will create them when receiving
    def __init__(self, name, server):
        self.name = name
        self.server = server
        self.properties = {}
    
    def _parseVectorTag(self, tag):
        name = tag.attrib['name']
        
        #print(self.properties)
        
        if (not name in self.properties):
            self.properties[name] = INDIGOProperty(tag, self)
            
        self.properties[name]._parseVectorTag(tag)
        
    def _parseDelTag(self, tag):
        if "name" in tag.attrib:
            name = tag.attrib['name']
            
            self.properties[name]._delete()
            
            del self.properties[name]
            
        else:   # Remove all properties
            #print(self.properties)
            for prop in self.properties.values():
                prop._delete()
                
            self.properties.clear()
        
        
    def getPropertyByName(self, name):
        return self.properties[name]




        
class INDIGOProperty:
    name = None
    device = None
    propertyType = None
    attributes = None
    elements = None
    listeners = None
    deleteListeners = None
    
    def __init__(self, tag, device):
        self.device = device
        self.name = tag.attrib['name']
        
        if ("Text" in tag.tag):
            self.propertyType = "Text"
        elif ("Number" in tag.tag):
            self.propertyType = "Number"
        elif ("Switch" in tag.tag):
            self.propertyType = "Switch"
        elif ("Light" in tag.tag):
            self.propertyType = "Light"
        elif ("BLOB" in tag.tag):
            self.propertyType = "BLOB"
        
        self.attributes = {}
        self.elements = {}
        self.listeners = []
        self.deleteListeners = []

    # Do not use directly. Add propertyListeners by the method in the INDIGOServer class
    def _addPropertyListener(self, listenerFunct = None, deleteListenerFunct = None):
        if (listenerFunct != None):
            self.listeners.append(listenerFunct)
        if (deleteListenerFunct != None):
            self.deleteListeners.append(deleteListenerFunct)

        if (listenerFunct != None):  # In the moment the listener is added is notified of the status of the property
            listenerFunct(self)

    # Do not use directly. Remove propertyListeners by the method in the INDIGOServer class
    def _removePropertyListener(self, listenerFunct = None, deleteListenerFunct = None):
        self.listeners.remove(listenerFunct)
        self.deleteListeners.remove(deleteListenerFunct)


    def _parseVectorTag(self, tag):
        self.attributes = {**self.attributes, **tag.attrib}     # Merge properties
        
        for elem in tag.findall("./"):
            if (not elem.attrib['name'] in self.elements):
                self.elements[elem.attrib['name']] = INDIGOElement(elem, self)
                
            self.elements[elem.attrib['name']]._parseElementTag(elem)
            
            for f in self.listeners:  # Pasamos los cambios a los listeners
                f(self)



            
    def _delete(self):
        for f in self.deleteListeners:  # Pasamos los cambios a los listeners
            print(f)
            f(self)
            
    def getGroup(self):
        if ('group' in self.attributes):
            return self.attributes['group']
        
        return None
    
    def getLabel(self):
        if ('label' in self.attributes):
            return self.attributes['label']
        
        return None
    
    def getPerm(self):
        if ('label' in self.attributes):
            return self.attributes['perm']
        
        return None
    
    def getState(self):
        if ('state' in self.attributes):
            return self.attributes['state']
        
        return None
    
    def getRule(self):
        if ('rule' in self.attributes):
            return self.attributes['rule']
        
        return None
    
    
    def getTimeout(self):
        if ('timeout' in self.attributes):
            return self.attributes['timeout']
        
        return None
    
    def getTimestamp(self):
        if ('timestamp' in self.attributes):
            return self.attributes['timestamp']
        
        return None
    
    def getMessage(self):
        if ('message' in self.attributes):
            return self.attributes['message']
        
        return None
    
    def getElementByName(self, name):
        return self.elements[name]
    
    def sendValues(self, elementNamesAndValues):           
        message = f'<new{self.propertyType}Vector device="{self.device.name}" name="{self.name}">\n'
        
        for name, value in elementNamesAndValues.items():
            message = message + f'  <one{self.propertyType} name="{name}" target="{value}">{value}</one{self.propertyType}>\n'
            
        message = message + f'</new{self.propertyType}Vector>\n'
        
        #print(message)

        self.device.server._send(message)
        
class INDIGOElement:
    name = None
    prop = None
    attributes = None
    value = None
    
    def __init__(self, tag, prop):
        self.prop = prop
        self.name = tag.attrib['name']
        self.attributes = {}
        self.value = None
        
    def _parseElementTag(self, tag):
        self.attributes = {**self.attributes, **tag.attrib}    # Merge properties
        self.value = tag.text
        
    def getName(self):
        return self.name
    
    def getLabel(self):
        if ('label' in self.attributes):
            return self.attributes['label']
        
        return None
    
    def getFormat(self):
        if ('format' in self.attributes):
            return self.attributes['format']
        
        return None
    
    def getMin(self):
        if ('min' in self.attributes):
            return self.attributes['min']
        
        return None
    
    def getMax(self):
        if ('max' in self.attributes):
            return self.attributes['max']
        
        return None
    
    def getStep(self):
        if ('step' in self.attributes):
            return self.attributes['step']
        
        return None

    def getPath(self):
        if ('path' in self.attributes):
            return self.attributes['path']

        return None

    def getValue(self):
        return self.value
    

    


class INDIGOServerListener:
    def serverConnect(self, server, error = None) -> None:
        pass

    def serverDisconnect(self, server, error = None) -> None:
        pass


class INDIGOServer:
    name = None
    _host = None
    _port = -1
    _sock = None
    _endReading = False
    _thread = None
    devices = None
    serverListeners = None

    pendingPropertyListeners = None

    def __init__(self, name, host, port):
        self.name = name
        self._host = host
        self._port = port
        self._sock = None

        self._endReading = False
        self._thread = None

        self.devices = {}
        self.serverListeners = []
        self.pendingPropertyListeners = []


    def connect(self):
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # Creamos el socket y nos conectamos
            self._sock.connect((self._host, self._port))
            self._sock.settimeout(.01)
            self._endReading = False
        except Exception as err:
            #print(err)
            self._sock = None
            for sl in self.serverListeners:
                sl.serverConnect(self, error = "Error Connecting")

            return

        self._thread = threading.Thread(target=self._readerFunction, args=())
        self._thread.start()

        for sl in self.serverListeners:
            sl.serverConnect(self)

        self.sendGetProperties()


    def getPropertyByName(self, deviceName, propertyName):
        if (deviceName in self.devices):
            d = self.devices[deviceName]

            if (propertyName in d.properties):
                p = d.properties[propertyName]

                return p

        return None

    def isConnected(self):
        if (self._sock != None):
            return True

        return False


    def sendPropertyValues(self, deviceName, propertyName, propertyValues):
        prop = self.getPropertyByName(deviceName, propertyName)

        if (prop != None):

            prop.sendValues(propertyValues)
    
    def sendPropertyValuesAndWait(self, deviceName, propertyName, propertyValues):
        self.sendPropertyValues(deviceName, propertyName, propertyValues)

        prop = self.getPropertyByName(deviceName, propertyName)

        ok = False

        while(not ok):
            ok = True

            for name, value in propertyValues.items():
                element = prop.getElementByName(name)
                val = str(element.getValue())

                #print(element.getName() + " " + val)

                if (val != str(value)):
                    ok = False
            time.sleep(0.001)


    def statusProperty(self, deviceName, propertyName):
        prop = self.getPropertyByName(deviceName, propertyName)
        #print(prop.getState())
        return prop.getState()
        #if (prop.getState() != "Ok"):
        #    time.sleep(0.1)
        #    print(prop.getState())
    
    def waitUntilPropertyOk(self, deviceName, propertyName):
        prop = self.getPropertyByName(deviceName, propertyName)
        print(prop.getState())
        while(prop.getState() != "Ok"):
            print("*")
            time.sleep(0.001)
        print("-")

    def disconnect(self, _error = None):
        if (self._sock != None):
            self._endReading = True

            time.sleep(0.3)

            self._sock.close()
            self._sock = None

        for sl in self.serverListeners:
            sl.serverDisconnect(self, error = _error)

    def addServerListener(self, sl: INDIGOServerListener) -> None:
        self.serverListeners.append(sl)

    def removeServerListener(self, sl: INDIGOServerListener) -> None:
        self.serverListeners.remove(sl)



    def addPropertyListener(self, deviceName, propertyName, listenerFunct = None, deleteListenerFunct = None):
        p = self.getPropertyByName(deviceName, propertyName)

        if (p == None):
            self.pendingPropertyListeners.append([deviceName, propertyName, listenerFunct, deleteListenerFunct])

            #print(self.pendingPropertyListeners)
        else:
            p._addPropertyListener(listenerFunct, deleteListenerFunct)

    def removePropertyListener(self, deviceName, propertyName, listenerFunct = None, deleteListenerFunct = None):
        p = self.getPropertyByName(deviceName, propertyName)

        if (p != None):
            p._removePropertyListener(listenerFunct = listenerFunct, deleteListenerFunct = deleteListenerFunc)


    # Possible values are "Never", "Also", "Only", "URL"
    def sendEnableBlob(self, deviceName, propertyName = None, value = "Never"):
        xml = f"<enableBLOB device='{deviceName}'"

        if (propertyName != None):
            xml = xml + f" name='{propertyName}'"

        xml = xml + f">{value}</enableBLOB>"

        #print(xml)

        self._send(xml)

    def getName(self):
        return self.name

    def getHost(self):
        return self._host

    def getPort(self):
        return self._port

    def getConnectionURL(self):
        return f"http://{self._host}:{self._port}"


    def isConnected(self):
        if (self._sock != None):
            return True

        return False


    def _readerFunction(self):
        parser = ET.XMLPullParser(['end'])

        parser.feed("<xml>\n")

        while(not self._endReading) and (not self.is_socket_closed()):
            msg = ""
            try:
                msg = self._sock.recv(500000).decode("UTF-8")
            except socket.timeout:
                msg = ""
            except:
                pass
                #self.disconnect(_error = "Error reading from socket")

            if (msg != ""):
                parser.feed(msg)
               # print(self.name)
                for event, elem in parser.read_events():
                    if (elem.tag == "defTextVector") or (elem.tag == "defNumberVector") or (elem.tag == "defSwitchVector") or (elem.tag == "defLightVector") or (elem.tag == "defBLOBVector") or (elem.tag == "setTextVector") or (elem.tag == "setNumberVector") or (elem.tag == "setSwitchVector") or (elem.tag == "setLightVector") or (elem.tag == "setBLOBVector"):
                        self._parseVectorTag(elem)
                    elif (elem.tag == "delProperty"):
                        self._parseDelProperty(elem)

            #time.sleep(.01)

        if (self.is_socket_closed()):
            self.disconnect(_error = "Error reading from socket")

    def is_socket_closed(self) -> bool:
        sock = self._sock
        try:
            # this will try to read bytes without blocking and also without removing them from buffer (peek only)
            data = sock.recv(16, socket.MSG_DONTWAIT | socket.MSG_PEEK)
            if len(data) == 0:
                return True
        except BlockingIOError:
            return False  # socket is open and reading from it would block
        except ConnectionResetError:
            return True  # socket was closed for some other reason
        except Exception as e:
            return False
        return False

    def _checkIfPendingPropertyListeners(self, prop):
        toDelete = []

        for p in self.pendingPropertyListeners:
            if (p[0] == prop.device.name) and (p[1] == prop.name):
                #print(p[2])

                prop._addPropertyListener(p[2], p[3])
                toDelete.append(p)

        for p in toDelete:
            self.pendingPropertyListeners.remove(p)



    def _parseVectorTag(self, tag):
        deviceName = tag.attrib['device']

        if not deviceName in self.devices:
            self.devices[deviceName] = INDIGODevice(deviceName, self)

        self.devices[deviceName]._parseVectorTag(tag)


        prop = self.devices[deviceName].getPropertyByName(tag.attrib['name'])

        self._checkIfPendingPropertyListeners(prop)




    def _parseDelProperty(self, tag):
        deviceName = tag.attrib['device']

        if deviceName in self.devices:
            #if ('name' in tag.attrib):
                #prop = self.devices[deviceName].getPropertyByName(tag.attrib['name'])

                #if (prop != None):
                    #pass

            self.devices[deviceName]._parseDelTag(tag)

            if (not 'name' in tag.attrib):        # Delete a whole device
                del self.devices[deviceName]

    def _send(self, command):
        command = command.encode("ASCII")

        if (self._sock != None):
            self._sock.sendall(command)

    def sendGetProperties(self):
        self._send('<getProperties version="2.0" />')
        

    def getDeviceByName(self, name):
        return devices[name]


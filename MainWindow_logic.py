import threading
import time
from MainWindow import MainWindow
from PySide6.QtGui import QFont
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtWidgets import (QHBoxLayout, QVBoxLayout,
    QLabel, QLineEdit, QPushButton, QWidget, QDialog, QDialogButtonBox,
    QMessageBox, QCheckBox, QGroupBox, QScrollArea, QListWidget,
    QAbstractItemView)
from INDIGO import INDIGOServer

class GroupboxDevices(QGroupBox):
    def __init__(self, server:INDIGOServer):
        super().__init__()
        self.server = server
        self.setTitle("Available devices in " + server.name +
        " (" + server.getHost() + ":" + str(server.getPort()) + ")")
        layout = QVBoxLayout()
        self.dict_checkboxes = {}
        self.dict_bool_created_device = {}
        self.bool_scrollbar_created = False
        self.current_device = None
        for device in server.devices.keys():
            self.dict_checkboxes[device] = QCheckBox(device)
            self.dict_bool_created_device[device] = False
            layout.addWidget(self.dict_checkboxes[device])
        self.setLayout(layout)

class ScrollBar_Properties(QScrollArea):
    def __init__(self, groupbox:GroupboxDevices):
        super().__init__()
        self.groupbox = groupbox
        font_bold = QFont()
        label_server = QLabel(groupbox.server.name)
        font_bold.setBold(True)
        label_server.setFont(font_bold)
        self.dict_devices = {}
        self.widget = QWidget()
        self.layout = QVBoxLayout()
        self.layout.addWidget(label_server)
        self.widget.setLayout(self.layout)
        self.setWidget(self.widget)



class MainWindow_logic(MainWindow):
    signal_create_scrollbar_properties = Signal(GroupboxDevices)
    signal_add_device_scrollbar = Signal(ScrollBar_Properties)
    def __init__(self):
        super().__init__()

        self.dict_servers = {}
        self.dict_groupboxes_devices = {}
        self.dict_scrollbars_properties = {}
        self.listwidget_servers = QListWidget()
        self.list_children_scroll_area = []

        self.bool_stop_thread = False
        self.thread_show_scrollbar_properties = threading.Thread(target = self.show_scrollbar_properties)
        self.thread_show_scrollbar_properties.start()

        #Activamos el modo de selección múltiple del listwidget
        self.listwidget_servers.setSelectionMode(QAbstractItemView.
        SelectionMode.ExtendedSelection)

        self.action_servers.triggered.connect(self.listwidget_server)
        self.signal_create_scrollbar_properties.connect(self.create_scrollbar_properties)
        self.signal_add_device_scrollbar.connect(self.add_device_scrollbar)
        self.action_quit.triggered.connect(self.quit)


    def quit(self):
        self.bool_stop_thread = True
        for server in self.dict_servers.values():
            self.disconnect_server(server)
        self.close()

    #Esta función realiza la conexión al servidor que
    #se introduzca. Además, nos muestra tras la conexión
    #si ésta ha sido correcta o no mediante la barra de
    #estado y un mensaje emergente

    def connect_server(self, server:INDIGOServer):
        server.connect()
        time.sleep(1)
        self.connection_info(server)

        #Si se ha conseguido llegar a establecer la conexión,
        #entramos en este bloque
        if server.isConnected():
            self.show_devices(server)
            return True
        else:
            return False

    def listwidget_server(self):
        self.dialog_total = QDialog(self)
        dialog_button_box = QDialogButtonBox()
        layout_total = QVBoxLayout()
        button_add_server = QPushButton("Add server")
        button_server_info = QPushButton("Show server info")
        button_delete_server = QPushButton("Delete server")

        dialog_button_box.addButton(button_add_server, QDialogButtonBox.ButtonRole.ActionRole)
        dialog_button_box.addButton(button_server_info, QDialogButtonBox.ButtonRole.ActionRole)
        dialog_button_box.addButton(button_delete_server, QDialogButtonBox.ButtonRole.ActionRole)
        dialog_button_box.addButton("Cancel", QDialogButtonBox.ButtonRole.RejectRole)
        dialog_button_box.rejected.connect(self.dialog_total.reject)
        button_add_server.clicked.connect(self.add_server_listwidget)
        button_server_info.clicked.connect(self.server_info)
        button_delete_server.clicked.connect(self.del_server_listwidget)

        layout_total.addWidget(self.listwidget_servers)
        layout_total.addWidget(dialog_button_box)
        self.dialog_total.setLayout(layout_total)

        self.dialog_total.open()

    def server_info(self):
        selected_items = self.listwidget_servers.selectedItems()
        for item in selected_items:
            dialog = QDialog()
            dialog_button_box = QDialogButtonBox()
            layout = QVBoxLayout()

            dialog_button_box.addButton("Close", dialog_button_box.ButtonRole.AcceptRole)
            dialog_button_box.accepted.connect(dialog.accept)

            layout.addWidget(QLabel("Name: " + self.dict_servers[item.text()].name))
            layout.addWidget(QLabel("IP address: " + self.dict_servers[item.text()].getHost()))
            layout.addWidget(QLabel("Port: " + str(self.dict_servers[item.text()].getPort())))
            layout.addWidget(dialog_button_box)

            dialog.setLayout(layout)

            dialog.exec()


    def del_server_listwidget(self):
        selected_items = self.listwidget_servers.selectedItems()
        for item in selected_items:
            current_item_row = self.listwidget_servers.row(item)
            self.listwidget_servers.takeItem(current_item_row)
            self.disconnect_server(self.dict_servers[item.text()])
            self.dict_servers.pop(item.text())
            self.dict_groupboxes_devices.pop(item.text())

    #Esta función genera un diálogo para introducir
    #la dirección IP y puerto del servidor INDIGO
    #al que conectarse y añadirlo al listwidget
    def add_server_listwidget(self):
        #Declaración de las variables que se van
        #a usar en la función
        bool_same_servers = False
        list_return = []
        layout_up = QHBoxLayout()
        layout_middle = QHBoxLayout()
        layout_down = QHBoxLayout()
        layout_total = QVBoxLayout()
        line_edit_address = QLineEdit("localhost")
        line_edit_port = QLineEdit("7624")
        line_edit_name = QLineEdit("Test")
        dialog_button_box = QDialogButtonBox()
        dialog = QDialog(self.dialog_total)

        #Añadimos una entrada de línea de texto en el
        #layout superior para la dirección IP
        layout_up.addWidget(QLabel("IP Address:"))
        layout_up.addWidget(line_edit_address)

        #Añadimos una entrada de línea de texto en el
        #layout intermedio para el puerto
        layout_middle.addWidget(QLabel("Port:"))
        layout_middle.addWidget(line_edit_port)

        #Añadimos una entrada de línea de texto en el
        #layout inferior para el nombre
        layout_down.addWidget(QLabel("Name:"))
        layout_down.addWidget(line_edit_name)

        #Añadimos los botones al diálogo y los conectamos
        #con sus respectivas señales de "aceptar" y
        #"rechazar"
        dialog_button_box.addButton("Add and connect", QDialogButtonBox.ButtonRole.AcceptRole)
        dialog_button_box.addButton("Cancel", QDialogButtonBox.ButtonRole.RejectRole)
        dialog_button_box.accepted.connect(dialog.accept)
        dialog_button_box.rejected.connect(dialog.reject)

        #Añadimos los diferentes layouts y la caja de
        #botones del diálogo al layout total del
        #diálogo y configuramos el layout total
        #en el propio diálogo
        layout_total.addLayout(layout_up)
        layout_total.addLayout(layout_middle)
        layout_total.addLayout(layout_down)
        layout_total.addWidget(dialog_button_box)
        dialog.setLayout(layout_total)

        #Hacemos que se muestre el diálogo de manera modal,
        #es decir, no se puede ignorar y que escupa una cadena de caracteres
        #con la dirección IP del servidor de INDIGO y un entero con el
        #puerto de éste, si aceptamos el diálogo
        if dialog.exec():
            server_name = line_edit_name.text()
            server_ip_address = line_edit_address.text()
            server_port = int(line_edit_port.text())
            server = INDIGOServer(server_name, server_ip_address, server_port)
            for connected_server in self.dict_servers.values():
                if (connected_server.getHost() == server.getHost()
                    and connected_server.getPort() == server.getPort()) or (
                    connected_server.name == server_name):
                    bool_same_servers = True
            if bool_same_servers:
                self.popup_same_servers(server)
            else:
                if self.connect_server(server):
                    self.listwidget_servers.addItem(server_name)
                    self.dict_servers[server_name] = server

    def popup_same_servers(self, server:INDIGOServer):
        message_info = QMessageBox.information(self, "Already connected!",
            "There already is an established connection in " + server.getHost() +
            ":" + str(server.getPort()) + " or name\"" + server.name + "\" already in use:")

    #Esta función realiza la desconexión con el servidor,
    #además de actualizar el contenido de la barra de estado,
    #informando sobre el estado actual de la conexión.
    #Al ya no haber conexión a ningún servidor, la acción para
    #desconectarse no es necesaria, por lo que se elimina
    #del menú de acciones
    def disconnect_server(self, server:INDIGOServer):
        server.disconnect()
        self.disconnected_info(server)
        if self.dict_groupboxes_devices[server.name].bool_scrollbar_created:
            self.del_scrollbar_properties(self.dict_groupboxes_devices[server.name])
        self.dict_groupboxes_devices[server.name].deleteLater()

    #Esta función muestra un mensaje de información cuando
    #nos corectamos correctamente a un servidor o un mensaje
    #crítico en caso de no haber podido realizar la conexión
    #con dicho servidor
    def connection_info(self, server:INDIGOServer):
        if server.isConnected():
            QMessageBox.information(self, ("Succesful "
            "connection!"), ("Connected to " + server.getHost()
            + ":" + str(server.getPort())))
        else:
            QMessageBox.warning(self, ("Error "
            "connecting!"), ("Connection failed to " + server.getHost()
            + ":" + str(server.getPort())))

    #Esta función muestra un mensaje cuando nos desconectamos
    #correctamente del servidor
    def disconnected_info(self, server:INDIGOServer):
        QMessageBox.information(self, ("Succesful "
        "disconnection!"), ("Disconnected from " + server.getHost()
        + ":" + str(server.getPort())) + " correctly")

    #Esta función nos permitirá mostrar los distintos
    #dispositivos que están presentes en el servidor
    #de INDIGO al que nos hemos conectado
    def show_devices(self, server:INDIGOServer):
        self.dict_groupboxes_devices[server.name] = GroupboxDevices(server)
        self.layout_devices.insertWidget(0, self.dict_groupboxes_devices[server.name])

    @Slot(ScrollBar_Properties)
    def add_device_scrollbar(self, scrollbar:ScrollBar_Properties):
        widget = QWidget()
        scrollbar.dict_devices[scrollbar.groupbox.current_device] = widget
        layout_device = QVBoxLayout()
        layout_device.addWidget(QLabel('\t' + scrollbar.groupbox.current_device))
        for prop_name, prop in scrollbar.groupbox.server.devices[scrollbar.groupbox.current_device].properties.items():
            layout_device.addWidget(QLabel('\t' + '\t' + prop_name))
            property_type = prop.propertyType
            for elem_name, elem in prop.elements.items():
                layout_element = QHBoxLayout()
                layout_element.addWidget(QLabel('\t' + '\t' + '\t' + elem_name + ": "))
                if (property_type == "Text" or property_type == "Number"):
                    item_elem = QLabel(elem.value)
                elif property_type == "Switch":
                    item_elem = QPushButton(elem.value)
                elif property_type == "Light":
                    item_elem = QLabel(elem.value)
                layout_element.addWidget(item_elem)
                layout_device.addLayout(layout_element)
        widget.setLayout(layout_device)
        scrollbar.layout.addWidget(widget)
        scrollbar.widget.setLayout(scrollbar.layout)
        scrollbar.setWidget(scrollbar.widget)
        scrollbar.setWidgetResizable(True)

    def del_device_scrollbar(self, scrollbar:ScrollBar_Properties):
        scrollbar.dict_devices[scrollbar.groupbox.current_device].deleteLater()
        scrollbar.dict_devices.pop(scrollbar.groupbox.current_device)

    # En esta función, mostaremos las propiedades, elementos
    # y valores de los elementos de los dispositivos
    # seleccionados previamente.
    # También declaramos aquí el widget que los contendrá
    # para poder borrarlo y volver a inicializarlo con
    # nuevos valores para cuando sea necesario
    @Slot(GroupboxDevices)
    def create_scrollbar_properties(self, groupbox: GroupboxDevices):
        groupbox.bool_scrollbar_created = True
        scrollbar = ScrollBar_Properties(groupbox)
        scrollbar.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.dict_scrollbars_properties[groupbox.server.name] = scrollbar
        scrollbar.setLayout(scrollbar.layout)
        self.layout_properties.addWidget(scrollbar)

    def del_scrollbar_properties(self, groupbox:GroupboxDevices):
        self.dict_scrollbars_properties[groupbox.server.name].deleteLater()
        self.dict_scrollbars_properties.pop(groupbox.server.name)
        groupbox.bool_scrollbar_created = False

    def show_scrollbar_properties(self):
        while not self.bool_stop_thread:
            for groupbox in self.dict_groupboxes_devices.values():
                checked_count = self.cb_checked_count(groupbox)
                if checked_count and (not groupbox.bool_scrollbar_created):
                    #Emitimos señal y no llamamos a la función directemente porque
                    #no se puede establecer el padre de un QObject que esté
                    #en un hilo de ejecución diferente
                    self.signal_create_scrollbar_properties.emit(groupbox)
                elif ((not checked_count) and groupbox.bool_scrollbar_created) and (
                    not(self.dict_scrollbars_properties[groupbox.server.name]).dict_devices):
                    self.del_scrollbar_properties(groupbox)
                for device_name, cb in groupbox.dict_checkboxes.items():
                    if cb.isChecked() and (not groupbox.dict_bool_created_device[device_name]):
                        groupbox.current_device = device_name
                        time.sleep(0.1)
                        self.signal_add_device_scrollbar.emit(self.dict_scrollbars_properties[groupbox.server.name])
                        groupbox.dict_bool_created_device[device_name] = True
                    elif (not cb.isChecked()) and groupbox.dict_bool_created_device[device_name]:
                        groupbox.current_device = device_name
                        #time.sleep(0.5)
                        self.del_device_scrollbar(self.dict_scrollbars_properties[groupbox.server.name])
                        groupbox.dict_bool_created_device[device_name] = False
            time.sleep(0.5)

    def cb_checked_count(self, groupbox:GroupboxDevices):
        checked_count = 0
        for cb in groupbox.dict_checkboxes.values():
            if cb.isChecked():
                checked_count += 1
        return checked_count

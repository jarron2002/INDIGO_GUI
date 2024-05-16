import threading
import time

import PySide6.QtCore

from MainWindow import MainWindow
from PySide6.QtGui import (
QAction,
QFont
)
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
QMainWindow,
QHBoxLayout,
QVBoxLayout,
QLabel,
QLineEdit,
QPushButton,
QWidget,
QDialog,
QDialogButtonBox,
QStatusBar,
QMessageBox,
QCheckBox,
QGroupBox,
QScrollArea,
QListWidget,
QListWidgetItem,
QAbstractItemView
)
from INDIGO import (
INDIGOServer,
INDIGODevice
)

class GroupboxDevices(QGroupBox):
    def __init__(self, server:INDIGOServer):
        super().__init__()
        self.server = server
        self.setTitle("Available devices in " + server.name +
        " (" + server._host + ":" + str(server._port) + ")")
        layout = QVBoxLayout()
        self.dict_checkboxes = {}
        self.bool_scrollbar_created = False
        for device in server.devices.keys():
            self.dict_checkboxes[device] = QCheckBox(device)
            layout.addWidget(self.dict_checkboxes[device])
        self.setLayout(layout)

class MainWindow_logic(MainWindow, QMainWindow):
    signal_create_scrollbar_properties = Signal(QGroupBox)
    def __init__(self):
        super().__init__()

        self.dict_servers = {}
        self.dict_groupboxes_devices = {}
        self.dict_scrollbars_properties = {}
        self.listwidget_servers = QListWidget()
        self.list_children_scroll_area = []

        self.bool_stop_thread = False
        self.thread_show_properties = threading.Thread(target = self.show_properties)
        self.thread_show_properties.start()

        #Activamos el modo de selección múltiple del listwidget
        self.listwidget_servers.setSelectionMode(QAbstractItemView.
        SelectionMode.ExtendedSelection)

        self.action_servers.triggered.connect(self.listwidget_server)
        self.signal_create_scrollbar_properties.connect(self.create_scrollbar_properties)
        self.action_quit.triggered.connect(self.quit)


    def quit(self):
        for server in self.dict_servers.values():
            self.disconnect_server(server)
        self.bool_stop_thread = True
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
        dialog_button_box.addButton("Close", QDialogButtonBox.ButtonRole.RejectRole)
        dialog_button_box.rejected.connect(self.dialog_total.reject)
        button_add_server.clicked.connect(self.add_server_listwidget)
        button_server_info.clicked.connect(self.server_info)
        button_delete_server.clicked.connect(self.del_server_listwidget)

        layout_total.addWidget(self.listwidget_servers)
        layout_total.addWidget(dialog_button_box)
        self.dialog_total.setLayout(layout_total)

        self.dialog_total.exec()

    def server_info(self):
        selected_items = self.listwidget_servers.selectedItems()
        for item in selected_items:
            dialog = QDialog()
            dialog_button_box = QDialogButtonBox()
            layout = QVBoxLayout()

            dialog_button_box.addButton("Close", dialog_button_box.ButtonRole.AcceptRole)
            dialog_button_box.accepted.connect(dialog.accept)

            layout.addWidget(QLabel("Name: " + self.dict_servers[item.text()].name))
            layout.addWidget(QLabel("IP address: " + self.dict_servers[item.text()]._host))
            layout.addWidget(QLabel("Port: " + str(self.dict_servers[item.text()]._port)))
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
    #al que conectarse
    def add_server(self):
        #Declaración de las variables que se van
        #a usar en la función
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
        #es decir, no se puede ignorar
        dialog.exec()

        #Escupimos una cadena de caracteres con la dirección IP
        #del servidor de INDIGO y un entero con el puerto de éste
        return line_edit_name.text(), line_edit_address.text(), int(line_edit_port.text())

    def add_server_listwidget(self):
        bool_same_servers = False
        server_name, server_ip_address, server_port = self.add_server()
        server = INDIGOServer(server_name, server_ip_address, server_port)
        for connected_server in self.dict_servers.values():
            if (connected_server._host == server._host
                and connected_server._port == server._port):
                    bool_same_servers = True
        if bool_same_servers:
            self.popup_same_servers(server)
        else:
            if self.connect_server(server):
                self.listwidget_servers.addItem(server_name)
                self.dict_servers[server_name] = server

    def popup_same_servers(self, server:INDIGOServer):
        message_info = QMessageBox.information(self, "Already connected!",
            "There already is an established connection in " + server._host +
            ":" + str(server._port))

    #Esta función realiza la desconexión con el servidor,
    #además de actualizar el contenido de la barra de estado,
    #informando sobre el estado actual de la conexión.
    #Al ya no haber conexión a ningún servidor, la acción para
    #desconectarse no es necesaria, por lo que se elimina
    #del menú de acciones
    def disconnect_server(self, server:INDIGOServer):
        server.disconnect()
        self.disconnected_info(server)
        self.dict_groupboxes_devices[server.name].deleteLater()

    #Esta función muestra un mensaje de información cuando
    #nos corectamos correctamente a un servidor o un mensaje
    #crítico en caso de no haber podido realizar la conexión
    #con dicho servidor
    def connection_info(self, server:INDIGOServer):
        if server.isConnected():
            message_box = QMessageBox.information(self, ("Succesful "
            "connection!"), ("Connected to " + server._host
            + ":" + str(server._port)))
        else:
            message_box = QMessageBox.warning(self, ("Error "
            "connecting!"), ("Connection failed to " + server._host
            + ":" + str(server._port)))

    #Esta función muestra un mensaje cuando nos desconectamos
    #correctamente del servidor
    def disconnected_info(self, server:INDIGOServer):
        message_box = QMessageBox.information(self, ("Succesful "
        "disconnection!"), ("Disconnected from " + server._host
        + ":" + str(server._port)) + " correctly")

    #Esta función nos permitirá mostrar los distintos
    #dispositivos que están presentes en el servidor
    #de INDIGO al que nos hemos conectado

    def show_devices(self, server:INDIGOServer):
        self.dict_groupboxes_devices[server.name] = GroupboxDevices(server)
        self.layout_devices.insertWidget(0, self.dict_groupboxes_devices[server.name])

    #En esta función, mostaremos las propiedades, elementos
    #y valores de los elementos de los dispositivos
    #seleccionados previamente.
    #También declaramos aquí el widget que los contendrá
    #para poder borrarlo y volver a inicializarlo con
    #nuevos valores para cuando sea necesario


    @Slot(QGroupBox)
    def create_scrollbar_properties(self, groupbox_device:GroupboxDevices):
        if not groupbox_device.bool_scrollbar_created:
            scroll_area = QScrollArea()
            self.dict_scrollbars_properties[groupbox_device.server.name] = scroll_area
            font_bold = QFont()
            label_server = QLabel(groupbox_device.server.name)
            font_bold.setBold(True)
            label_server.setFont(font_bold)
            widget = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(label_server)
            widget.setLayout(layout)
            scroll_area.setWidget(widget)
            self.layout_properties.addWidget(scroll_area)
            groupbox_device.bool_scrollbar_created = True

        '''
        for device_name, cb in groupbox_device.dict_checkboxes.items():
            if cb.isChecked():
                layout_device = QVBoxLayout()
                layout_device.addWidget(QLabel('\t' + device_name))
                layout.addLayout(layout_device)
                for prop_name, prop in groupbox_device.server.devices[device_name].properties.items():
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
        self.list_children_scroll_area = self.widget_properties.findChildren(QScrollArea)
        '''


    '''
    def show_properties(self):
        if self.bool_properties_shown:
            scroll_area_children_list = self.widget_properties.findChildren(QScrollArea)
            for child in scroll_area_children_list:
                child.deleteLater()
        for groupbox in self.dict_groupboxes_devices.values():
            self.create_widget_properties(groupbox)
        self.bool_properties_shown = True
    '''

    def show_properties(self):
        while (True and not self.bool_stop_thread):
            for groupbox in self.dict_groupboxes_devices.values():
                if self.any_cb_checked(groupbox):
                    self.signal_create_scrollbar_properties.emit(groupbox)
                elif not self.any_cb_checked(groupbox) and groupbox.bool_scrollbar_created:
                    self.dict_scrollbars_properties[groupbox.server.name].deleteLater()
                    self.dict_scrollbars_properties.pop(groupbox.server.name)
                    groupbox.bool_scrollbar_created = False
            time.sleep(0.5)
            for child in self.list_children_scroll_area:
                self.remove_widget(child)
            self.list_children_scroll_area.clear()


    def any_cb_checked(self, groupbox:GroupboxDevices):
        checked_count = 0
        for cb in groupbox.dict_checkboxes.values():
            if cb.isChecked():
                checked_count += 1
        if checked_count:
            return True
        else:
            return False


    def remove_widget(self, widget:QWidget):
        widget.deleteLater()

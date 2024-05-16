from PySide6.QtWidgets import (
QMainWindow,
QLabel,
QWidget,
QHBoxLayout,
QVBoxLayout,
QMenuBar,
QMenu,
QGroupBox,
QPushButton,
QStatusBar
)
from PySide6.QtGui import QAction

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        #Declaración de las variables
        self.widget_total = QWidget()
        self.layout_total = QHBoxLayout()
        self.menu_bar = QMenuBar()
        self.menu_actions = QMenu("Actions")
        self.action_servers = QAction("Servers...")
        self.action_quit = QAction("Quit app")
        self.widget_devices = QWidget()
        self.layout_devices = QVBoxLayout()
        self.widget_properties = QWidget()
        self.layout_properties = QHBoxLayout()


        #Ajustamos el layout del widget de los dispositivos
        #y añadimos el widget al layout total
        self.widget_devices.setLayout(self.layout_devices)
        self.layout_total.addWidget(self.widget_devices)

        # Ajustamos el layout del widget de las propiedades
        # y añadimos el widget al layout total
        self.widget_properties.setLayout(self.layout_properties)
        self.layout_total.addWidget(self.widget_properties)

        #Ajustamos el título de la ventana
        self.setWindowTitle("INDIGO GUI (testing)")

        #Configuración de las acciones en el menú de acciones
        #La acción de desconectar del servidor se añadirá cuando
        #se realice la pertinente conexión. Por tanto, se hace en
        #MainWindow_logic.py
        self.menu_actions.addAction(self.action_servers)
        self.menu_actions.addAction(self.action_quit)

        #Configuración del menú de acciones en la barra de menús
        self.menu_bar.addMenu(self.menu_actions)

        #Configuración de la barra de menús en la ventana principal
        self.setMenuBar(self.menu_bar)


        #Integramos el layout total en un widget, el cual
        #será el widget central de la ventana principal
        #del programa
        self.widget_total.setLayout(self.layout_total)
        self.setCentralWidget(self.widget_total)
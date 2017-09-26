#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
## PrivateOn-DeployReencrypt -- Because privacy matters
##
## Author: Mstislav Toivonen <matti-toivonen@users.noreply.github.com>
##
## Copyright (C) 2016  PrivateOn / Tietosuojakone Oy, Helsinki, Finland
## Released under the GNU Lesser General Public License
##

##
##  This is the graphical interface for re-encrypting the user's disk. 
##  The application has buttons for adding/deleting key-slots, viewing the header/master-key, 
##  re-encrypting the disk, powering-off/rebooting the computer and launching a terminal window. 
##


import sys, os, time, subprocess
from PyQt5.QtWidgets import QApplication, QInputDialog, QWidget, QDialog, QGridLayout, QHBoxLayout, QVBoxLayout, QComboBox, QProgressBar, QPushButton, QMessageBox, QLabel, QLineEdit, QSizePolicy, qApp
from PyQt5.QtCore    import QCoreApplication, QObject, Qt, pyqtSignal
from PyQt5.QtGui     import QIcon
import encrypt_config
import reencrypt_backend

class MainWindow(QWidget):
    SLOTS_AMOUNT = 8
    PASSWORD1    = ""
    PASSWORD2    = ""
    CACHE        = ""
    ENCRYPT_PART = "No_partition_found"
    ENCRYPT_CONFIG = {}
    LAST_SAVED_MASTERKEY = None
    SLOT_TO_ADD          = None
    SLOT_TO_DELETE       = None


    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUI()

    def initUI(self):
        ##BEGIN Definition of a layout hierarhy from a parent to a child
        self.ltTop               = QHBoxLayout()
        self.ltTopLeftPanel      = QGridLayout()
        self.ltTopRightPanel     = QVBoxLayout()
        self.ltTopRightPanelInfo = QGridLayout()
        ##Nesting layauts in each other
        self.ltTop.addLayout(self.ltTopLeftPanel,1)
        self.ltTop.addLayout(self.ltTopRightPanel,1)
        self.ltTopRightPanel.addLayout(self.ltTopRightPanelInfo)
        self.ltTopRightPanel.addStretch()
        ##END Definition of a layout hierarhy from a parent to a child
        ##BEGIN Definition of visual elements
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(True)
        #
        self.btn_show_master_key = QPushButton('Show master key', self)
        self.btn_add_key         = QPushButton('Add key',         self)
        self.btn_delete_key      = QPushButton('Delete key',      self)
        self.btn_re_encrypt      = QPushButton('Re-encrypt',      self)
        self.btn_do_reboot       = QPushButton('Reboot',          self)
        self.btn_do_poweroff     = QPushButton('Poweroff',        self)
        self.btn_shell           = QPushButton('Shell',           self)
        self.lbl_progress        = QLabel(self)
        self.pbr_progress        = QProgressBar(self)
        self.lbl_space           = QLabel(self)
        #
        self.lbl_keys_info       = QLabel(self)
        self.lbl_header_info     = QLabel(self)
        self.btn_details         = QPushButton('Details', self)
        self.btn_details.setCheckable(True)
        self.lbl_raw_info        = QLabel(self)
        #
        self.btn_show_master_key.setSizePolicy(sizePolicy)
        self.btn_add_key        .setSizePolicy(sizePolicy)
        self.btn_delete_key     .setSizePolicy(sizePolicy)
        self.btn_re_encrypt     .setSizePolicy(sizePolicy)
        self.btn_do_reboot      .setSizePolicy(sizePolicy)
        self.btn_do_poweroff    .setSizePolicy(sizePolicy)
        self.btn_shell          .setSizePolicy(sizePolicy)
        self.lbl_progress       .setSizePolicy(sizePolicy)
        self.pbr_progress       .setSizePolicy(sizePolicy)
        self.lbl_space          .setSizePolicy(sizePolicy)
        # self.lbl_header_info    .setSizePolicy(sizePolicy)
        # self.btn_details        .setSizePolicy(sizePolicy)
        # self.lbl_raw_info       .setSizePolicy(sizePolicy)
        ##END Definition of visual elements
        ##BEGIN Positioning of the elements
        self.ltTopLeftPanel.addWidget(self.btn_show_master_key,  0,0,1,4)
        self.ltTopLeftPanel.addWidget(self.btn_add_key,          1,0,1,2)
        self.ltTopLeftPanel.addWidget(self.btn_delete_key,       1,2,1,2)
        self.ltTopLeftPanel.addWidget(self.lbl_space,            2,0,1,4)
        self.ltTopLeftPanel.addWidget(self.btn_re_encrypt,       3,0,1,4)
        self.ltTopLeftPanel.addWidget(self.btn_do_reboot,        4,0,1,2)
        self.ltTopLeftPanel.addWidget(self.btn_do_poweroff,      4,2,1,2)
        self.ltTopLeftPanel.addWidget(self.lbl_space,            5,0,1,4)
        self.ltTopLeftPanel.addWidget(self.btn_shell,            6,0,1,4)
        self.ltTopLeftPanel.addWidget(self.lbl_space,            7,0,1,4)
        self.ltTopLeftPanel.addWidget(self.lbl_progress,         8,0,1,4)
        self.ltTopLeftPanel.addWidget(self.pbr_progress,         9,0,1,4)
        #
        self.ltTopRightPanelInfo.addWidget(self.lbl_keys_info,   0,0,1,1)
        self.ltTopRightPanelInfo.addWidget(self.lbl_header_info, 1,0,1,1)
        self.ltTopRightPanelInfo.addWidget(self.lbl_raw_info,    2,0,1,1)
        self.ltTopRightPanelInfo.addWidget(self.btn_details,     3,0,1,1)
        #self.ltTopRightPanelInfo.addStretch(1)
        ##END Positioning of the elements
        ##BEGIN Setting up connections between elements and their events handlers
        self.btn_show_master_key.clicked.connect(self.btn_show_master_key_OnClick)
        self.btn_add_key        .clicked.connect(self.btn_add_key_OnClick        ) 
        self.btn_delete_key     .clicked.connect(self.btn_delete_key_OnClick     ) 
        self.btn_re_encrypt     .clicked.connect(self.btn_re_encrypt_OnClick     )      
        self.btn_do_reboot      .clicked.connect(self.btn_do_reboot_OnClick      ) 
        self.btn_do_poweroff    .clicked.connect(self.btn_do_poweroff_OnClick    ) 
        self.btn_shell          .clicked.connect(self.btn_shell_OnClick          ) 
        self.btn_details        .clicked.connect(self.btn_details_OnClick        )                          
        ##END Setting up connections between elements and their events handlers
        self.lbl_keys_info.hide()
        self.lbl_raw_info.hide()
        self.setLayout(self.ltTop)
        self.setWindowTitle('PrivateOn DeployReencrypt')
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.get_encrypted_part()
        self.show_luks_header()
        self.showMaximized()
        #self.show()

    def makeSettingsPopUp(self, pass1_needed=True, pass2_needed=False, add_list=None, delete_list=None):
        self.window_password = SettingsPopUp(self, pass1_needed, pass2_needed, add_list, delete_list)
        val = self.window_password.exec_()
        MainWindow.PASSWORD1      = self.window_password.ldt_pass1.text()
        MainWindow.PASSWORD2      = self.window_password.ldt_pass2.text()
        MainWindow.SLOT_TO_ADD    = int(self.window_password.cbx_keys_to_add.currentText()[-1])    if self.window_password.cbx_keys_to_add.currentText()    else None
        MainWindow.SLOT_TO_DELETE = int(self.window_password.cbx_keys_to_delete.currentText()[-1]) if self.window_password.cbx_keys_to_delete.currentText() else None
    
    def makeErrorPopUp(self, message):
        QMessageBox.critical(self, '!', message, QMessageBox.Ok)
    
    def btn_show_master_key_OnClick(self):
        if MainWindow.CACHE == "":
            self.makeSettingsPopUp()
            MainWindow.CACHE = MainWindow.PASSWORD1
        else:
            MainWindow.PASSWORD1 = MainWindow.CACHE
        # reencrypt_backend.read_master_key(part, password) | return master_key, error_message
        master_key, read_master_key_error_message = reencrypt_backend.read_master_key(MainWindow.ENCRYPT_PART, MainWindow.PASSWORD1)
        if read_master_key_error_message == None:
            if MainWindow.LAST_SAVED_MASTERKEY == None:
                self.lbl_keys_info.setText("Current master key: " + master_key)
                MainWindow.LAST_SAVED_MASTERKEY = master_key
            else:
                self.lbl_keys_info.setText("Previous master key: " + MainWindow.LAST_SAVED_MASTERKEY + "\n" + "Current master key: " + master_key)
                MainWindow.LAST_SAVED_MASTERKEY = master_key
            self.lbl_keys_info.show()
            self.btn_show_master_key.setEnabled(False)
        else:
            self.makeErrorPopUp(read_master_key_error_message)
            MainWindow.CACHE = ""
            self.btn_show_master_key.setEnabled(True)
        
    def btn_add_key_OnClick(self):
        # reencrypt_backend.read_luks_header(part) | return luks_dict, luks_details, error_message
        luks_dict, luks_details, read_luks_header_error_message = reencrypt_backend.read_luks_header(MainWindow.ENCRYPT_PART)
        if read_luks_header_error_message == None:
            slots_to_add = ["Slot " + str(i) for i in range(MainWindow.SLOTS_AMOUNT) if luks_dict['key_slot_' + str(i)] == 'DISABLED']
            if len(slots_to_add) < 1:
                QMessageBox.warning(self, '!', 'You cannot add more keys!', QMessageBox.Ok)
            else:
                if MainWindow.CACHE == "":
                    self.makeSettingsPopUp(pass1_needed=True, pass2_needed=True, add_list=slots_to_add)
                    MainWindow.CACHE = MainWindow.PASSWORD1
                else:
                    self.makeSettingsPopUp(pass1_needed=False, pass2_needed=True, add_list=slots_to_add)
                    MainWindow.PASSWORD1 = MainWindow.CACHE
                # add_key(part, password_current, pasword_new, key_slot) | return error_message   
                add_key_error_message = reencrypt_backend.add_key(MainWindow.ENCRYPT_PART, MainWindow.PASSWORD1, MainWindow.PASSWORD2, MainWindow.SLOT_TO_ADD)
                if add_key_error_message != None:
                    self.makeErrorPopUp(add_key_error_message)
                    MainWindow.CACHE = ""
                self.show_luks_header()
        else:
            self.makeErrorPopUp(read_luks_header_error_message)
        self.show_luks_header()
        
    def btn_delete_key_OnClick(self):
        # reencrypt_backend.read_luks_header(part) | return luks_dict, luks_details, error_message
        luks_dict, luks_details, read_luks_header_error_message = reencrypt_backend.read_luks_header(MainWindow.ENCRYPT_PART)
        if read_luks_header_error_message == None:
            slots_to_delete = ["Slot " + str(i) for i in range(MainWindow.SLOTS_AMOUNT) if luks_dict['key_slot_' + str(i)] == 'ENABLED']
            if len(slots_to_delete) < 2:
                QMessageBox.warning(self, '!', 'You cannot delete more keys!', QMessageBox.Ok)
            else:
                if MainWindow.CACHE == "":
                    self.makeSettingsPopUp(pass1_needed=True, pass2_needed=False, delete_list=slots_to_delete)
                    MainWindow.CACHE = MainWindow.PASSWORD1
                else:
                    self.makeSettingsPopUp(pass1_needed=False, pass2_needed=False, delete_list=slots_to_delete)
                    MainWindow.PASSWORD1 = MainWindow.CACHE
                # delete_key(part, password_current, key_slot) | return error_message 
                delete_key_error_message = reencrypt_backend.delete_key(MainWindow.ENCRYPT_PART, MainWindow.PASSWORD1, MainWindow.SLOT_TO_DELETE)
                if delete_key_error_message != None:
                    self.makeErrorPopUp(delete_key_error_message)
                    MainWindow.CACHE = ""
                self.show_luks_header()
        else:
            self.makeErrorPopUp(read_luks_header_error_message)
        self.show_luks_header()
        
    def btn_re_encrypt_OnClick(self):
        def buttons(enabled):
            self.btn_show_master_key.setEnabled(enabled)
            self.btn_add_key        .setEnabled(enabled)
            self.btn_delete_key     .setEnabled(enabled)
            self.btn_re_encrypt     .setEnabled(enabled)
            self.btn_do_reboot      .setEnabled(enabled)
            self.btn_do_poweroff    .setEnabled(enabled)
            self.btn_details        .setEnabled(enabled)
        buttons(False)
        self.makeSettingsPopUp()
        # reencrypt_backend.preflight_check(part) | return error_message
        preflight_check_error_message = reencrypt_backend.preflight_check(MainWindow.ENCRYPT_PART, MainWindow.PASSWORD1)
        if preflight_check_error_message != None: 
            self.makeErrorPopUp(preflight_check_error_message)
            buttons(True)
            return
        user_answer = QMessageBox.question(self, '!', 'Do you want to re-encrypt?', QMessageBox.Yes, QMessageBox.No)
        if user_answer == QMessageBox.Yes:
            # reencrypt_backend.do_reecnrypt(part, password) | return error_message
            do_reecnrypt_error_message = reencrypt_backend.do_reecnrypt(MainWindow.ENCRYPT_PART, MainWindow.PASSWORD1)
            if do_reecnrypt_error_message != None: 
                self.makeErrorPopUp(do_reecnrypt_error_message)
                buttons(True)
                return
            start_time   = time.time()
            prev_time    = start_time
            prev_percent = 0
            progress = True
            while (progress):
                curr_time = time.time()
                # reencrypt_backend.poll_progress() | return progress_dict, error_message
                progress_dict, poll_progress_error_message = reencrypt_backend.poll_progress()
                if poll_progress_error_message != None and curr_time - start_time > 20:
                    self.makeErrorPopUp(poll_progress_error_message)
                    buttons(True)
                    return
                curr_percent = progress_dict['percent']
                if curr_time - prev_time > 20 and curr_percent == prev_percent:
                    self.makeErrorPopUp("No progress...")
                    buttons(True)
                    return
                self.lbl_progress.setText("; ".join(["%s: %s" % (i,progress_dict[i]) for i in sorted(progress_dict.keys())]))
                self.pbr_progress.setValue(float(curr_percent) * 0.9)
                if curr_percent == 100:
                    self.update_config_file()
                    break
                prev_percent = curr_percent
                prev_time = curr_time
                time.sleep(2)
            time.sleep(10)
            self.pbr_progress.setValue(100)
            self.lbl_keys_info.hide() #hide keys info after the function has completed, as this info is not more actual
            self.show_luks_header()
            buttons(True)

    def btn_do_reboot_OnClick(self):
        user_answer = QMessageBox.question(self, '!', 'Do you want to reboot?', QMessageBox.Yes, QMessageBox.No)
        if user_answer == QMessageBox.Yes:
            # reencrypt_backend.do_reboot() | return error_message
            do_reboot_error_message = reencrypt_backend.do_reboot()
            if do_reboot_error_message != None:
                self.makeErrorPopUp(do_reboot_error_message)
            
    def btn_do_poweroff_OnClick(self):
        user_answer = QMessageBox.question(self, '!', 'Do you want to poweroff?', QMessageBox.Yes, QMessageBox.No)
        if user_answer == QMessageBox.Yes:
            # reencrypt_backend.do_poweroff() | return error_message
            do_poweroff_error_message = reencrypt_backend.do_poweroff()
            if do_poweroff_error_message != None:
                self.makeErrorPopUp(do_poweroff_error_message)
            
    def btn_shell_OnClick(self):
        # open_terminal() | return error_message
        open_terminal_error_message = self.open_terminal()
        if open_terminal_error_message != None:
            self.makeErrorPopUp(open_terminal_error_message)
        
    def btn_details_OnClick(self):
        if self.btn_details.isChecked():
            self.lbl_raw_info.show()
            self.lbl_header_info.hide()
        else:        
            self.lbl_raw_info.hide()
            self.lbl_header_info.show()
            
    def get_encrypted_part(self):
        config, get_encrypted_part_error_message = encrypt_config.get_encrypted_part()
        if config:
            MainWindow.ENCRYPT_CONFIG = config
            if 'encrypt_part' in config:
                MainWindow.ENCRYPT_PART = config['encrypt_part']
            else:        
                self.makeErrorPopUp("Error: Encrypted partition not found in configurtion file.")
        else:        
            self.makeErrorPopUp(get_encrypted_part_error_message)

    def update_config_file(self):
        MainWindow.ENCRYPT_CONFIG['reencrypted'] = "YES"
        update_config_file_error_message = encrypt_config.update_config_file(MainWindow.ENCRYPT_CONFIG)
        if update_config_file_error_message != None: 
            self.makeErrorPopUp(update_config_file_error_message)

    def show_luks_header(self, wait = False):
        # reencrypt_backend.read_luks_header(part) | return luks_dict, luks_details, error_message
        luks_dict, luks_details, read_luks_header_error_message = reencrypt_backend.read_luks_header(MainWindow.ENCRYPT_PART)
        if read_luks_header_error_message == None:
            self.lbl_header_info.setText("\n".join(["%s: %s" % (i,luks_dict[i]) for i in sorted(luks_dict.keys())]))
            self.lbl_raw_info   .setText("\n".join(["%s" % i for i in luks_details]))
        else:
            self.makeErrorPopUp(read_luks_header_error_message)
            
    def open_terminal(self):
        error_message = None
        try:
            subprocess.Popen("gksudo -k -u root xfce4-terminal", shell=True)
        except subprocess.CalledProcessError, err:
            error_message = "Failed with process error: returned non-zero exit status %s" % (str(err.returncode))
            return error_message
        except OSError as err:
            error_message = "Failed with OS error: %s" % (err.strerror)
            return error_message
        except:
            err = sys.exc_info()[1]
            error_message = "Failed with generic error: %s" % (err)
            return error_message
        return error_message

class SettingsPopUp(QDialog):
    def __init__(self, sender, pass1_needed=True, pass2_needed=False, add_list=None, delete_list=None):
        super(SettingsPopUp, self).__init__()
        self.initUI(pass1_needed,pass2_needed,add_list,delete_list)

    def initUI(self, pass1_needed, pass2_needed, add_list, delete_list):
        self.ltTop              = QGridLayout()
        self.ldt_pass1          = QLineEdit()
        self.ldt_pass2          = QLineEdit()
        self.lbl_pass1          = QLabel(self)
        self.lbl_pass2          = QLabel(self)
        self.cbx_keys_to_add    = QComboBox()
        self.cbx_keys_to_delete = QComboBox()
        self.btn_OK             = QPushButton('OK', self)
        self.btn_showhide1      = QPushButton('', self)
        self.btn_showhide2      = QPushButton('', self)
        self.lbl_pass1.setText("Enter any existing password:")
        self.lbl_pass2.setText("Enter new password:")
        self.btn_showhide1.setIcon(QIcon('images/showhide.png'))
        self.btn_showhide2.setIcon(QIcon('images/showhide.png'))
        self.ldt_pass1.setEchoMode(QLineEdit.Password)
        self.ldt_pass2.setEchoMode(QLineEdit.Password)
        self.btn_OK.clicked.connect(self.close)
        self.btn_showhide1.clicked.connect(lambda: self.ldt_pass1.setEchoMode(QLineEdit.Normal) if self.ldt_pass1.echoMode()==QLineEdit.Password else self.ldt_pass1.setEchoMode(QLineEdit.Password))
        self.btn_showhide2.clicked.connect(lambda: self.ldt_pass2.setEchoMode(QLineEdit.Normal) if self.ldt_pass2.echoMode()==QLineEdit.Password else self.ldt_pass2.setEchoMode(QLineEdit.Password))
        self.ltTop.addWidget(self.lbl_pass1,          0,0,1,4)
        self.ltTop.addWidget(self.lbl_pass2,          1,0,1,4)
        self.ltTop.addWidget(self.ldt_pass1,          0,4,1,3)
        self.ltTop.addWidget(self.ldt_pass2,          1,4,1,3)
        self.ltTop.addWidget(self.btn_showhide1,      0,7,1,1)
        self.ltTop.addWidget(self.btn_showhide2,      1,7,1,1)
        self.ltTop.addWidget(self.cbx_keys_to_add,    2,0,1,8)
        self.ltTop.addWidget(self.cbx_keys_to_delete, 3,0,1,8)
        self.ltTop.addWidget(self.btn_OK,             4,3,1,2)
        self.setLayout(self.ltTop)
        if pass1_needed == False:
            self.ldt_pass1.hide()
            self.btn_showhide1.hide()
            self.lbl_pass1.hide()
        else:
            self.ldt_pass1.show()
            self.btn_showhide1.show()
            self.lbl_pass1.show()
        if pass2_needed == False:
            self.ldt_pass2.hide()
            self.btn_showhide2.hide()
            self.lbl_pass2.hide()
        else:
            self.ldt_pass2.show()
            self.btn_showhide2.show()
            self.lbl_pass2.show()
        if add_list != None:
            self.cbx_keys_to_add.addItems(add_list)
            self.cbx_keys_to_add.show()
        else:
            self.cbx_keys_to_add.hide()
        if delete_list != None:
            self.cbx_keys_to_delete.addItems(delete_list)
            self.cbx_keys_to_delete.show()
        else:
            self.cbx_keys_to_delete.hide()
        
        
def main():
    app = QApplication(sys.argv)
    GUI = MainWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

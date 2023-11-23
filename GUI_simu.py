import tkinter as tk
from tkinter import *
from tkinter import messagebox as mb
from tkinter import simpledialog as sd
import os
import time
import threading
from core.src.Monitor import Simulator
import ipdb

simu = Simulator()

def erase_database():
    """erase the whole database and remove all the folders
    """
    global simu
    global label1
    # to remove the whole database
    if not os.path.exists(os.path.join(os.getcwd(), "storage/")) and not os.path.exists(os.path.join(os.getcwd(), "core/config/")):
        mb.showerror(title = "Error",
                    message="Database does not exist.",
                    icon = "error")
        return
    ans = mb.askquestion(title="Warning",
                           message="Once erase you will permanently lose all data. Proceed?",
                           icon="warning")
    if ans == "yes":
        label1.configure(text="Processing...")
        simu.erase_database()
        label1.configure(text="")
        mb.showinfo(title="Info",
                    message="Success!",
                    icon="info")  
        return 0
    else:
        return 1

def create_database():
    """create the disks
    """
    global simu
    global label1
    path = os.path.join(os.getcwd(), "storage")
    if os.path.exists(path):
        if len(os.listdir(path)):
            ans = mb.askquestion(title="Warning",
                           message="Disks already exist. Do you want to recreate?",
                           icon="question")
            if ans == "yes":
                err = erase_database()
                if not err:
                    err = create_database()
                    return err
                else:
                    return err
            else:
                return 1
    disk_num = sd.askinteger(title="Input",
                             prompt="How many disk do you have?:",
                             initialvalue=8,
                             minvalue=4)
    if disk_num == None:
        # label1.configure(text="Database creation cancelled.")
        return 1
    label1.configure(text="Processing...")
    simu.create_database(disk_num)
    label1.configure(text="")
    mb.showinfo(title="Info",
                message="Success!",
                icon="info")
    return 0

def config_database():
    """configure the RAID6
    """
    global simu
    if os.path.exists(os.path.join(os.getcwd(), 'core/config/config.yml')):
        ans = mb.askquestion(title="warning",
                       message="Database configuration already exists.\nRe-configure wil lead to erase dataset.\n Proceed?",
                       icon="warning")
        if ans == "yes":
            err = erase_database() & create_database()
            if not err:
                err = config_database()
                return err
            else:
                return err
        else:
            return 1
    
    if not os.path.exists(os.path.join(os.getcwd(), 'storage')) or len(os.listdir(os.path.join(os.getcwd(), 'storage'))) == 0:
        ans = mb.askquestion(title="Question",
                       message="Need to create database first.\n Proceed?",
                       icon="question")
        if ans == "yes":
            err = create_database()
            if not err:
                err = config_database()
                return err
            else:
                return err
        else:
            return 1
    
    disk_num = len(os.listdir(os.path.join(os.getcwd(), "storage")))
    config = sd.askstring("Input",
                          prompt="\tYou totally have: {} Disks.\n\tPlease input number of:\n\n\tData_Disk,Check_Disk,Word_Length\n\n\t-> Int, no space\n\t-> Data_Disk+Check_Disk={}\n\t-> Word_Length in [1, 2]".format(disk_num, disk_num))
    # read user input and check validity
    # config: [data_num, parity_num, chunk_size]
    if config == None or len(config.split(",")) != 3:
        mb.showerror(title="error",
                    message="Invalid input",
                    icon="error")
        return 1
    config = config.split(",")
    config = [int(i) for i in config]
    if config[0]+config[1] != disk_num:
        mb.showerror(title="error",
                     message="You must use {} disks.\n But your setting {}+{}!={}".format(disk_num, config[0], config[1], disk_num),
                     icon="error")
        return 1
    if config[2] not in [1, 2]:
        mb.showerror(title="error",
                     message="Word Length shall be [1, 2], but your value is {}".format(config[2]),
                     icon="error")
        return 1
    
    label1.configure(text="Processing...")
    simu.set_system_info(disk_num, config[0], config[1], config[2])
    label1.configure(text="")
    mb.showinfo(title="Info",
                message="Success!",
                icon="info")
    return 0
    
def create_disk():
    """create one disk with designate label
    """
    global simu
    disk_id = sd.askinteger(title="Input",
                            prompt="Assign the disk an ID [int]:",
                            initialvalue=1)
    if disk_id == None:
        return 1
    
    if os.path.exists(os.path.join(os.getcwd(), "storage", "disk{}.bin".format(disk_id))):
        mb.showerror(title="error",
                message="Cannot create disk with the same name",
                icon="error")
        return 1
    
    label1.configure(text="Processing...")
    simu.create_disk(disk_id)
    label1.configure(text="")
    mb.showinfo(title="Info",
                message="Success!",
                icon="info")
    return 0

def remove_disk():
    """delete a disk with designated label
    """
    disk_id = sd.askinteger(title="Input",
                        prompt="Identify the disk an ID [int]:",
                        initialvalue=1)
    if disk_id == None:
        return 1
    
    if not os.path.exists(os.path.join(os.getcwd(), "storage", "disk{}.bin".format(disk_id))):
        mb.showerror(title="error",
                message="Disk not exist",
                icon="error")
        return 1    
    
    label1.configure(text="Processing...")
    simu.delete_disk(disk_id)
    label1.configure(text="")
    mb.showinfo(title="Info",
                message="Success!",
                icon="info")
    return 0
    
def callback(evt):
    """fake callback to improve GUI responsiveness
    """
    global root
    name = evt.widget.cget('text')
    if name == "Create Database":
        root.after(50, create_database)    
    elif name == "Erase Database":
        root.after(50, erase_database)
    elif name == "RAID Setting":
        root.after(50, config_database)
    elif name == "Create Disk":
        root.after(50, create_disk)
    elif name == "Remove Disk":
        root.after(50, remove_disk)
        

if __name__ == '__main__':

    root=tk.Tk()
    root.title("Hardware Simulator")
    root.geometry("800x400")  

    # create grid
    frame_lst = []
    for i in range(3):
        root.columnconfigure(i, weight=1, minsize=75)
        root.rowconfigure(i, weight=1, minsize=50)
        for j in range(3):
            frame_lst.append(tk.Frame(
                master=root,
                # relief=tk.RAISED,
                borderwidth=1
            ))
            frame_lst[-1].grid(row=i, column=j, sticky="nsew")

    ###### create elements ######

    # create database
    button1=tk.Button(frame_lst[0], text="Create Database")
    button1.bind("<Button-1>", callback)
    button1.pack(fill="both", expand="True")

    # raid setting
    button2=tk.Button(frame_lst[1], text="RAID Setting")
    button2.bind("<Button-1>", callback)
    button2.pack(fill="both", expand="True")

    # create disk
    button3=tk.Button(frame_lst[2], text="Create Disk")
    button3.bind("<Button-1>", callback)
    button3.pack(fill="both", expand="True")

    # erase whole database
    button4=tk.Button(frame_lst[3], text="Erase Database")
    button4.bind("<Button-1>", callback)
    button4.pack(fill="both", expand="True")

    # information panel
    label1=tk.Label(frame_lst[4], relief="sunken")
    label1.pack(fill="both", expand="True")

    # remove disk
    button5=tk.Button(frame_lst[5], text="Remove Disk")
    button5.bind("<Button-1>", callback)
    button5.pack(fill="both", expand="True")


    root.mainloop()
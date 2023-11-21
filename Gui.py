import tkinter as tk
from tkinter import *
from tkinter import messagebox as mb
import os
import time
# import yaml
from core.src.Monitor import Simulator
from core.src.Controller import Controller

selected_value = []
error_code = []

def get_file_list() -> list:
    file_list = os.listdir(os.path.join(os.getcwd(), "input_data"))
    # print(file_list)
    return file_list

def read_file_list() -> list:
    filepath = os.path.join(os.getcwd(), "core/config/files.csv")
    file_list = []
    with open(filepath, 'r') as f:
        files_info = f.readlines()
    for file in files_info:
        file = file.split(',')
        file_list.append(file[0])
    # print(file_list)
    return file_list
    
def oneselect(evt):
    global selected_value
    w = evt.widget
    value = [w.get(int(i)) for i in w.curselection()]
    if len(value) == 0:
        pass
    else:
        selected_value = value
        print(w, ',' , value)
    
def list_of_file(widget, file_list):
    widget.delete(0,END)
    for f in file_list:
        widget.insert(0, f)

def erase_database():
    global simu
    # to remove the whole database
    simu.erase_database()

    # to create the database
    simu.set_system_info()
    simu.save_system_info()
    simu.create_fake_disk()

def write_file(evt):
    global selected_value
    global lbl_disp
    global lbx_disk
    global rebuild_choice
    
    if len(selected_value) == 0:
        lbl_disp.configure(text="Please select a file and try again!", wraplength=200)
        return
    [err, msg] = cont.process(mode="write", filename=selected_value[0])
    if err == 1:
        rebuild_choice = True
    lbl_disp.configure(text=msg, wraplength=200)
    file_list = read_file_list()
    list_of_file(widget=lbx_disk, file_list=file_list)
    
def read_file(evt):
    global selected_value
    global lbl_disp
    if len(selected_value) == 0:
        lbl_disp.configure(text="Please select a file and try again!", wraplength=200)
        return
    [err, msg] = cont.process(mode="read", filename=selected_value[0])
    # if err == 1:
        # open_popup()
    lbl_disp.configure(text=msg, wraplength=200)

def popup_lose_error():
    global root
    global rebuild_choice

    msg_box = mb.askquestion(title = "Rebuild",
                             message="[ERROR!]\n You may lose one or more disk!\n DON'T PANIC.\n We can restore it! Do you want to proceed?",
                             icon = 'warning',)
    
    if msg_box == 'yes':
        rebuild_choice = True
    else:
        rebuild_choice = False
    # popup.mainloop()

def popup_lose_disaster():
    # global quit

    msg_box = mb.showerror(title = "Error",
                             message="[Disaster Error]\n Sorry lah, your data may have lost permanently!",
                             icon = 'error')
    
    # popup = tk.Tk()
    # popup.wm_title("!")
    # label = tk.Label(popup, text="[Disaster Error] Sorry lah, your data have lost permanently!")
    # label.pack(side="top", fill="x", pady=10)
    # B1 = tk.Button(popup, text="Okay", command = popup.destroy)
    # B1.pack()
    # popup.mainloop()
    # quit = True
    

def refresh_sys(evt):
    global lbx_sys
    file_list = get_file_list()
    list_of_file(widget=lbx_sys, file_list=file_list)
    
def refresh_disk(evt):
    global lbx_disk
    file_list = read_file_list()
    list_of_file(widget=lbx_disk, file_list=file_list)

def on_quit():
    global quit 
    quit = True

quit = False
root = tk.Tk()
root.title("RAID Controller")
root.geometry("800x400")
root.protocol("WM_DELETE_WINDOW", on_quit)

simu = Simulator()
cont = Controller()


frame_disk = tk.Frame(master=root)
frame_disk.pack(fill="both", side="left", expand="True")

frame_disk_sub = tk.Frame(master=frame_disk,
                         height=30)
frame_disk_sub.pack(fill="x", side="top", expand="False")
lbl_sys_info = tk.Label(master=frame_disk_sub, text="File in RAID6 Disk")
lbl_sys_info.pack(side="left", fill="x", expand="True")
btn_sys_info = tk.Button(master=frame_disk_sub, text="Refresh")
btn_sys_info.bind("<Button-1>", refresh_disk)
btn_sys_info.pack(side="right", fill="x", expand="True")

lbx_disk = tk.Listbox(master=frame_disk)
lbx_disk.bind("<<ListboxSelect>>", oneselect)
lbx_disk.pack(fill="both", expand="True")
file_list = read_file_list()
list_of_file(widget=lbx_disk, file_list=file_list)



frame_op = tk.Frame(master=root)
frame_op.pack(fill="both", side="left", expand="True")

frame_disp = tk.Frame(master=frame_op)
frame_disp.pack(fill="both", side="top", expand="True")
lbl_disp = tk.Label(master=frame_disp, 
                    # text = "Status:", 
                    relief="sunken")
lbl_disp.pack(fill="both", expand="True")

frame_btn = tk.Frame(master=frame_op)
frame_btn.pack(fill="both", side="bottom", expand="True")
btn_save = tk.Button(master=frame_btn,
                   text="save\n<-------",
                   height=3)
btn_save.bind("<Button-1>", write_file)
btn_save.pack(fill="x", side="top", expand="True")
btn_read = tk.Button(master=frame_btn,
                   text="read\n------->",
                   height=3)
btn_read.bind("<Button-1>", read_file)
btn_read.pack(fill="x", side="top", expand="True")
btn_read = tk.Button(master=frame_btn,
                   text="Rebuild",
                   height=3)
# btn_read.bind("<Button-1>", read_file)
btn_read.pack(fill="x", side="top", expand="True")





frame_sys = tk.Frame(master=root)
frame_sys.pack(fill="both", side="left", expand="True")

frame_sys_sub = tk.Frame(master=frame_sys,
                         height=30)
frame_sys_sub.pack(fill="x", side="top", expand="False")
lbl_sys_info = tk.Label(master=frame_sys_sub, text="File in System")
lbl_sys_info.pack(side="left", fill="x", expand="True")
btn_sys_info = tk.Button(master=frame_sys_sub, text="Refresh")
btn_sys_info.bind("<Button-1>", refresh_sys)
btn_sys_info.pack(side="right", fill="x", expand="True")

lbx_sys = tk.Listbox(master=frame_sys)
lbx_sys.bind("<<ListboxSelect>>", oneselect)
lbx_sys.pack(side="top", fill="both", expand="True")
file_list = get_file_list()
list_of_file(widget=lbx_sys, file_list=file_list)


# # lbx_disk.bind("<Double-Button>", lambda x: openfolders(lbx_sys.get(lbx_sys.curselection())))
# lbx_disk.bind("<<ListboxSelect>>", oneselect)
# lbx_disk.pack(fill="both", expand="True")
# file_list = read_file_list()
# list_of_file(widget=lbx_disk, file_list=file_list)

rebuild_choice = True
while True: # Only exits, because update cannot be used on a destroyed application
    cont.detect_storage()
    
    if sum(cont.disk_status) < cont.total_num_of_disk - cont.num_check_disk:
        popup_lose_disaster()
        root.destroy()
        cont.save_system_info()
        print("[Disaster Error] Sorry lah, your data have lost permanently!")
        break
    
    if sum(cont.disk_status) < cont.total_num_of_disk and rebuild_choice:
        popup_lose_error()
        print("Disk {} failed! Place replace and rebuild it first!".format(cont.disk_name[~cont.disk_status]))
    
    
    root.update()
    root.update_idletasks()
    time.sleep(0.05)
    if quit:
        # root.destroy()
        cont.save_system_info()
        break
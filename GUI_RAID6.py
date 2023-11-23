import tkinter as tk
from tkinter import *
from tkinter import messagebox as mb
import os
import time
from core.src.Controller import Controller

read_selected = []
write_selected = []
error_code = []

# initialize controller
cont = Controller()

def get_file_list() -> list:
    """get the file within the input path

    Returns:
        list: file list of input path
    """
    file_list = os.listdir(os.path.join(os.getcwd(), "input_data"))
    return file_list

def read_file_list() -> list:
    """get the file inside the RAID6

    Returns:
        list: file list of RAID6
    """
    filepath = os.path.join(os.getcwd(), "core/config/files.csv")
    file_list = []
    with open(filepath, 'r') as f:
        files_info = f.readlines()
    for file in files_info:
        file = file.split(',')
        file_list.append(file[0])
    # print(file_list)
    return file_list
    
def write_select(evt):
    """call back of select a file
    """
    global write_selected
    global read_selected
    global lbl_disp
    w = evt.widget
    write_selected = [w.get(int(i)) for i in w.curselection()]
    if len(write_selected) == 0 and len(read_selected) != 0:
        lbl_disp.configure(text=read_selected, wraplength=200)
    else:
        lbl_disp.configure(text=write_selected, wraplength=200)
    

def read_select(evt):
    """callback of select a file
    """
    global read_selected
    global write_selected
    global lbl_disp
    w = evt.widget
    read_selected = [w.get(int(i)) for i in w.curselection()]
    if len(write_selected) != 0 and len(read_selected) == 0:
        lbl_disp.configure(text=write_selected, wraplength=200)
    else:
        lbl_disp.configure(text=read_selected, wraplength=200)
    
    
def list_of_file(widget, file_list):
    """update file list in box

    Args:
        widget: which box to update
        file_list: file list to display
    """
    selected = [widget.get(int(i)) for i in widget.curselection()]
    widget.delete(0,END)
    for f in file_list:
        widget.insert(END, f)
    [widget.selection_set(file_list.index(filename)) for filename in selected]

def write_file():
    """callback for writing file into RAID6
    """
    global write_selected
    global lbl_disp
    global lbx_disk
    global rebuild_choice
    
    lbl_disp.configure(text="Sure! Processing...", wraplength=200)
    if len(write_selected) == 0:
        lbl_disp.configure(text="Please select a file", wraplength=200)
        return
    [err, msg] = cont.process(mode="write", filename=write_selected)
    if err == 1:
        rebuild_choice = True
    lbl_disp.configure(text=msg, wraplength=200)
    file_list = read_file_list()
    list_of_file(widget=lbx_disk, file_list=file_list)
    
def read_file():
    """callback for reading file from RAID6
    """
    global read_selected
    global lbl_disp
    if len(read_selected) == 0:
        lbl_disp.configure(text="Please select a file", wraplength=200)
        return
    lbl_disp.configure(text="Sure! Processing...", wraplength=200)
    [err, msg] = cont.process(mode="read", filename=read_selected)
    lbl_disp.configure(text=msg, wraplength=200)

def rebuild_file():
    """callback for rebuild the database
    """
    global lbl_disp
    
    lbl_disp.configure(text="No problem! Rebuilding it...", 
                       wraplength=200)
    [err, msg] = cont.process(mode="rebuild", filename=cont.files_info.keys())
    lbl_disp.configure(text=msg, wraplength=200)

def callback(evt):
    """fake callback to call the real callback
    this will improve the GUI's responsiveness
    """
    global root
    name = evt.widget.cget('text')
    if name == "read\n------->":
        root.after(50, read_file)
    elif name == "save\n<-------":
        root.after(50, write_file)
    elif name == "<rebuild>":
        root.after(50, rebuild_file)

def popup_lose_error(lose_num):
    """pop up window of disk lost

    Args:
        lose_num: the lost disks' name
    """
    global root
    global rebuild_choice
    global cont

    lost_disk = cont.disk_name[~cont.disk_status]
    mb.showwarning(title = "Rebuild",
                    message="\n\t{} Lost!\n\tDON'T PANIC.\n\tReplace the disk(s) and click <rebuild>".format(lost_disk),
                    icon = 'warning')
    
    rebuild_choice = False

def popup_lose_disaster():
    """pop up window for too many disks lost
    and the data cannot be restored
    """

    msg_box = mb.showerror(title = "Error",
                             message="[Disaster Error]\n Sorry lah, your data may have lost permanently!",
                             icon = 'error')
    
    

def refresh_sys(evt):
    """refresh user disks' list
    """
    global lbx_sys
    file_list = get_file_list()
    list_of_file(widget=lbx_sys, file_list=file_list)
    
def refresh_disk(evt):
    """refresh RAID file list
    """
    global lbx_disk
    file_list = read_file_list()
    list_of_file(widget=lbx_disk, file_list=file_list)

def on_quit():
    global quit 
    quit = True



if __name__ == '__main__':

    # check path exist or not
    if not os.path.exists(os.path.join(os.getcwd(), 'storage')) or len(os.listdir(os.path.join(os.getcwd(), 'storage'))) == 0:
        mb.showerror(title="error",
                    message="Please create disk first!",
                    icon="error")
        exit()

    if not os.path.exists(os.path.join(os.getcwd(), 'core/config/config.yml')):
        mb.showerror(title="error",
                    message="Database configuration file not found.\nPlease configure the database first!",
                    icon="error")
        exit()

    # create tk window
    quit = False
    root = tk.Tk()
    root.title("RAID Controller")
    root.geometry("800x400")
    root.protocol("WM_DELETE_WINDOW", on_quit)

    ##### create contents in tk windows #####
    
    # create user's disk selectable file list box
    frame_disk = tk.Frame(master=root)
    frame_disk.pack(fill="both", side="left", expand="True")

    frame_disk_sub = tk.Frame(master=frame_disk,
                            height=30)
    frame_disk_sub.pack(fill="x", side="top", expand="False")
    lbl_sys_info = tk.Label(master=frame_disk_sub, text="File in RAID6 Disk")
    lbl_sys_info.pack(side="left", fill="x", expand="True")
    # refresh button
    btn_sys_info = tk.Button(master=frame_disk_sub, text="Refresh")
    btn_sys_info.bind("<Button-1>", refresh_disk)
    btn_sys_info.pack(side="right", fill="x", expand="True")
    # file list
    lbx_disk = tk.Listbox(master=frame_disk, selectmode=EXTENDED, exportselection=False)
    lbx_disk.bind("<<ListboxSelect>>", read_select)
    lbx_disk.pack(fill="both", expand="True")
    file_list = read_file_list()
    list_of_file(widget=lbx_disk, file_list=file_list)

    # create operational button and display window
    frame_op = tk.Frame(master=root)
    frame_op.pack(fill="both", side="left", expand="True")

    # display window
    frame_disp = tk.Frame(master=frame_op)
    frame_disp.pack(fill="both", side="top", expand="True")
    lbl_disp = tk.Label(master=frame_disp, 
                        # text = "Status:", 
                        relief="sunken")
    lbl_disp.pack(fill="both", expand="True")

    # save (write) button
    frame_btn = tk.Frame(master=frame_op)
    frame_btn.pack(fill="both", side="bottom", expand="True")
    btn_save = tk.Button(master=frame_btn,
                    text="save\n<-------",
                    height=3)
    btn_save.bind("<Button-1>", callback)
    btn_save.pack(fill="x", side="top", expand="True")
    # read button
    btn_read = tk.Button(master=frame_btn,
                    text="read\n------->",
                    height=3)
    btn_read.bind("<Button-1>", callback)
    btn_read.pack(fill="x", side="top", expand="True")
    # rebuild button
    btn_read = tk.Button(master=frame_btn,
                    text="<rebuild>",
                    height=3)
    btn_read.bind("<Button-1>", callback)
    btn_read.pack(fill="x", side="top", expand="True")


    # create RAID6 disk selectable file list box
    frame_sys = tk.Frame(master=root)
    frame_sys.pack(fill="both", side="left", expand="True")

    frame_sys_sub = tk.Frame(master=frame_sys,
                            height=30)
    frame_sys_sub.pack(fill="x", side="top", expand="False")
    lbl_sys_info = tk.Label(master=frame_sys_sub, text="File in System")
    lbl_sys_info.pack(side="left", fill="x", expand="True")
    # refresh
    btn_sys_info = tk.Button(master=frame_sys_sub, text="Refresh")
    btn_sys_info.bind("<Button-1>", refresh_sys)
    btn_sys_info.pack(side="right", fill="x", expand="True")
    # file list
    lbx_sys = tk.Listbox(master=frame_sys, selectmode=EXTENDED, exportselection=False)
    lbx_sys.bind("<<ListboxSelect>>", write_select)
    lbx_sys.pack(side="top", fill="both", expand="True")
    file_list = get_file_list()
    list_of_file(widget=lbx_sys, file_list=file_list)


    rebuild_choice = True
    last_disk_num = cont.total_num_of_disk
    while True:
        # iteratively check disk status
        err = cont.detect_storage()
        if err: # check disks fail (would happen if the "storage" folder is removed)
            popup_lose_disaster()
            root.destroy()
            print("[Disaster Error] Hey! What happened?")
            break
        
        # too many disk lost
        if sum(cont.disk_status) < cont.total_num_of_disk - cont.num_check_disk:
            popup_lose_disaster()
            root.destroy()
            cont.save_system_info()
            print("[Disaster Error] Sorry lah, your data have lost permanently!")
            break
        elif sum(cont.disk_status) < last_disk_num: # some disks lost
            lose_num = cont.total_num_of_disk - sum(cont.disk_status)
            last_disk_num = sum(cont.disk_status)
            popup_lose_error(lose_num)
        last_disk_num = sum(cont.disk_status)
        
        root.update()
        root.update_idletasks()
        time.sleep(0.05)
        if quit:
            # root.destroy()
            cont.save_system_info()
            break
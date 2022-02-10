from makichan_decode import *
from tkinter import *
from tkinter import filedialog as fd
import tkinter.messagebox as msgbox
import tkinter.ttk as ttk
import os.path

# not only these formats, formats that supported by pil can be used
Format_List = ["BMP",
"GIF",
"JPG",
"PCX",
"PNG",
"TGA",
"TIFF",
"WebP"]

def cmd_Add():
    files = fd.askopenfilenames(title="Select Files", filetypes=(("MAG File", "*.mag"), ("MAX File", "*.max"), ("MKI File", "*.mki"), ("All Files", "*.*")))
    if files:
        for file in files:
            FileList_ListBox.insert(END, file)

def cmd_Remove():
    files = [FileList_ListBox.get(x) for x in FileList_ListBox.curselection()]
    for file in files:
        FileList_ListBox.delete(FileList_ListBox.get(0, END).index(file))

def cmd_Find():
    directory = fd.askdirectory(title="Select Output Folder")
    if len(directory) > 0:
        Savepath_Entry.delete(0, END)
        Savepath_Entry.insert(0, directory)

def cmd_Convert():
    try:
        files = FileList_ListBox.get(0, END)
        if not files:
            msgbox.showwarning(title="MAKIPie", message="Add MAKI-chan graphics file to convert!")
            return
        path = Savepath_Entry.get()
        if not path:
            msgbox.showwarning(title="MAKIPie", message="Output folder is not set!")
            return
        if path[len(path) - 1] != '/' or path[len(path) - 1] != '\\':
            path += '/'
        formatsel = '.' + Format_Combobox.get().lower()
        errorfiles = []

        for idx, file in enumerate(files):
            f_open = open(file, mode='rb')
            maki = Decode_MAKI(bytearray(f_open.read()))
            f_open.close()
            if type(maki) == str:
                errorfiles.append((os.path.basename(file), maki))
            else:
                maki[0].save(os.path.join(path + os.path.splitext(os.path.basename(file))[0] + formatsel))
            Progress_Bar_var.set(((idx + 1) / len(files)) * 100)
            Progress_Bar.update()

        infomsg = ""
        if errorfiles:
            infomsg = "{0} out of {1} file(s) converted successfully.\n".format(len(files) - len(errorfiles), len(files))
            for errorinfo in errorfiles:
                infomsg += "\n\"{0}\": {1}".format(errorinfo[0], errorinfo[1])
        else:
            infomsg = "File(s) converted successfully.\n"
        msgbox.showinfo(title="MAKIPie", message=infomsg)
    except Exception as err:
        msgbox.showerror(title="MAKIPie", message=err)
    Progress_Bar_var.set(0)
    Progress_Bar.update()

root = Tk()
root.title("MAKIPie")
root.geometry("640x500")

Progress_Bar_var = DoubleVar()

fr_Banner = Frame(root)
banner_image = PhotoImage(file="banner.png")
banner_label = Label(fr_Banner, image=banner_image)
banner_label.pack()

fr_FileButton = Frame(root)
FileButton_Add = Button(fr_FileButton, text="Add File...", padx=18, pady=3, command=cmd_Add)
FileButton_Remove = Button(fr_FileButton, text="Remove Selected", padx=3, pady=3, command=cmd_Remove)
FileButton_Add.pack(side=LEFT, padx=(0, 5))
FileButton_Remove.pack(side=LEFT)

fr_FileList = Frame(root)
FileList_Scrollbar = Scrollbar(fr_FileList)
FileList_ListBox = Listbox(fr_FileList, selectmode="extended", yscrollcommand=FileList_Scrollbar.set)
FileList_Scrollbar.config(command=FileList_ListBox.yview)
FileList_Scrollbar.pack(side=RIGHT, fill=Y)
FileList_ListBox.pack(side=LEFT, fill=BOTH, expand=True)

fr_Output_Sets = Frame(root)

fr_Savepath = LabelFrame(fr_Output_Sets, text="Output Folder")
Savepath_Entry = Entry(fr_Savepath)
Savepath_FindButton = Button(fr_Savepath, text="Find...", padx=7, command=cmd_Find)
Savepath_Entry.pack(side=LEFT, fill=X, expand=True, padx=(3, 0), pady=8)
Savepath_FindButton.pack(side=RIGHT, padx=(10, 3))

fr_Format = LabelFrame(fr_Output_Sets, text="Output Format")
Format_Combobox = ttk.Combobox(fr_Format, values=Format_List, state="readonly")
Format_Combobox.current(0)
Format_Combobox.pack(padx=3, pady=3)

fr_Bottom = Frame(root)

fr_Progress = LabelFrame(fr_Bottom, text="Progress")
Progress_Bar = ttk.Progressbar(fr_Progress, maximum=100, length=515, variable=Progress_Bar_var)
Progress_Bar.pack(padx=3, pady=3)

fr_Convert = Frame(fr_Bottom)
Convert_Button = Button(fr_Convert, text="Convert", padx=25, pady=6, command=cmd_Convert)
Convert_Button.pack()

fr_Banner.pack(padx=4, pady=(4, 25))
fr_FileButton.pack(fill=X, padx=4, pady=5)
fr_FileList.pack(fill=X, padx=4, pady=(0, 5))
fr_Savepath.pack(side=LEFT, fill=X, expand=True, padx=(0, 4))
fr_Format.pack(side=RIGHT, fill=X)
fr_Output_Sets.pack(fill=X, padx=4, pady=(0, 20))
fr_Progress.pack(side=LEFT, fill=X)
fr_Convert.pack(side=RIGHT)
fr_Bottom.pack(fill=X, padx=4)

root.resizable(False, False)
root.mainloop()
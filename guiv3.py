from tkinter import *


def end(): ## EXIT GUI
    root.destroy()


root = Tk()
#root.geometry('{}x{}'.format(800, 480))
#root.attributes("-fullscreen", True)
##Main Frames
Header = Frame(root, height=100, width=800, bg="Blue")
Center = Frame(root, height=285, width=800, bg="green")
Footer = Frame(root, height=95, width=800, bg="red")

#Sub Frames
Info = Frame(Center, height=285, width=176.25, bg="white")
Status = Frame(Center, height=285, width=528.75, bg="black")
Mode = Frame(Center, height=285, width=95, bg="yellow")

## Frame Setup



## Place Frames

Header.pack()
Center.pack()
Footer.pack()
Info.grid(column=0, row=0)
Status.grid(column=1, row=0)
Mode.grid(column=2, row=0)

## Lables
##info_label = Label(Info, text='Label')
##info_label.pack()
##status_label = Label(Info, text='status')
##status_label.pack()
##mode_label = Label(Info, text='mode')
##mode_label.pack()
##header_label = Label(Header, text='header')
##header_label.pack()

## Exit Button

close = Button(Mode, text="Exit", command=end, height=95, width=95, bg="black")

#close.grid(column=0, row=0)

root.mainloop()

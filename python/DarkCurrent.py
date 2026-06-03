import numpy as np
import os
import tkinter
from tkinter import *

import HelperFunction as HF
import WidgetHelper as WH
import UI_Builder as UI


# fd = pathlib.Path(__file__).parent.resolve()
fd = os.getcwd()
Window_Size = [1280, 1280]
fw = int(Window_Size[0]/2)
fh = int(Window_Size[1]/2)
fs = (fw/200, fh/200)
fsPTC = (fw/200, fh/100)

class DarkCurrentAnalysis:
    def __init__(self, window):
        self.window = window
        self.window.title("Frame Averaging and Signal Mean")
        # self.window.config(background='#FFFFFF')
        self.window.geometry(f"{fw+350}x{int(2*fh/3)+100}")
        self.window.resizable(True, True)

        self.filepath = ""
        self.OffsetCalibration = BooleanVar()
        self.dFormat = StringVar()
        self.ImageSize_Row = IntVar()
        self.ImageSize_Col = IntVar()

        self.FOI_Start, self.FOI_End, self.ROI_Left, self.ROI_Right, self.ROI_Up, self.ROI_Dn =\
            IntVar(), IntVar(), IntVar(), IntVar(), IntVar(), IntVar()
        self.read_data = np.array([], dtype=np.float64)
        self.dark_data = np.array([], dtype=np.float64)
        self.frame_average = np.array([], dtype=np.float64)
        self.variance_ij = np.array([], dtype=np.float64)
        self.Average = 0
        self.Sigma = 0

        self.Division_Column, self.Division_Row = IntVar(), IntVar()
        self.PrevMask = BooleanVar()
        self.NIQR, self.NIteration, self.ExcludingZero = DoubleVar(), IntVar(), BooleanVar()

        self.SpatialMask = FALSE
        self.Output = FALSE

        self._build_ui()

    def Open_Path(self):

        self.filepath = WH.ButtonClickedEvent.Open_Path(fd)
        self.label1.configure(text=f"{self.filepath[-40:]}")

    def Read_Image(self):

        Image_Size = [int(self.ImageSize_Row.get()), int(self.ImageSize_Col.get())]
        self.read_data = WH.ButtonClickedEvent.Read_Folder(self.filepath, self.dFormat.get()[1:], np.uint16, Image_Size)

        if not hasattr(self, 'ImageWidget'):
            self.ImageWidget = WH.Plotting.MakeFigureWidget(self.ImagePlotFrame, fs)

        self.InputData = self.read_data.copy()
        self.frame_average = HF.DataProcessing.TemporalAverage(self.InputData)

        WH.Plotting.ShowImage(self.frame_average, self.ImageWidget)
        WH.UIConfiguration.set_text(self.Entry4_1, '1')
        WH.UIConfiguration.set_text(self.Entry4_2, f"{int(len(self.InputData))}")
        WH.UIConfiguration.set_text(self.Entry5_1_1, '0')
        WH.UIConfiguration.set_text(self.Entry5_1_2, f"{int(self.InputData.shape[2]) - 1}")
        WH.UIConfiguration.set_text(self.Entry5_2_1, '0')
        WH.UIConfiguration.set_text(self.Entry5_2_2, f'{int(self.InputData.shape[1]) - 1}')


    def Dark_Image(self):

        Image_Size = [int(self.ImageSize_Row.get()), int(self.ImageSize_Col.get())]

        fpath = WH.ButtonClickedEvent.Open_File(self.filepath)
        self.Label3.configure(text=f"{fpath[-40:]}")

        self.dark_data = WH.ButtonClickedEvent.Read_File(fpath, self.dFormat.get()[1:], np.uint16, Image_Size)
        self.InputData = self.InputData - self.dark_data + 1000
        self.frame_average = HF.DataProcessing.TemporalAverage(self.InputData)
        WH.Plotting.ShowImage(self.frame_average, self.ImageWidget)

    def Show_ROI(self, Frame):

        FOI = np.array([int(self.FOI_Start.get()), int(self.FOI_End.get())])
        ROI1 = np.array([int(self.ROI_Left.get()), int(self.ROI_Dn.get())])
        ROI2 = np.array([int(self.ROI_Right.get()), int(self.ROI_Up.get())])

        Frame = HF.DataProcessing.TemporalAverage(WH.ButtonClickedEvent.Set_FOI(Frame, FOI))
        self.ROI_Data = WH.ButtonClickedEvent.Set_ROI(Frame, ROI1, ROI2)

        if not hasattr(self, 'ROIWidget'):
            self.ROIWidget = WH.Plotting.MakeFigureWidget(self.ROIPlotFrame, fs)

        WH.Plotting.ShowImage(Frame, self.ImageWidget)
        WH.Plotting.ShowImage(self.ROI_Data, self.ROIWidget)

    def ShowBlock(self, ax, Frame, row, col):

        WH.Plotting.DrawDivision(ax, Frame, row, col)

    def Calculate(self, ax, Frame, row, col):

        Frame = HF.DataProcessing.Array2Maskedarray(Frame)
        self.Average = WH.ButtonClickedEvent.Average(ax, Frame, row, col)

        self.Label8_2_1.configure(text=f"{np.format_float_scientific(np.mean(Frame), unique=False, precision=2)}")
        self.Label8_2_2.configure(text=f"{np.format_float_scientific(np.std(Frame), unique=False, precision=2)}")
        self.Output = self.Average[:, np.newaxis]
        # self.Output = np.append(self.Output, axis=1)

    def Apply_IQR(self, ax, Frame, row, col, NIQR, NIteration, ExcZero, MaskExisting, PrevMask):

        Frame = HF.DataProcessing.Array2Maskedarray(Frame)

        if MaskExisting:
            IQR_Frame = Frame
            IQR_Frame.mask = PrevMask

        else:
            IQR_Frame = WH.ButtonClickedEvent.IQR(Frame, NIQR, NIteration, ExcZero)
            self.SpatialMask = IQR_Frame.mask.copy()


        WH.Plotting.ShowImage(IQR_Frame, ax)
        WH.Plotting.DrawDivision(ax, IQR_Frame, row, col)
        Average = WH.ButtonClickedEvent.Average(ax, IQR_Frame, row, col)

        self.Output = np.append(self.Output, Average[:, np.newaxis].copy(), axis=1)
        # self.Output = np.append(self.Output, Sigma[:, np.newaxis].copy(), axis=1)

    def SaveBTNEvent(self, data):

        WH.ButtonClickedEvent.Save_csv(self.filepath, data)

    def SaveClipboardBTNEvent(self, data):
        WH.UIConfiguration.Save2Clipboard(data)

    def _build_ui(self):
        """
        Build Tkinter GUI widgets.
        This GUI was originally developed as a practical engineering tool.
        The widget layout is defined by configuration dictionaries and generated through UI_Builder.UIBuilder.
        """
        self.InputFrame = tkinter.Frame(self.window, width=fw, height=fh+100)
        self.InputFrame.grid(column=0, row=0)
        self.ImagePlotFrame = tkinter.Frame(self.InputFrame, bg='white', width=fw/2, height=fh/2)
        self.ImagePlotFrame.grid(column=0, row=0)
        self.ROIPlotFrame = tkinter.Frame(self.InputFrame, bg='white', width=fw / 2, height=fh / 2)
        self.ROIPlotFrame.grid(column=1, row=0)

        self.InputinfoFrame = tkinter.Frame(self.InputFrame, width=fw, height=100)
        self.InputinfoFrame.grid(column=0, row=1, columnspan = 2)

        self.FrameAddress = {}
        self.ButtonAddress = {}
        self.LabelAddress = {}
        self.EntryAddress = {}
        self.ComboBoxAddress = {}
        self.CheckButtonAddress = {}

        # ------------------------------------------------------------
        # Control frames
        # ------------------------------------------------------------
        FrameInfos = [
            {"name": "ReadFrame", "row": 0, "col": 0, "top_minsize": 20},
            {"name": "DarkFileFrame", "row": 0, "col": 1, "top_minsize": 20},
            {"name": "FrameFrame", "row": 0, "col": 2, "top_minsize": 20},
            {"name": "ROIFrame", "row": 0, "col": 3, "top_minsize": 20},
            {"name": "SummaryFrame", "row": 0, "col": 4, "top_minsize": 20},
            {"name": "DivisionFrame", "row": 0, "col": 5, "top_minsize": 20},
            {"name": "CalculateFrame", "row": 0, "col": 6, "top_minsize": 20},
            {"name": "IQRFrame", "row": 0, "col": 7, "top_minsize": 20},
            {"name": "SaveFrame", "row": 0, "col": 8, "top_minsize": 20},
        ]

        for frame_info in FrameInfos:
            UI.UIBuilder.make_control_frame(self, self.InputinfoFrame, frame_info)

        # ------------------------------------------------------------
        # Labels
        # ------------------------------------------------------------
        LabelInfos = [
            # ReadFrame
            {"parent": self.ReadFrame, "name": "label1", "text": "", "row": 0, "col": 0, "columnspan": 4},
            {"parent": self.ReadFrame, "name": "Label1_1", "text": "Image Size(Row, Col)", "row": 2, "col": 0, "columnspan": 2},
            {"parent": self.ReadFrame, "name": "Label1_2", "text": "Offset Calibration", "row": 3, "col": 0, "columnspan": 2},
            {"parent": self.ReadFrame, "name": "Label1_3", "text": "Format", "row": 4, "col": 0, "columnspan": 2},

            # DarkFileFrame
            {"parent": self.DarkFileFrame, "name": "Label3", "text": "", "row": 0, "col": 0, "columnspan": 2},

            # SummaryFrame - title labels
            {"parent": self.SummaryFrame, "name": "Label6_1_1", "text": "Image Size", "row": 2, "col": 0},
            {"parent": self.SummaryFrame, "name": "Label6_2_1", "text": "Frame", "row": 3, "col": 0},
            {"parent": self.SummaryFrame, "name": "Label6_3_1", "text": "ROI(Left, Right)", "row": 4, "col": 0},
            {"parent": self.SummaryFrame, "name": "Label6_4_1", "text": "ROI(Down, Up)", "row": 5, "col": 0},

            # SummaryFrame - value labels
            {"parent": self.SummaryFrame, "name": "Label6_1_2", "textvariable": self.ImageSize_Row, "row": 2, "col": 1},
            {"parent": self.SummaryFrame, "name": "Label6_1_3", "textvariable": self.ImageSize_Col, "row": 2, "col": 2},
            {"parent": self.SummaryFrame, "name": "Label6_2_2", "textvariable": self.FOI_Start, "row": 3, "col": 1},
            {"parent": self.SummaryFrame, "name": "Label6_2_3", "textvariable": self.FOI_End, "row": 3, "col": 2},
            {"parent": self.SummaryFrame, "name": "Label6_3_2", "textvariable": self.ROI_Left, "row": 4, "col": 1},
            {"parent": self.SummaryFrame, "name": "Label6_3_3", "textvariable": self.ROI_Right, "row": 4, "col": 2},
            {"parent": self.SummaryFrame, "name": "Label6_4_2", "textvariable": self.ROI_Dn, "row": 5, "col": 1},
            {"parent": self.SummaryFrame, "name": "Label6_4_3", "textvariable": self.ROI_Up, "row": 5, "col": 2},

            # DivisionFrame
            {"parent": self.DivisionFrame, "name": "Label7_1_1", "text": "Column", "row": 2, "col": 0},
            {"parent": self.DivisionFrame, "name": "Label7_2_1", "text": "Row", "row": 3, "col": 0},

            # CalculateFrame
            {"parent": self.CalculateFrame, "name": "Label8_1_1", "text": "Mean", "row": 2, "col": 0},
            {"parent": self.CalculateFrame, "name": "Label8_1_2", "text": "stddev", "row": 3, "col": 0},
            {"parent": self.CalculateFrame, "name": "Label8_2_1", "text": "", "row": 2, "col": 1},
            {"parent": self.CalculateFrame, "name": "Label8_2_2", "text": "", "row": 3, "col": 1},

            # IQRFrame
            {"parent": self.IQRFrame, "name": "Label9_1_1", "text": "IQR", "row": 2, "col": 0},
            {"parent": self.IQRFrame, "name": "Label9_2_1", "text": "Iterations", "row": 3, "col": 0},
            {"parent": self.IQRFrame, "name": "Label9_3_1", "text": "Excluding 0", "row": 4, "col": 0},
        ]

        for label_info in LabelInfos:
            UI.UIBuilder.make_label(self, label_info)

        # ------------------------------------------------------------
        # Entries
        # ------------------------------------------------------------
        EntryInfos = [
            # ReadFrame
            {"parent": self.ReadFrame, "name": "Entry2_1_1", "textvariable": self.ImageSize_Row, "default": 1280, "row": 2, "col": 2, "width": 4},
            {"parent": self.ReadFrame, "name": "Entry2_1_2", "textvariable": self.ImageSize_Col, "default": 1280, "row": 2, "col": 3, "width": 4},

            # FrameFrame
            {"parent": self.FrameFrame, "name": "Entry4_1", "textvariable": self.FOI_Start, "default": 0, "row": 2, "col": 0, "width": 4},
            {"parent": self.FrameFrame, "name": "Entry4_2", "textvariable": self.FOI_End, "default": 0, "row": 2, "col": 1, "width": 4},

            # ROIFrame
            {"parent": self.ROIFrame, "name": "Entry5_1_1", "textvariable": self.ROI_Left, "default": 0, "row": 2, "col": 0, "width": 4},
            {"parent": self.ROIFrame, "name": "Entry5_1_2", "textvariable": self.ROI_Right, "default": 0, "row": 2, "col": 1, "width": 4},
            {"parent": self.ROIFrame, "name": "Entry5_2_1", "textvariable": self.ROI_Dn, "default": 0, "row": 3, "col": 0, "width": 4},
            {"parent": self.ROIFrame, "name": "Entry5_2_2", "textvariable": self.ROI_Up, "default": 0, "row": 3, "col": 1, "width": 4},

            # DivisionFrame
            {"parent": self.DivisionFrame, "name": "Entry7_1_2", "textvariable": self.Division_Column, "row": 2, "col": 1, "width": 4},
            {"parent": self.DivisionFrame, "name": "Entry7_2_2", "textvariable": self.Division_Row, "row": 3, "col": 1, "width": 4},

            # IQRFrame
            {"parent": self.IQRFrame, "name": "Entry9_1_2", "textvariable": self.NIQR, "row": 2, "col": 1, "width": 4},
            {"parent": self.IQRFrame, "name": "Entry9_2_2", "textvariable": self.NIteration, "row": 3, "col": 1, "width": 4},
        ]

        for entry_info in EntryInfos:
            UI.UIBuilder.make_entry(self, entry_info)

        # ------------------------------------------------------------
        # ComboBox
        # ------------------------------------------------------------
        ComboBoxInfos = [
            {"parent": self.ReadFrame, "name": "FormatCBox", "textvariable": self.dFormat, "values": [" raw", " tif", " bin"], "default": " raw", "row": 4, "col": 2, "columnspan": 2, "width": 4, "state": "readonly"},
        ]

        for combo_info in ComboBoxInfos:
            UI.UIBuilder.make_combobox(self, combo_info)

        # ------------------------------------------------------------
        # Buttons
        # ------------------------------------------------------------
        ButtonInfos = [
            {"parent": self.ReadFrame, "name": "Button1", "text": "Open File", "command": self.Open_Path, "row": 1, "col": 0},
            {"parent": self.ReadFrame, "name": "Button2", "text": "Read File", "command": self.Read_Image, "row": 1, "col": 1, "columnspan": 3},

            {"parent": self.DarkFileFrame, "name": "Button3", "text": "Dark File", "command": self.Dark_Image, "row": 1, "col": 0, "columnspan": 2},

            {"parent": self.FrameFrame, "name": "Button4", "text": "Frame", "row": 1, "col": 0, "columnspan": 2, "state": "disabled"},
            {"parent": self.ROIFrame, "name": "Button5", "text": "ROI (Left, Right\nDown, Up)", "row": 1, "col": 0, "columnspan": 2, "state": "disabled"},

            {"parent": self.SummaryFrame, "name": "Button6", "text": "Show ROI", "command": lambda: self.Show_ROI(self.InputData.copy()), "row": 1, "col": 0, "columnspan": 3},

            {"parent": self.DivisionFrame, "name": "Button7", "text": "Division", "command": lambda: self.ShowBlock(self.ROIWidget, self.ROI_Data.copy(), int(self.Division_Row.get()), int(self.Division_Column.get())), "row": 1, "col": 0, "columnspan": 2},

            {"parent": self.CalculateFrame, "name": "Button8", "text": "Calculate", "command": lambda: self.Calculate(self.ROIWidget, self.ROI_Data.copy(), int(self.Division_Row.get()), int(self.Division_Column.get())), "row": 1, "col": 0, "columnspan": 2},

            {"parent": self.CalculateFrame, "name": "Button8_3_2", "text": "Use Previous",
             "command": lambda: self.Apply_IQR(self.ROIWidget, self.ROI_Data.copy(), int(self.Division_Row.get()), int(self.Division_Column.get()), self.NIQR.get(), self.NIteration.get(), self.ExcludingZero.get(), self.PrevMask.get(), self.SpatialMask), "row": 4, "col": 1, "state": "disabled"},

            {"parent": self.IQRFrame, "name": "Button9", "text": "Spatial IQR",
             "command": lambda: self.Apply_IQR(self.ROIWidget, self.ROI_Data.copy(), int(self.Division_Row.get()), int(self.Division_Column.get()), self.NIQR.get(), self.NIteration.get(), self.ExcludingZero.get(), self.PrevMask.get(), self.SpatialMask), "row": 1, "col": 0, "columnspan": 2},

            {"parent": self.SaveFrame, "name": "Button10", "text": "Save Image", "command": lambda: self.SaveBTNEvent(self.Output), "row": 1, "col": 0},
            {"parent": self.SaveFrame, "name": "Button10_2", "text": "Save Clipboard", "command": lambda: self.SaveClipboardBTNEvent(self.Output), "row": 2, "col": 0},
        ]

        for button_info in ButtonInfos:
            UI.UIBuilder.make_button(self, button_info)

        # ------------------------------------------------------------
        # CheckButtons
        # ------------------------------------------------------------
        CheckButtonInfos = [
            {"parent": self.ReadFrame, "name": "CheckButton2_2", "text": "", "variable": self.OffsetCalibration, "command": lambda: WH.UIConfiguration.ButtonState([self.Button3], self.OffsetCalibration.get()), "row": 3, "col": 2, "columnspan": 2},

            {"parent": self.CalculateFrame, "name": "CheckButton8_3_1", "text": "", "variable": self.PrevMask,
             "command": lambda: [WH.UIConfiguration.ButtonState([self.Button8_3_2], self.PrevMask.get()), WH.UIConfiguration.ButtonState([self.Button9, self.Entry9_1_2, self.Entry9_2_2], not self.PrevMask.get())], "row": 4, "col": 0},

            {"parent": self.IQRFrame, "name": "CheckButton9_3_2", "text": "", "variable": self.ExcludingZero, "row": 4, "col": 1},
        ]

        for checkbutton_info in CheckButtonInfos:
            UI.UIBuilder.make_checkbutton(self, checkbutton_info)

        # ------------------------------------------------------------
        # Initial states
        # ------------------------------------------------------------
        self.CheckButton2_2.select()
        self.Button8_3_2["state"] = "disabled"

        # col = 0
        #
        # Entry1Span = 1
        # self.label1 = tkinter.Label(self.InputinfoFrame)
        # self.label1.grid(column=col, row=1, columnspan=3)
        # self.Button1 = tkinter.Button(self.InputinfoFrame, text='Open File', command=self.Open_Path)
        # self.Button1.grid(column=col, row=2)
        # self.Label1_1 = tkinter.Label(self.InputinfoFrame, text='Image Size(Row, Col)')
        # self.Label1_1.grid(column=col, row=3)
        # self.Label1_2 = tkinter.Label(self.InputinfoFrame, text='Offset Calibration')
        # self.Label1_2.grid(column=col, row=4)
        # self.Label1_3 = tkinter.Label(self.InputinfoFrame, text = 'Format')
        # self.Label1_3.grid(column=col, row=5)
        # col = col + Entry1Span
        #
        # Entry2Span = 2
        # self.Button2 = tkinter.Button(self.InputinfoFrame, text='Read File', command=self.Read_Image)
        # self.Button2.grid(column=col, row=2, columnspan=Entry2Span)
        # self.Entry2_1_1 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.ImageSize_Row, relief="ridge")
        # self.Entry2_1_1.grid(column=col, row=3)
        # WH.UIConfiguration.set_text(self.Entry2_1_1, '1280')
        # self.Entry2_1_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.ImageSize_Col, relief="ridge")
        # self.Entry2_1_2.grid(column=col+1, row=3)
        # WH.UIConfiguration.set_text(self.Entry2_1_2, '1280')
        # self.CheckButton2_2 = tkinter.Checkbutton(self.InputinfoFrame, text="", variable=self.OffsetCalibration,
        #                                           command=lambda: WH.UIConfiguration.ButtonState([self.Button3], self.OffsetCalibration.get()))
        # self.CheckButton2_2.select()
        # self.CheckButton2_2.grid(column = col, row = 4, columnspan=Entry2Span)
        # self.FormatCBox = Combobox(self.InputinfoFrame, width = 4, textvariable = self.dFormat, state="readonly", values=[" raw", " tif", " bin"])
        # self.FormatCBox.set(" raw")
        # self.FormatCBox.grid(column = col, row = 5, columnspan=Entry2Span)
        # col = col + Entry2Span
        #
        # Entry3span = 1
        # self.Label3 = tkinter.Label(self.InputinfoFrame)
        # self.Label3.grid(column=col, row = 1, columnspan=10)
        # self.Button3 = tkinter.Button(self.InputinfoFrame, text='Dark File', command=self.Dark_Image)
        # self.Button3.grid(column=col, row=2, columnspan=Entry3span)
        # col = col + Entry3span
        #
        # Entry4Span = 2
        # self.Entry4_1 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.FOI_Start, relief="ridge")
        # self.Entry4_1.grid(column=col, row=3)
        # WH.UIConfiguration.set_text(self.Entry4_1, '0')
        # self.Entry4_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.FOI_End, relief="ridge")
        # self.Entry4_2.grid(column=col+1, row=3)
        # WH.UIConfiguration.set_text(self.Entry4_2, '0')
        # self.Button4 = tkinter.Button(self.InputinfoFrame, text='Frame')
        # self.Button4["state"] = 'disable'
        # self.Button4.grid(column=col, row=2, columnspan=Entry4Span)
        # col = col + Entry4Span
        #
        #
        # Entry5Span = 2
        # self.Entry5_1_1 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.ROI_Left, relief="ridge")
        # self.Entry5_1_1.grid(column=col, row=3)
        # WH.UIConfiguration.set_text(self.Entry5_1_1, '0')
        # self.Entry5_1_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.ROI_Right, relief="ridge")
        # self.Entry5_1_2.grid(column=col+1, row=3)
        # WH.UIConfiguration.set_text(self.Entry5_1_2, '0')
        # self.Entry5_2_1 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.ROI_Dn, relief="ridge")
        # self.Entry5_2_1.grid(column=col, row=4)
        # WH.UIConfiguration.set_text(self.Entry5_2_1, '0')
        # self.Entry5_2_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.ROI_Up, relief="ridge")
        # self.Entry5_2_2.grid(column=col+1, row=4)
        # WH.UIConfiguration.set_text(self.Entry5_2_2, '0')
        #
        # self.Button5 = tkinter.Button(self.InputinfoFrame, text='ROI (Left, Right \n Down, Up)')
        # self.Button5["state"] = "disable"
        # self.Button5.grid(column=col, row=2, columnspan=Entry5Span)
        # col = col + Entry5Span
        #
        # Entry6Span = 3
        # self.Button6 = tkinter.Button(self.InputinfoFrame, text='Show ROI', command=lambda: self.Show_ROI(self.InputData.copy()))
        # self.Button6.grid(column=col, row=2, columnspan=Entry6Span)
        # self.Label6_1_1 = tkinter.Label(self.InputinfoFrame, text='Image Size')
        # self.Label6_1_1.grid(column=col, row=3)
        # self.Label6_2_1 = tkinter.Label(self.InputinfoFrame, text='Frame')
        # self.Label6_2_1.grid(column=col, row=4)
        # self.Label6_3_1 = tkinter.Label(self.InputinfoFrame, text='ROI(Left, Right)')
        # self.Label6_3_1.grid(column=col, row=5)
        # self.Label6_4_1 = tkinter.Label(self.InputinfoFrame, text='ROI(Down, Up')
        # self.Label6_4_1.grid(column=col, row=6)
        # self.Label6_1_2 = tkinter.Label(self.InputinfoFrame, textvariable=self.ImageSize_Row)
        # self.Label6_1_2.grid(column=col+1, row=3)
        # self.Label6_2_2 = tkinter.Label(self.InputinfoFrame, textvariable=self.FOI_Start)
        # self.Label6_2_2.grid(column=col+1, row=4)
        # self.Label6_3_2 = tkinter.Label(self.InputinfoFrame, textvariable=self.ROI_Left)
        # self.Label6_3_2.grid(column=col+1, row=5)
        # self.Label6_4_2 = tkinter.Label(self.InputinfoFrame, textvariable=self.ROI_Dn)
        # self.Label6_4_2.grid(column=col+1, row=6)
        # self.Label6_1_3 = tkinter.Label(self.InputinfoFrame, textvariable=self.ImageSize_Col)
        # self.Label6_1_3.grid(column=col+2, row=3)
        # self.Label6_2_3 = tkinter.Label(self.InputinfoFrame, textvariable=self.FOI_End)
        # self.Label6_2_3.grid(column=col+2, row=4)
        # self.Label6_3_3 = tkinter.Label(self.InputinfoFrame, textvariable=self.ROI_Right)
        # self.Label6_3_3.grid(column=col+2, row=5)
        # self.Label6_4_3 = tkinter.Label(self.InputinfoFrame, textvariable=self.ROI_Up)
        # self.Label6_4_3.grid(column=col+2, row=6)
        # col = col + Entry6Span
        #
        # Entry7Span = 2
        # self.Label7_1_1 = tkinter.Label(self.InputinfoFrame, text='Column')
        # self.Label7_1_1.grid(column = col, row = 3)
        # self.Label7_2_1 = tkinter.Label(self.InputinfoFrame, text='Row')
        # self.Label7_2_1.grid(column = col, row = 4)
        #
        # self.Entry7_1_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.Division_Column, relief="ridge")
        # self.Entry7_1_2.grid(column=col + 1, row=3)
        # self.Entry7_2_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.Division_Row, relief="ridge")
        # self.Entry7_2_2.grid(column=col + 1, row=4)
        #
        # self.Button7 = tkinter.Button(self.InputinfoFrame, text='Division',
        #                               command=lambda: self.ShowBlock(self.ROIWidget, self.ROI_Data.copy(), int(self.Division_Row.get()), int(self.Division_Column.get())))
        # self.Button7.grid(column=col, row=2, columnspan=Entry7Span)
        # col = col + Entry7Span
        #
        # Entry8Span = 2
        # self.Button8 = tkinter.Button(self.InputinfoFrame, text='Calculate',
        #                               command=lambda: self.Calculate(self.ROIWidget, self.ROI_Data.copy(), int(self.Division_Row.get()), int(self.Division_Column.get())))
        # self.Button8.grid(column=col, row=2, columnspan=Entry8Span)
        #
        # self.Label8_1_1 = tkinter.Label(self.InputinfoFrame, text='Mean')
        # self.Label8_1_1.grid(column=col, row=3)
        # self.Label8_1_2 = tkinter.Label(self.InputinfoFrame, text='stddev')
        # self.Label8_1_2.grid(column=col, row=4)
        # self.Label8_2_1 = tkinter.Label(self.InputinfoFrame)
        # self.Label8_2_1.grid(column=col+1, row=3)
        # self.Label8_2_2 = tkinter.Label(self.InputinfoFrame)
        # self.Label8_2_2.grid(column=col+1, row=4)
        #
        # self.CheckButton8_3_1 = tkinter.Checkbutton(self.InputinfoFrame, text="", variable=self.PrevMask,
        #                                           command=lambda: [WH.UIConfiguration.ButtonState([self.Button8_3_2], self.PrevMask.get()),
        #                                             WH.UIConfiguration.ButtonState([self.Button9, self.Entry9_1_2, self.Entry9_2_2], not self.PrevMask.get())])
        # self.CheckButton8_3_1.grid(column = col, row = 5)
        # self.Button8_3_2 = tkinter.Button(self.InputinfoFrame, text='Use Previous', command=lambda: self.Apply_IQR(self.ROIWidget,
        #                                                                                                            self.ROI_Data.copy(),
        #                                                                                                            int(self.Division_Row.get()),
        #                                                                                                            int(self.Division_Column.get()),
        #                                                                                                            self.NIQR.get(),
        #                                                                                                            self.NIteration.get(),
        #                                                                                                            self.ExcludingZero.get(),
        #                                                                                                            self.PrevMask.get(),
        #                                                                                                            self.SpatialMask
        #                                                                                                            ))
        # self.Button8_3_2.grid(column=col+1, row=5)
        # self.Button8_3_2["state"] = 'disable'
        #
        # col = col + Entry8Span
        #
        # Entry9Span = 2
        # self.Button9 = tkinter.Button(self.InputinfoFrame, text='Spatial IQR',
        #                               command=lambda: self.Apply_IQR(self.ROIWidget,
        #                                                              self.ROI_Data.copy(),
        #                                                              int(self.Division_Row.get()),
        #                                                              int(self.Division_Column.get()),
        #                                                              self.NIQR.get(),
        #                                                              self.NIteration.get(),
        #                                                              self.ExcludingZero.get(),
        #                                                              self.PrevMask.get(),
        #                                                              self.SpatialMask
        #                                                              ))
        #
        # self.Button9.grid(column=col, row=2, columnspan=Entry9Span)
        # self.Label9_1_1 = tkinter.Label(self.InputinfoFrame, text='IQR')
        # self.Label9_1_1.grid(column=col, row=3)
        # self.Label9_2_1 = tkinter.Label(self.InputinfoFrame, text='Iterations')
        # self.Label9_2_1.grid(column=col, row=4)
        # self.Label9_3_1 = tkinter.Label(self.InputinfoFrame, text='Excluding 0')
        # self.Label9_3_1.grid(column=col, row=5)
        #
        # self.Entry9_1_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.NIQR, relief="ridge")
        # self.Entry9_1_2.grid(column=col + 1, row=3)
        # self.Entry9_2_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.NIteration, relief="ridge")
        # self.Entry9_2_2.grid(column=col + 1, row=4)
        # self.CheckButton9_3_2 = tkinter.Checkbutton(self.InputinfoFrame, text="", variable=self.ExcludingZero)
        # self.CheckButton9_3_2.grid(column = col + 1, row = 5)
        #
        # col = col + Entry9Span
        #
        # Entry10Span = 1
        # self.Button10 = tkinter.Button(self.InputinfoFrame, text='Save Image', command=lambda: self.SaveBTNEvent(self.Output))
        # self.Button10.grid(column=col, row=2, columnspan=Entry8Span)
        # self.Button10_2 = tkinter.Button(self.InputinfoFrame, text='Save Clipboard', command=lambda: self.SaveClipboardBTNEvent(self.Output))
        # self.Button10_2.grid(column=col, row=3)
        # col = col + Entry10Span


if __name__ == '__main__':
    window = tkinter.Tk()
    DarkCurrentAnalysis(window)
    window.mainloop()
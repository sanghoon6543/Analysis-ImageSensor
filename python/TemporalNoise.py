from tkinter.ttk import Combobox

import numpy as np
import os
import pandas as pd
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

class TemporalNoiseAnalysis:
    def __init__(self, window):
        self.window = window
        self.window.title("Temporal Noise Calculation")
        # self.window.config(background='#FFFFFF')
        self.window.geometry(f"{fw+450}x{int(2*fh/3)+100}")
        self.window.resizable(True, True)

        self.filepath = ""
        self.OffsetCalibration = BooleanVar()
        self.dFormat = StringVar()
        self.ImageSize_Row = IntVar()
        self.ImageSize_Col = IntVar()

        self.FOI_Start, self.FOI_End, self.ROI_Left, self.ROI_Right, self.ROI_Up, self.ROI_Dn =\
            IntVar(), IntVar(), IntVar(), IntVar(), IntVar(), IntVar()

        self.read_data = np.array([], dtype=np.float64)
        self.frame_average = np.array([], dtype=np.float64)
        self.dark_data = np.array([], dtype=np.float64)

        self.SystemGain, self.Differential, self.ExcludingZero, self.HPF =\
            DoubleVar(), BooleanVar(), BooleanVar(), BooleanVar()

        self.Division_Column, self.Division_Row = IntVar(), IntVar()
        self.NIQR, self.NIteration = DoubleVar(), IntVar()
        self.NIQR_S, self.NIteration_S = DoubleVar(), IntVar()

        self.SpatialMask = FALSE
        self.OutputFrame = FALSE
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
        WH.UIConfiguration.set_text(self.Entry4_1_2, '1')
        WH.UIConfiguration.set_text(self.Entry4_1_3, f"{int(len(self.InputData))}")
        WH.UIConfiguration.set_text(self.Entry4_2_2, '0')
        WH.UIConfiguration.set_text(self.Entry4_2_3, f"{int(self.InputData.shape[2]) - 1}")
        WH.UIConfiguration.set_text(self.Entry4_3_2, '0')
        WH.UIConfiguration.set_text(self.Entry4_3_3, f'{int(self.InputData.shape[1]) - 1}')


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

        Frame = WH.ButtonClickedEvent.Set_ROI(Frame, ROI1, ROI2)
        Frame = WH.ButtonClickedEvent.Set_FOI(Frame, FOI)

        self.ROI_Data = Frame

        if not hasattr(self, 'ROIWidget'):
            self.ROIWidget = WH.Plotting.MakeFigureWidget(self.ROIPlotFrame, fs)

        WH.Plotting.ShowImage(HF.DataProcessing.TemporalAverage(self.ROI_Data), self.ImageWidget)
        # WH.Plotting.ShowImage(self.ROI_Data, self.ROIWidget)

    def ShowBlock(self, ax, Frame, row, col):

        WH.Plotting.DrawDivision(ax, Frame, row, col)

    def Configurations(self, Frame, Differential):

        if Differential == False:
            self.Label6_3_2.configure(text=f"{int(self.FOI_End.get() - self.FOI_Start.get() + 1)}")
        else:
            self.Label6_3_2.configure(text=f"{int(self.FOI_End.get() - self.FOI_Start.get())}")

    def Calculate(self, ax1, ax2, Frame, row, col, Differential):

        self.Noise = WH.ButtonClickedEvent.Calculate_TemporalNoise(imageinfo=Frame, Differential = Differential)

        self.Label8_1_2.configure(text=f'{int(np.round(self.Noise["TotalNoise"] / self.SystemGain.get(), 0))}')
        self.Label8_2_2.configure(text=f'{int(np.round(self.Noise["FrameNoise"] / self.SystemGain.get(), 0))}')
        self.Label8_3_2.configure(text=f'{int(np.round(self.Noise["RowLineNoise"] / self.SystemGain.get(), 0))}')
        self.Label8_4_2.configure(text=f'{int(np.round(self.Noise["ColLineNoise"] / self.SystemGain.get(), 0))}')

        WH.Plotting.ShowImage(HF.DataProcessing.TemporalAverage(self.Noise["ImageInfo"]), ax2)
        WH.UIConfiguration.Save2Clipboard(HF.DataProcessing.Data2Histogram(self.Noise['ImageInfo']))

    def Apply_IQR(self, Frame, NIQR, NIteration, Differential, ExcZero, HPF, Widget):
        self.MaskedNoise = WH.ButtonClickedEvent.Apply_IQR_TemporalNoise(Frame, NIQR, NIteration, Differential, ExcZero, HPF)

        self.Label10_1_2.configure(text=f'{int(np.round(self.MaskedNoise["TotalNoise"]/ self.SystemGain.get(), 0))}')
        self.Label10_2_2.configure(text=f'{int(np.round(self.MaskedNoise["FrameNoise"] / self.SystemGain.get(), 0))}')
        self.Label10_3_2.configure(text=f'{int(np.round(self.MaskedNoise["RowLineNoise"] / self.SystemGain.get(), 0))}')
        self.Label10_4_2.configure(text=f'{int(np.round(self.MaskedNoise["ColLineNoise"] / self.SystemGain.get(), 0))}')

        WH.Plotting.ShowImage(HF.DataProcessing.TemporalAverage(self.MaskedNoise["Mask"]), Widget)
        WH.UIConfiguration.Save2Clipboard(HF.DataProcessing.Data2Histogram(self.MaskedNoise['ImageInfo'], self.MaskedNoise['Mask']))

    def SaveBTNEvent(self, fp, dtype, data):

        WH.ButtonClickedEvent.Save_Files(fp, dtype, data)

    def SaveClipboardBTNEvent(self, data):

        if data.shape[1] == 1:
            df = pd.DataFrame(data, columns=['Raw'])
        elif data.shape[1] == 2:
            df = pd.DataFrame(data, columns=['Raw', 'IQR'])
        elif data.shape[1] == 3:
            df = pd.DataFrame(data, columns=['Raw', 'IQR', 'Cal'])
        else:
            df = pd.DataFrame(data)

        WH.ButtonClickedEvent.SaveClipboard(df)

    def _build_ui(self):
        """
        Build Tkinter GUI widgets.
        This GUI was originally developed as a practical engineering tool.
        UI widgets are generated from configuration dictionaries through UI_Builder.UIBuilder.
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

        FrameInfos = [
            {"name": "ReadFrame", "row": 0, "col": 0, "top_minsize": 20},
            {"name": "DarkFileFrame", "row": 0, "col": 1, "top_minsize": 20},
            {"name": "ROISettingFrame", "row": 0, "col": 2, "top_minsize": 20},
            {"name": "ROISummaryFrame", "row": 0, "col": 3, "top_minsize": 20},
            {"name": "ConfigurationFrame", "row": 0, "col": 4, "top_minsize": 20},
            {"name": "DivisionFrame", "row": 0, "col": 5, "top_minsize": 20},
            {"name": "CalculateFrame", "row": 0, "col": 6, "top_minsize": 20},
            {"name": "IQRFrame", "row": 0, "col": 7, "top_minsize": 20},
            {"name": "SaveFrame", "row": 0, "col": 8, "top_minsize": 20},
        ]

        for frame_info in FrameInfos:
            UI.UIBuilder.make_control_frame(self, self.InputinfoFrame, frame_info)

        LabelInfos = [
            # ReadFrame
            {"parent": self.ReadFrame, "name": "label1", "text": "", "row": 0, "col": 0, "columnspan": 4},
            {"parent": self.ReadFrame, "name": "Label1_1", "text": "Image Size(Row, Col)", "row": 2, "col": 0, "columnspan": 2},
            {"parent": self.ReadFrame, "name": "Label1_2", "text": "Offset Calibration", "row": 3, "col": 0, "columnspan": 2},
            {"parent": self.ReadFrame, "name": "Label1_3", "text": "Format", "row": 4, "col": 0, "columnspan": 2},

            # DarkFileFrame
            {"parent": self.DarkFileFrame, "name": "Label3", "text": "", "row": 0, "col": 0, "columnspan": 2},

            # ROISettingFrame
            {"parent": self.ROISettingFrame, "name": "Label4_1_1", "text": "Frame", "row": 2, "col": 0},
            {"parent": self.ROISettingFrame, "name": "Label4_2_1", "text": "ROI(H)", "row": 3, "col": 0},
            {"parent": self.ROISettingFrame, "name": "Label4_3_1", "text": "ROI(V)", "row": 4, "col": 0},

            # ROISummaryFrame
            {"parent": self.ROISummaryFrame, "name": "Label5_1_1", "text": "Frame", "row": 2, "col": 0},
            {"parent": self.ROISummaryFrame, "name": "Label5_2_1", "text": "ROI(H)", "row": 3, "col": 0},
            {"parent": self.ROISummaryFrame, "name": "Label5_3_1", "text": "ROI(V)", "row": 4, "col": 0},
            {"parent": self.ROISummaryFrame, "name": "Label5_4_1", "text": "Image Size", "row": 5, "col": 0},

            {"parent": self.ROISummaryFrame, "name": "Label5_1_2", "textvariable": self.FOI_Start, "row": 2, "col": 1},
            {"parent": self.ROISummaryFrame, "name": "Label5_1_3", "textvariable": self.FOI_End, "row": 2, "col": 2},
            {"parent": self.ROISummaryFrame, "name": "Label5_2_2", "textvariable": self.ROI_Left, "row": 3, "col": 1},
            {"parent": self.ROISummaryFrame, "name": "Label5_2_3", "textvariable": self.ROI_Right, "row": 3, "col": 2},
            {"parent": self.ROISummaryFrame, "name": "Label5_3_2", "textvariable": self.ROI_Dn, "row": 4, "col": 1},
            {"parent": self.ROISummaryFrame, "name": "Label5_3_3", "textvariable": self.ROI_Up, "row": 4, "col": 2},
            {"parent": self.ROISummaryFrame, "name": "Label5_4_2", "textvariable": self.ImageSize_Row, "row": 5, "col": 1},
            {"parent": self.ROISummaryFrame, "name": "Label5_4_3", "textvariable": self.ImageSize_Col, "row": 5, "col": 2},

            # ConfigurationFrame
            {"parent": self.ConfigurationFrame, "name": "Label6_1_1", "text": "System Gain", "row": 2, "col": 0},
            {"parent": self.ConfigurationFrame, "name": "Label6_2_1", "text": "Differential", "row": 3, "col": 0},
            {"parent": self.ConfigurationFrame, "name": "Label6_3_1", "text": "Frames", "row": 4, "col": 0},
            {"parent": self.ConfigurationFrame, "name": "Label6_3_2", "text": "", "row": 4, "col": 1},

            # DivisionFrame
            {"parent": self.DivisionFrame, "name": "Label7_1_1", "text": "Column", "row": 2, "col": 0},
            {"parent": self.DivisionFrame, "name": "Label7_2_1", "text": "Row", "row": 3, "col": 0},

            # CalculateFrame
            {"parent": self.CalculateFrame, "name": "Label8_1_1", "text": "Pixel Noise", "row": 2, "col": 0},
            {"parent": self.CalculateFrame, "name": "Label8_2_1", "text": "Frame Noise", "row": 3, "col": 0},
            {"parent": self.CalculateFrame, "name": "Label8_3_1", "text": "Line Noise(R)", "row": 4, "col": 0},
            {"parent": self.CalculateFrame, "name": "Label8_4_1", "text": "Line Noise(C)", "row": 5, "col": 0},
            {"parent": self.CalculateFrame, "name": "Label8_1_2", "text": "", "row": 2, "col": 1},
            {"parent": self.CalculateFrame, "name": "Label8_2_2", "text": "", "row": 3, "col": 1},
            {"parent": self.CalculateFrame, "name": "Label8_3_2", "text": "", "row": 4, "col": 1},
            {"parent": self.CalculateFrame, "name": "Label8_4_2", "text": "", "row": 5, "col": 1},

            # IQRFrame
            {"parent": self.IQRFrame, "name": "Label9_1_1", "text": "IQR", "row": 2, "col": 0},
            {"parent": self.IQRFrame, "name": "Label9_2_1", "text": "Iterations", "row": 3, "col": 0},
            {"parent": self.IQRFrame, "name": "Label9_3_1", "text": "Excluding 0", "row": 4, "col": 0},
            {"parent": self.IQRFrame, "name": "Label9_4_1", "text": "HighPass Filter", "row": 5, "col": 0},

            # SaveFrame / IQR result
            {"parent": self.SaveFrame, "name": "Label10_1_1", "text": "Pixel Noise", "row": 2, "col": 0},
            {"parent": self.SaveFrame, "name": "Label10_2_1", "text": "Frame Noise", "row": 3, "col": 0},
            {"parent": self.SaveFrame, "name": "Label10_3_1", "text": "Line Noise(R)", "row": 4, "col": 0},
            {"parent": self.SaveFrame, "name": "Label10_4_1", "text": "Line Noise(C)", "row": 5, "col": 0},
            {"parent": self.SaveFrame, "name": "Label10_1_2", "text": "", "row": 2, "col": 1},
            {"parent": self.SaveFrame, "name": "Label10_2_2", "text": "", "row": 3, "col": 1},
            {"parent": self.SaveFrame, "name": "Label10_3_2", "text": "", "row": 4, "col": 1},
            {"parent": self.SaveFrame, "name": "Label10_4_2", "text": "", "row": 5, "col": 1},
        ]

        for label_info in LabelInfos:
            UI.UIBuilder.make_label(self, label_info)

        EntryInfos = [
            # ReadFrame
            {"parent": self.ReadFrame, "name": "Entry2_1_1", "textvariable": self.ImageSize_Row, "default": 1280, "row": 2, "col": 2, "width": 4},
            {"parent": self.ReadFrame, "name": "Entry2_1_2", "textvariable": self.ImageSize_Col, "default": 1280, "row": 2, "col": 3, "width": 4},

            # ROISettingFrame
            {"parent": self.ROISettingFrame, "name": "Entry4_1_2", "textvariable": self.FOI_Start, "default": 0, "row": 2, "col": 1, "width": 4},
            {"parent": self.ROISettingFrame, "name": "Entry4_1_3", "textvariable": self.FOI_End, "default": 0, "row": 2, "col": 2, "width": 4},
            {"parent": self.ROISettingFrame, "name": "Entry4_2_2", "textvariable": self.ROI_Left, "default": 0, "row": 3, "col": 1, "width": 4},
            {"parent": self.ROISettingFrame, "name": "Entry4_2_3", "textvariable": self.ROI_Right, "default": 0, "row": 3, "col": 2, "width": 4},
            {"parent": self.ROISettingFrame, "name": "Entry4_3_2", "textvariable": self.ROI_Dn, "default": 0, "row": 4, "col": 1, "width": 4},
            {"parent": self.ROISettingFrame, "name": "Entry4_3_3", "textvariable": self.ROI_Up, "default": 0, "row": 4, "col": 2, "width": 4},

            # ConfigurationFrame
            {"parent": self.ConfigurationFrame, "name": "Entry6_1_1", "textvariable": self.SystemGain, "default": 1, "row": 2, "col": 1, "width": 4},

            # DivisionFrame
            {"parent": self.DivisionFrame, "name": "Entry7_1_2", "textvariable": self.Division_Column, "default": 1, "row": 2, "col": 1, "width": 4},
            {"parent": self.DivisionFrame, "name": "Entry7_2_2", "textvariable": self.Division_Row, "default": 1, "row": 3, "col": 1, "width": 4},

            # IQRFrame
            {"parent": self.IQRFrame, "name": "Entry9_1_2", "textvariable": self.NIQR, "row": 2, "col": 1, "width": 4},
            {"parent": self.IQRFrame, "name": "Entry9_2_2", "textvariable": self.NIteration, "row": 3, "col": 1, "width": 4},
        ]

        for entry_info in EntryInfos:
            UI.UIBuilder.make_entry(self, entry_info)

        ComboBoxInfos = [
            {"parent": self.ReadFrame, "name": "FormatCBox", "textvariable": self.dFormat, "values": [" raw", " tif", " bin"], "default": " raw", "row": 4, "col": 2, "columnspan": 2, "width": 4, "state": "readonly"},
        ]

        for combo_info in ComboBoxInfos:
            UI.UIBuilder.make_combobox(self, combo_info)

        ButtonInfos = [
            {"parent": self.ReadFrame, "name": "Button1", "text": "Open File", "command": self.Open_Path, "row": 1, "col": 0},
            {"parent": self.ReadFrame, "name": "Button2", "text": "Read File", "command": self.Read_Image, "row": 1, "col": 1, "columnspan": 3},

            {"parent": self.DarkFileFrame, "name": "Button3", "text": "Dark File", "command": self.Dark_Image, "row": 1, "col": 0, "columnspan": 2},

            {"parent": self.ROISettingFrame, "name": "Button4", "text": "ROI Setting", "row": 1, "col": 0, "columnspan": 3, "state": "disabled"},

            {"parent": self.ROISummaryFrame, "name": "Button5", "text": "Show ROI", "command": lambda: self.Show_ROI(self.InputData.copy()), "row": 1, "col": 0, "columnspan": 3},

            {"parent": self.ConfigurationFrame, "name": "Button6", "text": "Configuration", "command": lambda: self.Configurations(self.ROI_Data.copy(), self.Differential.get()), "row": 1, "col": 0, "columnspan": 2},

            {"parent": self.DivisionFrame, "name": "Button7", "text": "Division", "command": lambda: self.ShowBlock(self.ImageWidget, self.ROI_Data.copy(), int(self.Division_Row.get()), int(self.Division_Column.get())), "row": 1, "col": 0, "columnspan": 2},

            {"parent": self.CalculateFrame, "name": "Button8", "text": "Calculate", "command": lambda: self.Calculate(self.ImageWidget, self.ROIWidget, self.ROI_Data.copy(), int(self.Division_Row.get()), int(self.Division_Column.get()), self.Differential.get()), "row": 1, "col": 0, "columnspan": 2},

            {"parent": self.IQRFrame, "name": "Button9", "text": "Spatial IQR", "command": lambda: self.Apply_IQR(self.ROI_Data.copy(), self.NIQR.get(), self.NIteration.get(), self.Differential.get(), self.ExcludingZero.get(), self.HPF.get(), self.ROIWidget), "row": 1, "col": 0, "columnspan": 2},

            {"parent": self.SaveFrame, "name": "Button10", "text": "Save Clipboard", "command": lambda: self.SaveClipboardBTNEvent(self.Output), "row": 1, "col": 0, "columnspan": 2},
        ]

        for button_info in ButtonInfos:
            UI.UIBuilder.make_button(self, button_info)

        CheckButtonInfos = [
            {"parent": self.ReadFrame, "name": "CheckButton2_2", "text": "", "variable": self.OffsetCalibration, "command": lambda: WH.UIConfiguration.ButtonState([self.Button3], self.OffsetCalibration.get()), "row": 3, "col": 2, "columnspan": 2},

            {"parent": self.ConfigurationFrame, "name": "CheckButton6_2_2", "text": "", "variable": self.Differential, "row": 3, "col": 1},

            {"parent": self.IQRFrame, "name": "CheckButton9_3_2", "text": "", "variable": self.ExcludingZero, "row": 4, "col": 1},
            {"parent": self.IQRFrame, "name": "CheckButton9_4_2", "text": "", "variable": self.HPF, "row": 5, "col": 1},
        ]

        for checkbutton_info in CheckButtonInfos:
            UI.UIBuilder.make_checkbutton(self, checkbutton_info)

        # ------------------------------------------------------------
        # Initial states
        # ------------------------------------------------------------
        self.CheckButton2_2.select()
        self.CheckButton6_2_2.select()
        self.CheckButton9_4_2.select()

        WH.UIConfiguration.ButtonState([self.Button7], False)
        WH.UIConfiguration.set_text(self.Entry7_1_2, "1")
        WH.UIConfiguration.set_text(self.Entry7_2_2, "1")
        self.Entry7_1_2.configure(state="readonly")
        self.Entry7_2_2.configure(state="readonly")


        # col = 0
        #
        # # UI for Opening File
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
        #
        # col = col + Entry1Span
        #
        # # UI for Reading File
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
        # self.FormatCBox = Combobox(self.InputinfoFrame, width = 4, textvariable = self.dFormat, state="readonly", values=[" raw", " tif"])
        # self.FormatCBox.set(" raw")
        # self.FormatCBox.grid(column = col, row = 5, columnspan=Entry2Span)
        # col = col + Entry2Span
        #
        # # UI for Selecting and Reading Darkfile
        # Entry3span = 1
        # self.Label3 = tkinter.Label(self.InputinfoFrame)
        # self.Label3.grid(column=col, row = 1, columnspan=10)
        # self.Button3 = tkinter.Button(self.InputinfoFrame, text='Dark File', command=self.Dark_Image)
        # self.Button3.grid(column=col, row=2, columnspan=Entry3span)
        # col = col + Entry3span
        #
        #
        # # UI for Setting ROI
        # Entry4Span = 3
        # self.Label4_1_1 = tkinter.Label(self.InputinfoFrame, text='Frame')
        # self.Label4_1_1.grid(column=col, row=3)
        # self.Entry4_1_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.FOI_Start, relief="ridge")
        # self.Entry4_1_2.grid(column=col+1, row=3)
        # WH.UIConfiguration.set_text(self.Entry4_1_2, '0')
        # self.Entry4_1_3 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.FOI_End, relief="ridge")
        # self.Entry4_1_3.grid(column=col+2, row=3)
        # WH.UIConfiguration.set_text(self.Entry4_1_3, '0')
        #
        # self.Label4_2_1 = tkinter.Label(self.InputinfoFrame, text='ROI(H)')
        # self.Label4_2_1.grid(column=col, row=4)
        # self.Entry4_2_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.ROI_Left, relief="ridge")
        # self.Entry4_2_2.grid(column=col+1, row=4)
        # WH.UIConfiguration.set_text(self.Entry4_2_2, '0')
        # self.Entry4_2_3 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.ROI_Right, relief="ridge")
        # self.Entry4_2_3.grid(column=col+2, row=4)
        # WH.UIConfiguration.set_text(self.Entry4_2_3, '0')
        #
        # self.Label4_3_1 = tkinter.Label(self.InputinfoFrame, text='ROI(V)')
        # self.Label4_3_1.grid(column=col, row=5)
        # self.Entry4_3_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.ROI_Dn, relief="ridge")
        # self.Entry4_3_2.grid(column=col+1, row=5)
        # WH.UIConfiguration.set_text(self.Entry4_3_2, '0')
        # self.Entry4_3_3 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.ROI_Up, relief="ridge")
        # self.Entry4_3_3.grid(column=col+2, row=5)
        # WH.UIConfiguration.set_text(self.Entry4_3_3, '0')
        #
        # self.Button4 = tkinter.Button(self.InputinfoFrame, text='ROI Setting')
        # self.Button4["state"] = 'disable'
        # self.Button4.grid(column=col, row=2, columnspan=Entry4Span)
        # col = col + Entry4Span
        #
        # Entry5Span = 3
        # self.Button5 = tkinter.Button(self.InputinfoFrame, text='Show ROI', command=lambda: self.Show_ROI(self.InputData.copy()))
        # self.Button5.grid(column=col, row=2, columnspan=Entry5Span)
        # self.Label5_1_1 = tkinter.Label(self.InputinfoFrame, text='Frame')
        # self.Label5_1_1.grid(column=col, row=3)
        # self.Label5_2_1 = tkinter.Label(self.InputinfoFrame, text='ROI(H)')
        # self.Label5_2_1.grid(column=col, row=4)
        # self.Label5_3_1 = tkinter.Label(self.InputinfoFrame, text='ROI(V)')
        # self.Label5_3_1.grid(column=col, row=5)
        # self.Label5_4_1 = tkinter.Label(self.InputinfoFrame, text='Image Size')
        # self.Label5_4_1.grid(column=col, row=6)
        # self.Label5_1_2 = tkinter.Label(self.InputinfoFrame, textvariable=self.FOI_Start)
        # self.Label5_1_2.grid(column=col+1, row=3)
        # self.Label5_2_2 = tkinter.Label(self.InputinfoFrame, textvariable=self.ROI_Left)
        # self.Label5_2_2.grid(column=col+1, row=4)
        # self.Label5_3_2 = tkinter.Label(self.InputinfoFrame, textvariable=self.ROI_Dn)
        # self.Label5_3_2.grid(column=col+1, row=5)
        # self.Label5_4_2 = tkinter.Label(self.InputinfoFrame, textvariable=self.ImageSize_Row)
        # self.Label5_4_2.grid(column=col+1, row=6)
        # self.Label5_1_3 = tkinter.Label(self.InputinfoFrame, textvariable=self.FOI_End)
        # self.Label5_1_3.grid(column=col+2, row=3)
        # self.Label5_2_3 = tkinter.Label(self.InputinfoFrame, textvariable=self.ROI_Right)
        # self.Label5_2_3.grid(column=col+2, row=4)
        # self.Label5_3_3 = tkinter.Label(self.InputinfoFrame, textvariable=self.ROI_Up)
        # self.Label5_3_3.grid(column=col+2, row=5)
        # self.Label5_4_3 = tkinter.Label(self.InputinfoFrame, textvariable=self.ImageSize_Col)
        # self.Label5_4_3.grid(column=col+2, row=6)
        # col = col + Entry5Span
        #
        # Entry6Span = 2
        # self.Label6_1_1 = tkinter.Label(self.InputinfoFrame, text='System Gain')
        # self.Label6_1_1.grid(column = col, row = 3)
        # self.Label6_2_1 = tkinter.Label(self.InputinfoFrame, text='Differential')
        # self.Label6_2_1.grid(column = col, row = 4)
        # self.Label6_3_1 = tkinter.Label(self.InputinfoFrame, text='Frames')
        # self.Label6_3_1.grid(column = col, row = 5)
        #
        # self.Entry6_1_1 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.SystemGain, relief="ridge")
        # self.Entry6_1_1.grid(column=col + 1, row=3)
        #
        # self.CheckButton6_2_2 = tkinter.Checkbutton(self.InputinfoFrame, text="", variable=self.Differential)
        # self.CheckButton6_2_2.select()
        # self.CheckButton6_2_2.grid(column = col + 1, row = 4)
        # self.Label6_3_2 = tkinter.Label(self.InputinfoFrame, text='')
        # self.Label6_3_2.grid(column=col + 1, row=5)
        #
        # self.Button6 = tkinter.Button(self.InputinfoFrame, text='Configuration', command=lambda: self.Configurations(self.ROI_Data.copy(), self.Differential.get()))
        # self.Button6.grid(column=col, row=2, columnspan=Entry6Span)
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
        #                               command=lambda: self.ShowBlock(self.ImageWidget, self.ROI_Data.copy(), int(self.Division_Row.get()), int(self.Division_Column.get())))
        # self.Button7.grid(column=col, row=2, columnspan=Entry7Span)
        # WH.UIConfiguration.ButtonState([self.Button7], False)
        # WH.UIConfiguration.set_text(self.Entry7_1_2, '1')
        # WH.UIConfiguration.set_text(self.Entry7_2_2, '1')
        # self.Entry7_1_2.configure(state='readonly')
        # self.Entry7_2_2.configure(state='readonly')
        #
        # col = col + Entry7Span
        #
        # Entry8Span = 2
        # self.Button8 = tkinter.Button(self.InputinfoFrame, text='Calculate',
        #                               command=lambda: self.Calculate(self.ImageWidget,
        #                                                              self.ROIWidget,
        #                                                              self.ROI_Data.copy(),
        #                                                              int(self.Division_Row.get()),
        #                                                              int(self.Division_Column.get()),
        #                                                              self.Differential.get()))
        # self.Button8.grid(column=col, row=2, columnspan=Entry8Span)
        #
        # self.Label8_1_1 = tkinter.Label(self.InputinfoFrame, text='Pixel Noise')
        # self.Label8_1_1.grid(column=col, row=3)
        # self.Label8_2_1 = tkinter.Label(self.InputinfoFrame, text='Frame Noise')
        # self.Label8_2_1.grid(column=col, row=4)
        # self.Label8_3_1 = tkinter.Label(self.InputinfoFrame, text='Line Noise(R)')
        # self.Label8_3_1.grid(column=col, row=5)
        # self.Label8_4_1 = tkinter.Label(self.InputinfoFrame, text='Line Noise(C)')
        # self.Label8_4_1.grid(column=col, row=6)
        #
        # self.Label8_1_2 = tkinter.Label(self.InputinfoFrame)
        # self.Label8_1_2.grid(column=col+1, row=3)
        # self.Label8_2_2 = tkinter.Label(self.InputinfoFrame)
        # self.Label8_2_2.grid(column=col+1, row=4)
        # self.Label8_3_2 = tkinter.Label(self.InputinfoFrame)
        # self.Label8_3_2.grid(column=col+1, row=5)
        # self.Label8_4_2 = tkinter.Label(self.InputinfoFrame)
        # self.Label8_4_2.grid(column=col+1, row=6)
        # col = col + Entry8Span
        #
        # Entry9Span = 2
        # self.Button9 = tkinter.Button(self.InputinfoFrame, text='Spatial IQR', command=lambda: self.Apply_IQR(self.ROI_Data.copy(),
        #                                                                                                     self.NIQR.get(),
        #                                                                                                     self.NIteration.get(),
        #                                                                                                     self.Differential.get(),
        #                                                                                                     self.ExcludingZero.get(),
        #                                                                                                     self.HPF.get(),
        #                                                                                                     self.ROIWidget))
        #
        # self.Button9.grid(column=col, row=2, columnspan=Entry9Span)
        # self.Label9_1_1 = tkinter.Label(self.InputinfoFrame, text='IQR')
        # self.Label9_1_1.grid(column=col, row=3)
        # self.Label9_2_1 = tkinter.Label(self.InputinfoFrame, text='Iterations')
        # self.Label9_2_1.grid(column=col, row=4)
        # self.Label9_3_1 = tkinter.Label(self.InputinfoFrame, text='Excluding 0')
        # self.Label9_3_1.grid(column=col, row=5)
        # self.Label9_4_1 = tkinter.Label(self.InputinfoFrame, text='HighPass Filter')
        # self.Label9_4_1.grid(column=col, row=6)
        #
        # self.Entry9_1_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.NIQR, relief="ridge")
        # self.Entry9_1_2.grid(column=col + 1, row=3)
        # self.Entry9_2_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.NIteration, relief="ridge")
        # self.Entry9_2_2.grid(column=col + 1, row=4)
        # self.CheckButton9_3_2 = tkinter.Checkbutton(self.InputinfoFrame, text="", variable=self.ExcludingZero)
        # self.CheckButton9_3_2.grid(column = col + 1, row = 5)
        # self.CheckButton9_4_2 = tkinter.Checkbutton(self.InputinfoFrame, text="", variable=self.HPF)
        # self.CheckButton9_4_2.grid(column=col + 1, row=6)
        # self.CheckButton9_4_2.select()
        # col = col + Entry9Span
        #
        # Entry10Span = 2
        # self.Button10 = tkinter.Button(self.InputinfoFrame, text='Save Clipboard',
        #                                 command=lambda: self.SaveClipboardBTNEvent(self.Output))
        # self.Button10.grid(column=col, row=2, columnspan=Entry10Span)
        # self.Label10_1_1 = tkinter.Label(self.InputinfoFrame, text='Pixel Noise')
        # self.Label10_1_1.grid(column=col, row=3)
        # self.Label10_2_1 = tkinter.Label(self.InputinfoFrame, text='Frame Noise')
        # self.Label10_2_1.grid(column=col, row=4)
        # self.Label10_3_1 = tkinter.Label(self.InputinfoFrame, text='Line Noise(R)')
        # self.Label10_3_1.grid(column=col, row=5)
        # self.Label10_4_1 = tkinter.Label(self.InputinfoFrame, text='Line Noise(C)')
        # self.Label10_4_1.grid(column=col, row=6)
        #
        # self.Label10_1_2 = tkinter.Label(self.InputinfoFrame)
        # self.Label10_1_2.grid(column=col+1, row=3)
        # self.Label10_2_2 = tkinter.Label(self.InputinfoFrame)
        # self.Label10_2_2.grid(column=col+1, row=4)
        # self.Label10_3_2 = tkinter.Label(self.InputinfoFrame)
        # self.Label10_3_2.grid(column=col+1, row=5)
        # self.Label10_4_2 = tkinter.Label(self.InputinfoFrame)
        # self.Label10_4_2.grid(column=col+1, row=6)
        # col = col + Entry10Span
        #
        # Entry11Span = 1
        # # self.Button11 = tkinter.Button(self.InputinfoFrame, text='Save Image',
        # #                                 command=lambda: self.SaveBTNEvent(self.filepath, np.uint16, self.OutputFrame))
        # # self.Button11.grid(column=col, row=3, columnspan=Entry11Span)
        #
        # col = col + Entry11Span


if __name__ == '__main__':
    window = tkinter.Tk()
    TemporalNoiseAnalysis(window)
    window.mainloop()
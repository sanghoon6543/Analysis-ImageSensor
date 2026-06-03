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

class PixelMathAnalysis:
    def __init__(self, window):
        self.window = window
        self.window.title("Pixel Math")
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
        self.dark_data = np.array([], dtype=np.float64)
        self.frame_average = np.array([], dtype=np.float64)

        self.Division_Column, self.Division_Row = IntVar(), IntVar()
        self.Criterion, self.MaxValue, self.AddValue = IntVar(), IntVar(), IntVar()

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

        if not hasattr(self, 'ROIWidget'):
            self.ROIWidget = WH.Plotting.MakeFigureWidget(self.ROIPlotFrame, fs)

        self.InputData = self.read_data.copy()
        self.frame_average = HF.DataProcessing.TemporalAverage(self.InputData)

        WH.Plotting.ShowImage(self.frame_average, self.ImageWidget)
        WH.UIConfiguration.set_text(self.Entry4_1_1, '1')
        WH.UIConfiguration.set_text(self.Entry4_1_2, f"{int(len(self.InputData))}")
        self.Label4_2_1.configure(text = f"1 ~ {int(len(self.InputData))}")
        WH.UIConfiguration.set_text(self.Entry5_1_1, '0')
        WH.UIConfiguration.set_text(self.Entry5_1_2, f"{int(self.InputData.shape[2]) - 1}")
        WH.UIConfiguration.set_text(self.Entry5_2_1, '0')
        WH.UIConfiguration.set_text(self.Entry5_2_2, f'{int(self.InputData.shape[1]) - 1}')


    def Dark_Image(self):

        Image_Size = [int(self.ImageSize_Row.get()), int(self.ImageSize_Col.get())]

        fpath = WH.ButtonClickedEvent.Open_File(self.filepath)
        self.Label3.configure(text=f"{fpath[-40:]}")

        self.dark_data = WH.ButtonClickedEvent.Read_File(fpath, self.dFormat.get()[1:], np.uint16, Image_Size)
        self.InputData = self.InputData - self.dark_data
        self.frame_average = HF.DataProcessing.TemporalAverage(self.InputData)
        WH.Plotting.ShowImage(self.frame_average, self.ImageWidget)

    def Show_ROI(self, ax, Frame):

        FOI = np.array([int(self.FOI_Start.get()), int(self.FOI_End.get())])
        ROI1 = np.array([int(self.ROI_Left.get()), int(self.ROI_Dn.get())])
        ROI2 = np.array([int(self.ROI_Right.get()), int(self.ROI_Up.get())])

        Frame = WH.ButtonClickedEvent.Set_ROI(Frame, ROI1, ROI2)
        Frame = WH.ButtonClickedEvent.Set_FOI(Frame, FOI)

        self.ROI_Data = Frame

        WH.Plotting.ShowImage(HF.DataProcessing.TemporalAverage(self.ROI_Data), ax)
        # WH.Plotting.ShowImage(self.ROI_Data, self.ROIWidget)

    def ShowBlock(self, ax, Frame, row, col):

        WH.Plotting.DrawDivision(ax, Frame, row, col)

    def Calculate(self, ax1, ax2, Frame, row, col, criteron, maxV, addV):

        Frame[Frame>=criteron] -= maxV
        Frame += addV
        self.Show_ROI(ax2, Frame.copy())

        # Frame = HF.DataProcessing.Array2Maskedarray(Frame)
        Average = HF.DataProcessing.SpatialAverage(Frame)

        self.Output = Average[:, np.newaxis].copy()
        self.OutputFrame = Frame.copy()

    def SaveBTNEvent(self, fp, dtype, dformat, data):
        # data = np.swapaxes(data, 1, 2)
        WH.ButtonClickedEvent.Save_Files(fp, dtype, dformat, data)

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

        self.InputFrame = tkinter.Frame(self.window, width=fw, height=fh + 100)
        self.InputFrame.grid(column=0, row=0)

        self.ImagePlotFrame = tkinter.Frame(self.InputFrame, bg="white", width=fw / 2, height=fh / 2)
        self.ImagePlotFrame.grid(column=0, row=0)

        self.ROIPlotFrame = tkinter.Frame(self.InputFrame, bg="white", width=fw / 2, height=fh / 2)
        self.ROIPlotFrame.grid(column=1, row=0)

        self.InputinfoFrame = tkinter.Frame(self.InputFrame, width=fw, height=100)
        self.InputinfoFrame.grid(column=0, row=1, columnspan=2)

        self.FrameAddress = {}
        self.ButtonAddress = {}
        self.LabelAddress = {}
        self.EntryAddress = {}
        self.ComboBoxAddress = {}
        self.CheckButtonAddress = {}

        FrameInfos = [
            {"name": "ReadFrame", "row": 0, "col": 0, "top_minsize": 20},
            {"name": "DarkFileFrame", "row": 0, "col": 1, "top_minsize": 20},
            {"name": "FrameFrame", "row": 0, "col": 2, "top_minsize": 20},
            {"name": "ROIFrame", "row": 0, "col": 3, "top_minsize": 20},
            {"name": "SummaryFrame", "row": 0, "col": 4, "top_minsize": 20},
            {"name": "DivisionFrame", "row": 0, "col": 5, "top_minsize": 20},
            {"name": "PixelMathFrame", "row": 0, "col": 6, "top_minsize": 20},
            {"name": "SaveFrame", "row": 0, "col": 7, "top_minsize": 20},
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

            # FrameFrame
            {"parent": self.FrameFrame, "name": "Label4_2_1", "text": "", "row": 3, "col": 0, "columnspan": 2},

            # SummaryFrame
            {"parent": self.SummaryFrame, "name": "Label6_1_1", "text": "Image Size", "row": 2, "col": 0},
            {"parent": self.SummaryFrame, "name": "Label6_2_1", "text": "Frame", "row": 3, "col": 0},
            {"parent": self.SummaryFrame, "name": "Label6_3_1", "text": "ROI(Left, Right)", "row": 4, "col": 0},
            {"parent": self.SummaryFrame, "name": "Label6_4_1", "text": "ROI(Down, Up)", "row": 5, "col": 0},

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

            # PixelMathFrame
            {"parent": self.PixelMathFrame, "name": "Label8_1_1", "text": "Criterion", "row": 2, "col": 0},
            {"parent": self.PixelMathFrame, "name": "Label8_2_1", "text": "Maximum Value", "row": 3, "col": 0},
            {"parent": self.PixelMathFrame, "name": "Label8_3_1", "text": "Add Value", "row": 4, "col": 0},
        ]

        for label_info in LabelInfos:
            UI.UIBuilder.make_label(self, label_info)

        EntryInfos = [
            # ReadFrame
            {"parent": self.ReadFrame, "name": "Entry2_1_1", "textvariable": self.ImageSize_Row, "default": 1280, "row": 2, "col": 2, "width": 4},
            {"parent": self.ReadFrame, "name": "Entry2_1_2", "textvariable": self.ImageSize_Col, "default": 1280, "row": 2, "col": 3, "width": 4},

            # FrameFrame
            {"parent": self.FrameFrame, "name": "Entry4_1_1", "textvariable": self.FOI_Start, "default": 0, "row": 2, "col": 0, "width": 4},
            {"parent": self.FrameFrame, "name": "Entry4_1_2", "textvariable": self.FOI_End, "default": 0, "row": 2, "col": 1, "width": 4},

            # ROIFrame
            {"parent": self.ROIFrame, "name": "Entry5_1_1", "textvariable": self.ROI_Left, "default": 0, "row": 2, "col": 0, "width": 4},
            {"parent": self.ROIFrame, "name": "Entry5_1_2", "textvariable": self.ROI_Right, "default": 0, "row": 2, "col": 1, "width": 4},
            {"parent": self.ROIFrame, "name": "Entry5_2_1", "textvariable": self.ROI_Dn, "default": 0, "row": 3, "col": 0, "width": 4},
            {"parent": self.ROIFrame, "name": "Entry5_2_2", "textvariable": self.ROI_Up, "default": 0, "row": 3, "col": 1, "width": 4},

            # DivisionFrame
            {"parent": self.DivisionFrame, "name": "Entry7_1_2", "textvariable": self.Division_Column, "default": 1, "row": 2, "col": 1, "width": 4},
            {"parent": self.DivisionFrame, "name": "Entry7_2_2", "textvariable": self.Division_Row, "default": 1, "row": 3, "col": 1, "width": 4},

            # PixelMathFrame
            {"parent": self.PixelMathFrame, "name": "Entry8_1_2", "textvariable": self.Criterion, "row": 2, "col": 1, "width": 4},
            {"parent": self.PixelMathFrame, "name": "Entry8_2_2", "textvariable": self.MaxValue, "row": 3, "col": 1, "width": 4},
            {"parent": self.PixelMathFrame, "name": "Entry8_3_2", "textvariable": self.AddValue, "row": 4, "col": 1, "width": 4},
        ]

        for entry_info in EntryInfos:
            UI.UIBuilder.make_entry(self, entry_info)

        ComboBoxInfos = [
            {"parent": self.ReadFrame, "name": "FormatCBox", "textvariable": self.dFormat, "values": [" raw", " tif"], "default": " raw", "row": 4, "col": 2, "columnspan": 2, "width": 4, "state": "readonly"},
        ]

        for combo_info in ComboBoxInfos:
            UI.UIBuilder.make_combobox(self, combo_info)

        ButtonInfos = [
            {"parent": self.ReadFrame, "name": "Button1", "text": "Open File", "command": self.Open_Path, "row": 1, "col": 0},
            {"parent": self.ReadFrame, "name": "Button2", "text": "Read File", "command": self.Read_Image, "row": 1, "col": 1, "columnspan": 3},

            {"parent": self.DarkFileFrame, "name": "Button3", "text": "Dark File", "command": self.Dark_Image, "row": 1, "col": 0, "columnspan": 2},

            {"parent": self.FrameFrame, "name": "Button4", "text": "Frame", "row": 1, "col": 0, "columnspan": 2, "state": "disabled"},

            {"parent": self.ROIFrame, "name": "Button5", "text": "ROI (Left, Right\nDown, Up)", "row": 1, "col": 0, "columnspan": 2, "state": "disabled"},

            {"parent": self.SummaryFrame, "name": "Button6", "text": "Show ROI", "command": lambda: self.Show_ROI(self.ROIWidget, self.InputData.copy()), "row": 1, "col": 0, "columnspan": 3},

            {"parent": self.DivisionFrame, "name": "Button7", "text": "Division", "command": lambda: self.ShowBlock(self.ImageWidget, self.ROI_Data.copy(), int(self.Division_Row.get()), int(self.Division_Column.get())), "row": 1, "col": 0, "columnspan": 2},

            {"parent": self.PixelMathFrame, "name": "Button8", "text": "Calculate", "command": lambda: self.Calculate(self.ImageWidget, self.ROIWidget, self.ROI_Data.copy(), int(self.Division_Row.get()), int(self.Division_Column.get()), self.Criterion.get(), self.MaxValue.get(), self.AddValue.get()), "row": 1, "col": 0, "columnspan": 2},

            {"parent": self.SaveFrame, "name": "Button11_1", "text": "Save Clipboard", "command": lambda: self.SaveClipboardBTNEvent(self.Output), "row": 1, "col": 0},
            {"parent": self.SaveFrame, "name": "Button11_2", "text": "Save Image", "command": lambda: self.SaveBTNEvent(self.filepath, np.uint16, self.dFormat.get()[1:], self.OutputFrame), "row": 2, "col": 0},
        ]

        for button_info in ButtonInfos:
            UI.UIBuilder.make_button(self, button_info)

        CheckButtonInfos = [
            {"parent": self.ReadFrame, "name": "CheckButton2_2", "text": "", "variable": self.OffsetCalibration, "command": lambda: WH.UIConfiguration.ButtonState([self.Button3], self.OffsetCalibration.get()), "row": 3, "col": 2, "columnspan": 2},
        ]

        for checkbutton_info in CheckButtonInfos:
            UI.UIBuilder.make_checkbutton(self, checkbutton_info)

        # ------------------------------------------------------------
        # Initial states
        # ------------------------------------------------------------
        self.CheckButton2_2.select()

        WH.UIConfiguration.ButtonState([self.Button7], False)
        WH.UIConfiguration.set_text(self.Entry7_1_2, "1")
        WH.UIConfiguration.set_text(self.Entry7_2_2, "1")
        self.Entry7_1_2.configure(state="readonly")
        self.Entry7_2_2.configure(state="readonly")

if __name__ == '__main__':
    window = tkinter.Tk()
    PixelMathAnalysis(window)
    window.mainloop()
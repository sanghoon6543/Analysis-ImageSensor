import numpy as np
import sys
import os
import tkinter
from tkinter import *

sys.path.append(os.path.dirname(os.getcwd()))
import HelperFunction as HF
import WidgetHelper as WH
import UI_Builder as UI
import DPSConfig as DPS


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
        self.t_frame = np.array([], dtype=np.float64)
        self.Average = 0
        self.Sigma = 0

        self.SystemClock,self.BitDepth, self.LogFactor, self.Nth = StringVar(), IntVar(),IntVar(), IntVar()
        self.SystemClock.set("50E6")
        self.BitDepth.set(12)
        self.LogFactor.set(511)
        self.Nth.set(18700)

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
        self.InputData = self.InputData - self.dark_data
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

        # WH.Plotting.ShowImage(HF.DataProcessing.TemporalAverage(self.ROI_Data), self.ImageWidget)
        WH.Plotting.ShowImage(HF.DataProcessing.TemporalAverage(self.ROI_Data), self.ROIWidget)
        # WH.ButtonClickedEvent.Save_Files(self.filepath, np.uint16, 'raw', 4095 - Frame, [f for f in listdir(self.filepath) if isfile(join(self.filepath, f))])

    def PV2Time(self, Frame, LogFactor, BitDepth, SystemClock):
        Frame = DPS.DataProcessing.PV2int(Frame)
        N = np.power(2, BitDepth)
        freq = 1 / SystemClock
        dt = np.array([0, freq], dtype = float)
        t = dt.copy()

        t = DPS.DataProcessing.LookUpTable(LogFactor, freq, t, dt, N)
        self.t_frame = DPS.DataProcessing.PV2time(Frame, t)
        asdf = 1

    def Calculate(self, Frame):

        Frame = HF.DataProcessing.t2J(HF.DataProcessing.Array2Maskedarray(Frame), mu_sat=self.Nth.get())
        Average = HF.DataProcessing.TemporalAverage(Frame)
        Sigma_s = HF.DataProcessing.TotalNoise(Average, Differential=False)
        Sigma = HF.DataProcessing.TemporalNoise(Frame, Differential=False)

        # WH.Plotting.ShowImage(HF.DataProcessing.TemporalAverage(Frame), ax)
        self.Label8_2_1.configure(text=f"{np.format_float_scientific(np.ma.median(Average), unique=False, precision=2)}")
        self.Label8_2_2.configure(text=f"{np.format_float_scientific(Sigma_s, unique=False, precision=2)}")

        temp = np.concatenate((Average, np.zeros(np.shape(Average)[1])[np.newaxis, :], Sigma), axis=0)
        # WH.ButtonClickedEvent.Save_Files(self.filepath, np.uint16, 'raw', 4095 - Frame)
        self.Output = temp.copy()


    def Apply_IQR(self, ax, Frame, NIQR, NIteration, ExcZero, MaskExisting, PrevMask):

        # Frame = HF.DataProcessing.Array2Maskedarray(Frame)
        Frame = HF.DataProcessing.t2J(HF.DataProcessing.Array2Maskedarray(Frame), mu_sat=self.Nth.get())

        if MaskExisting:
            IQR_Frame = Frame
            IQR_Frame.mask = PrevMask

        else:
            IQR_Frame = WH.ButtonClickedEvent.IQR(Frame, NIQR, NIteration, ExcZero)
            self.SpatialMask = IQR_Frame.mask.copy()

        Average = HF.DataProcessing.TemporalAverage(IQR_Frame)
        Sigma_s = HF.DataProcessing.TotalNoise(Average, Differential=False)

        Sigma = HF.DataProcessing.TemporalNoise(IQR_Frame, Differential=False)

        WH.Plotting.ShowImage(Average, ax)
        self.Label8_2_1.configure(text=f"{np.format_float_scientific(np.ma.median(Average), unique=False, precision=2)}")
        # self.Label8_2_2.configure(text=f"{np.format_float_scientific(np.ma.median(Sigma), unique=False, precision=2)}")
        self.Label8_2_2.configure(text=f"{np.format_float_scientific(Sigma_s, unique=False, precision=2)}")
        temp = np.concatenate((Average, np.zeros(np.shape(Average)[1])[np.newaxis, :], Sigma), axis=0)
        self.Output = temp.copy()

        self.Label9_4_2.configure(text=f"{np.ma.count_masked(Average)}")

    def SaveBTNEvent(self, data):

        WH.ButtonClickedEvent.Save_csv(self.filepath, data)

    def SaveClipboardBTNEvent(self, data):
        WH.UIConfiguration.Save2Clipboard(data)

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
            {"name": "PV2TimeFrame", "row": 0, "col": 5, "top_minsize": 20},
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

            # PV2TimeFrame
            {"parent": self.PV2TimeFrame, "name": "Label7_1_1", "text": "LogFactor", "row": 2, "col": 0},
            {"parent": self.PV2TimeFrame, "name": "Label7_2_1", "text": "Nth", "row": 3, "col": 0},
            {"parent": self.PV2TimeFrame, "name": "Label7_3_1", "text": "BitDepth", "row": 4, "col": 0},
            {"parent": self.PV2TimeFrame, "name": "Label7_5_1", "text": "System Clock", "row": 5, "col": 0},

            # CalculateFrame
            {"parent": self.CalculateFrame, "name": "Label8_1_1", "text": "Mean", "row": 2, "col": 0},
            {"parent": self.CalculateFrame, "name": "Label8_1_2", "text": "stddev", "row": 3, "col": 0},
            {"parent": self.CalculateFrame, "name": "Label8_2_1", "text": "", "row": 2, "col": 1},
            {"parent": self.CalculateFrame, "name": "Label8_2_2", "text": "", "row": 3, "col": 1},

            # IQRFrame
            {"parent": self.IQRFrame, "name": "Label9_1_1", "text": "IQR", "row": 2, "col": 0},
            {"parent": self.IQRFrame, "name": "Label9_2_1", "text": "Iterations", "row": 3, "col": 0},
            {"parent": self.IQRFrame, "name": "Label9_3_1", "text": "Excluding 0", "row": 4, "col": 0},
            {"parent": self.IQRFrame, "name": "Label9_4_1", "text": "Outliers #", "row": 5, "col": 0},
            {"parent": self.IQRFrame, "name": "Label9_4_2", "text": "", "row": 5, "col": 1},
        ]

        for label_info in LabelInfos:
            UI.UIBuilder.make_label(self, label_info)

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

            # PV2TimeFrame
            {"parent": self.PV2TimeFrame, "name": "Entry7_1_2", "textvariable": self.LogFactor, "row": 2, "col": 1, "width": 4},
            {"parent": self.PV2TimeFrame, "name": "Entry7_2_2", "textvariable": self.Nth, "row": 3, "col": 1, "width": 4},
            {"parent": self.PV2TimeFrame, "name": "Entry7_3_2", "textvariable": self.BitDepth, "row": 4, "col": 1, "width": 4},
            {"parent": self.PV2TimeFrame, "name": "Entry7_5_2", "textvariable": self.SystemClock, "row": 5, "col": 1, "width": 6},

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

            {"parent": self.FrameFrame, "name": "Button4", "text": "Frame", "row": 1, "col": 0, "columnspan": 2, "state": "disabled"},

            {"parent": self.ROIFrame, "name": "Button5", "text": "ROI (Left, Right\nDown, Up)", "row": 1, "col": 0, "columnspan": 2, "state": "disabled"},

            {"parent": self.SummaryFrame, "name": "Button6", "text": "Show ROI", "command": lambda: self.Show_ROI(self.InputData.copy()), "row": 1, "col": 0, "columnspan": 3},

            {"parent": self.PV2TimeFrame, "name": "Button7", "text": "PV2Time", "command": lambda: self.PV2Time(self.ROI_Data.copy(), self.LogFactor.get(), self.BitDepth.get(), float(self.SystemClock.get())), "row": 1, "col": 0, "columnspan": 2},

            {"parent": self.CalculateFrame, "name": "Button8", "text": "Calculate", "command": lambda: self.Calculate(self.t_frame.copy()), "row": 1, "col": 0, "columnspan": 2},

            {"parent": self.CalculateFrame, "name": "Button8_3_2", "text": "Use Previous", "command": lambda: self.Apply_IQR(self.ROIWidget, self.t_frame.copy(), self.NIQR.get(), self.NIteration.get(), self.ExcludingZero.get(), self.PrevMask.get(), self.SpatialMask), "row": 4, "col": 1, "state": "disabled"},

            {"parent": self.IQRFrame, "name": "Button9", "text": "Spatial IQR", "command": lambda: self.Apply_IQR(self.ROIWidget, self.t_frame.copy(), self.NIQR.get(), self.NIteration.get(), self.ExcludingZero.get(), self.PrevMask.get(), self.SpatialMask), "row": 1, "col": 0, "columnspan": 2},

            {"parent": self.SaveFrame, "name": "Button10", "text": "Save Image", "command": lambda: self.SaveBTNEvent(self.Output), "row": 1, "col": 0},
            {"parent": self.SaveFrame, "name": "Button10_2", "text": "Save Clipboard", "command": lambda: self.SaveClipboardBTNEvent(self.Output), "row": 2, "col": 0},
        ]

        for button_info in ButtonInfos:
            UI.UIBuilder.make_button(self, button_info)

        CheckButtonInfos = [
            {"parent": self.ReadFrame, "name": "CheckButton2_2", "text": "", "variable": self.OffsetCalibration, "command": lambda: WH.UIConfiguration.ButtonState([self.Button3], self.OffsetCalibration.get()), "row": 3, "col": 2, "columnspan": 2},

            {"parent": self.CalculateFrame, "name": "CheckButton8_3_1", "text": "", "variable": self.PrevMask, "command": lambda: [WH.UIConfiguration.ButtonState([self.Button8_3_2], self.PrevMask.get()), WH.UIConfiguration.ButtonState([self.Button9, self.Entry9_1_2, self.Entry9_2_2], not self.PrevMask.get())], "row": 4, "col": 0},

            {"parent": self.IQRFrame, "name": "CheckButton9_3_2", "text": "", "variable": self.ExcludingZero, "row": 4, "col": 1},
        ]

        for checkbutton_info in CheckButtonInfos:
            UI.UIBuilder.make_checkbutton(self, checkbutton_info)

        # ------------------------------------------------------------
        # Initial states
        # ------------------------------------------------------------
        self.CheckButton2_2.select()
        self.Button8_3_2["state"] = "disabled"


if __name__ == '__main__':
    window = tkinter.Tk()
    DarkCurrentAnalysis(window)
    window.mainloop()
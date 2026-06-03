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

class FrameStabilityAnalysis:
    def __init__(self, window):
        self.window = window
        self.window.title("Temporal Stability and Calibration")
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
        self.PrevMask = BooleanVar()
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

    def Calculate(self, ax1, ax2, Frame, row, col):

        self.Show_ROI(self.InputData.copy())
        self.ShowBlock(ax1, HF.DataProcessing.TemporalAverage(Frame), row, col)

        variance_ij = (HF.DataProcessing.TemporalNoise(Frame, Differential=False))**2
        variance_ij = HF.DataProcessing.Array2Maskedarray(variance_ij)
        stddev_y = HF.DataProcessing.RMS_Division(np.sqrt(variance_ij), row, col)

        # Frame = HF.DataProcessing.Array2Maskedarray(Frame)
        Average = HF.DataProcessing.SpatialAverage(Frame)

        WH.Plotting.Show2DPlot(ax2, np.arange(Average.__len__()), Average,
                               c='r', label=f'Raw ($\\mu$={int(np.mean(Average))} $\\sigma$={int(np.std(Average))})',
                               cla=True, xlabel='Frame Number $n^{th}$', ylabel='Pixel Value [DN]')

        self.Label8_2_1.configure(text=f"{np.format_float_scientific(np.mean(Average), unique=False, precision=2)}")
        self.Label8_2_2.configure(text=f"{np.format_float_scientific(np.sqrt(np.mean(variance_ij)), unique=False, precision=2)}")
        self.Label8_2_3.configure(text=f"{np.format_float_scientific(np.sqrt(np.ma.median(variance_ij)), unique=False, precision=2)}")

        self.Output = Average[:, np.newaxis].copy()
        self.OutputFrame = Frame.copy()


    def Apply_IQR(self, Frame, NIQR, NIteration, ax1, ax2, row, col, MaskExisting, PrevMask):
        if MaskExisting:
            MaskedImage = HF.DataProcessing.Array2Maskedarray(HF.DataProcessing.TemporalAverage(Frame))
            MaskedImage.mask = PrevMask

        else:
            MaskedImage = WH.ButtonClickedEvent.IQR(HF.DataProcessing.TemporalAverage(Frame), NIQR, NIteration, False)
            self.SpatialMask = MaskedImage.mask.copy()

        WH.Plotting.ShowImage(MaskedImage, ax1)
        self.ShowBlock(ax1, MaskedImage.copy(), row, col)
        WH.ButtonClickedEvent.Average(ax1, MaskedImage.copy(), row, col)

        # variance_ij = HF.DataProcessing.Array2Maskedarray(variance_ij)
        # variance_ij.mask = MaskedImage.mask

        Frame = HF.DataProcessing.Array2Maskedarray(Frame)
        Frame.mask = MaskedImage.mask
        Average = HF.DataProcessing.SpatialAverage(Frame)

        variance_ij = (HF.DataProcessing.TemporalNoise(Frame, Differential=False))**2
        stddev_y = HF.DataProcessing.RMS_Division(np.sqrt(variance_ij), row, col)

        WH.Plotting.Show2DPlot(ax2, np.arange(Average.__len__()), Average,
                               c='b', label=f'IQR ($\\mu$={int(np.mean(Average))} $\\sigma$={int(np.std(Average))})',
                               cla=False)

        self.Label9_3_2.configure(text=f"{np.format_float_scientific(np.mean(Average), unique=False, precision=2)}")
        self.Label9_4_2.configure(text=f"{np.format_float_scientific(np.sqrt(np.mean(variance_ij)), unique=False, precision=2)}")
        self.Label9_5_2.configure(text=f"{np.format_float_scientific(np.sqrt(np.ma.median(variance_ij)), unique=False, precision=2)}")


        self.Output = np.append(self.Output, Average[:, np.newaxis].copy(), axis=1)
        self.OutputFrame = Frame.data.copy()
        # self.OutputFrame.fill_value = 65535


    def Stability_Calibration(self, Frame, SpatialMask, NIQR, NIteration, ax1, ax2, row, col, FittingCurve = 'Exponential'):
        pady = Frame.shape[0]
        Frame = HF.DataProcessing.Array2Maskedarray(Frame)
        Frame.mask = SpatialMask
        Average = HF.DataProcessing.SpatialAverage(Frame)

        FittingCurve = 'Constant'
        k = 0
        for k in range(NIteration):
            x = np.arange(Average.__len__())
            if FittingCurve == 'Exponential':
                popt = HF.DataProcessing.CurveFit(FittingCurve, x, Average,
                                                  [np.mean(Average[:3] - Average[-3:]), -0.3, np.mean(Average[-3:])],
                                                  maxfev=10000)
                y = HF.ModelingFunction.ExponentialCurve(x, *popt)
                calFactor = popt[-1] - y

            elif FittingCurve == 'Linear':
                popt = HF.DataProcessing.CurveFit(FittingCurve, x, Average)
                y = HF.ModelingFunction.Line1D(x, *popt)
                calFactor = -y

            elif FittingCurve == 'RollingAverage':
                popt = HF.DataProcessing.CurveFit(FittingCurve, x, Average, 5)
                y = popt
                calFactor = -y + np.mean(y)

            elif FittingCurve == 'Constant':
                popt = HF.DataProcessing.CurveFit(FittingCurve, x, Average)
                y = popt
                calFactor = -y + np.mean(y)

            Frame = Frame + calFactor[:, np.newaxis, np.newaxis]

            MaskedFrame = WH.ButtonClickedEvent.IQR(HF.DataProcessing.SpatialAverage(Frame), NIQR, 1, False)
            Frame = np.delete(Frame, np.where(MaskedFrame.mask == True), axis=0)
            Frame.mask = SpatialMask
            Average = HF.DataProcessing.SpatialAverage(Frame)

        x = np.arange(Average.__len__())
        variance_ij = (HF.DataProcessing.TemporalNoise(Frame, Differential=False))**2
        stddev_y = HF.DataProcessing.RMS_Division(np.sqrt(variance_ij), row, col)

        WH.Plotting.Show2DPlot(ax2, x, Average, c='g', label=f'Cal({k+1}) ($\\mu$={int(np.mean(Average))} $\\sigma$={int(np.std(Average))})',
                           cla=False)

        self.Label10_3_2.configure(text=f"{np.format_float_scientific(np.mean(Average), unique=False, precision=2)}")
        self.Label10_4_2.configure(text=f"{np.format_float_scientific(np.sqrt(np.mean(variance_ij)), unique=False, precision=2)}")
        self.Label10_5_2.configure(text=f"{np.format_float_scientific(np.sqrt(np.ma.median(variance_ij)), unique=False, precision=2)}")


        Average = np.pad(Average.data, (0, int(pady - Average.shape[0])), 'constant')
        self.Output = np.append(self.Output, Average[:, np.newaxis].copy(), axis=1)
        self.OutputFrame = Frame.data.copy()

    def SaveBTNEvent(self, fp, dtype, data):
        # data = np.swapaxes(data, 1, 2)
        WH.ButtonClickedEvent.Save_Files(fp, dtype, "raw", data)

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
            {"name": "CalculateFrame", "row": 0, "col": 6, "top_minsize": 20},
            {"name": "IQRFrame", "row": 0, "col": 7, "top_minsize": 20},
            {"name": "CalibrationFrame", "row": 0, "col": 8, "top_minsize": 20},
            {"name": "SaveFrame", "row": 0, "col": 9, "top_minsize": 20},
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

            # CalculateFrame
            {"parent": self.CalculateFrame, "name": "Label8_1_1", "text": "Mean", "row": 2, "col": 0},
            {"parent": self.CalculateFrame, "name": "Label8_1_2", "text": "stddev", "row": 3, "col": 0},
            {"parent": self.CalculateFrame, "name": "Label8_1_3", "text": "stdev(m)", "row": 4, "col": 0},
            {"parent": self.CalculateFrame, "name": "Label8_2_1", "text": "", "row": 2, "col": 1},
            {"parent": self.CalculateFrame, "name": "Label8_2_2", "text": "", "row": 3, "col": 1},
            {"parent": self.CalculateFrame, "name": "Label8_2_3", "text": "", "row": 4, "col": 1},

            # IQRFrame
            {"parent": self.IQRFrame, "name": "Label9_1_1", "text": "IQR", "row": 2, "col": 0},
            {"parent": self.IQRFrame, "name": "Label9_2_1", "text": "Iterations", "row": 3, "col": 0},
            {"parent": self.IQRFrame, "name": "Label9_3_1", "text": "Mean", "row": 4, "col": 0},
            {"parent": self.IQRFrame, "name": "Label9_4_1", "text": "stddev", "row": 5, "col": 0},
            {"parent": self.IQRFrame, "name": "Label9_5_1", "text": "stdev(m)", "row": 6, "col": 0},
            {"parent": self.IQRFrame, "name": "Label9_3_2", "text": "", "row": 4, "col": 1},
            {"parent": self.IQRFrame, "name": "Label9_4_2", "text": "", "row": 5, "col": 1},
            {"parent": self.IQRFrame, "name": "Label9_5_2", "text": "", "row": 6, "col": 1},

            # CalibrationFrame
            {"parent": self.CalibrationFrame, "name": "Label10_1_1", "text": "IQR", "row": 2, "col": 0},
            {"parent": self.CalibrationFrame, "name": "Label10_2_1", "text": "Iterations", "row": 3, "col": 0},
            {"parent": self.CalibrationFrame, "name": "Label10_3_1", "text": "Mean", "row": 4, "col": 0},
            {"parent": self.CalibrationFrame, "name": "Label10_4_1", "text": "stddev", "row": 5, "col": 0},
            {"parent": self.CalibrationFrame, "name": "Label10_5_1", "text": "stdev(m)", "row": 6, "col": 0},
            {"parent": self.CalibrationFrame, "name": "Label10_3_2", "text": "", "row": 4, "col": 1},
            {"parent": self.CalibrationFrame, "name": "Label10_4_2", "text": "", "row": 5, "col": 1},
            {"parent": self.CalibrationFrame, "name": "Label10_5_2", "text": "", "row": 6, "col": 1},
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

            # IQRFrame
            {"parent": self.IQRFrame, "name": "Entry9_1_2", "textvariable": self.NIQR, "row": 2, "col": 1, "width": 4},
            {"parent": self.IQRFrame, "name": "Entry9_2_2", "textvariable": self.NIteration, "row": 3, "col": 1, "width": 4},

            # CalibrationFrame
            {"parent": self.CalibrationFrame, "name": "Entry10_1_2", "textvariable": self.NIQR_S, "row": 2, "col": 1, "width": 4},
            {"parent": self.CalibrationFrame, "name": "Entry10_2_2", "textvariable": self.NIteration_S, "row": 3, "col": 1, "width": 4},
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

            {"parent": self.SummaryFrame, "name": "Button6", "text": "Show ROI", "command": lambda: self.Show_ROI(self.InputData.copy()), "row": 1, "col": 0, "columnspan": 3},

            {"parent": self.DivisionFrame, "name": "Button7", "text": "Division", "command": lambda: self.ShowBlock(self.ImageWidget, self.ROI_Data.copy(), int(self.Division_Row.get()), int(self.Division_Column.get())), "row": 1, "col": 0, "columnspan": 2},

            {"parent": self.CalculateFrame, "name": "Button8", "text": "Calculate", "command": lambda: self.Calculate(self.ImageWidget, self.ROIWidget, self.ROI_Data.copy(), int(self.Division_Row.get()), int(self.Division_Column.get())), "row": 1, "col": 0, "columnspan": 2},

            {"parent": self.CalculateFrame, "name": "Button8_3_2", "text": "Use Previous", "command": lambda: self.Apply_IQR(self.ROI_Data.copy(), self.NIQR.get(), self.NIteration.get(), self.ImageWidget, self.ROIWidget, int(self.Division_Row.get()), int(self.Division_Column.get()), self.PrevMask.get(), self.SpatialMask), "row": 5, "col": 1, "state": "disabled"},

            {"parent": self.IQRFrame, "name": "Button9", "text": "Spatial IQR", "command": lambda: self.Apply_IQR(self.ROI_Data.copy(), self.NIQR.get(), self.NIteration.get(), self.ImageWidget, self.ROIWidget, int(self.Division_Row.get()), int(self.Division_Column.get()), self.PrevMask.get(), self.SpatialMask), "row": 1, "col": 0, "columnspan": 2},

            {"parent": self.CalibrationFrame, "name": "Button10", "text": "Stability\nCalibration", "command": lambda: self.Stability_Calibration(self.ROI_Data.copy(), self.SpatialMask.copy(), self.NIQR_S.get(), self.NIteration_S.get(), self.ImageWidget, self.ROIWidget, int(self.Division_Row.get()), int(self.Division_Column.get())), "row": 1, "col": 0, "columnspan": 2},

            {"parent": self.SaveFrame, "name": "Button11_1", "text": "Save Clipboard", "command": lambda: self.SaveClipboardBTNEvent(self.Output), "row": 1, "col": 0},
            {"parent": self.SaveFrame, "name": "Button11_2", "text": "Save Image", "command": lambda: self.SaveBTNEvent(self.filepath, np.uint16, self.OutputFrame), "row": 2, "col": 0},
        ]

        for button_info in ButtonInfos:
            UI.UIBuilder.make_button(self, button_info)

        CheckButtonInfos = [
            {"parent": self.ReadFrame, "name": "CheckButton2_2", "text": "", "variable": self.OffsetCalibration, "command": lambda: WH.UIConfiguration.ButtonState([self.Button3], self.OffsetCalibration.get()), "row": 3, "col": 2, "columnspan": 2},

            {"parent": self.CalculateFrame, "name": "CheckButton8_3_1", "text": "", "variable": self.PrevMask, "command": lambda: [WH.UIConfiguration.ButtonState([self.Button8_3_2], self.PrevMask.get()), WH.UIConfiguration.ButtonState([self.Button9, self.Entry9_1_2, self.Entry9_2_2], not self.PrevMask.get())], "row": 5, "col": 0},
        ]

        for checkbutton_info in CheckButtonInfos:
            UI.UIBuilder.make_checkbutton(self, checkbutton_info)

        # ------------------------------------------------------------
        # Initial states
        # ------------------------------------------------------------
        self.CheckButton2_2.select()
        self.Button8_3_2["state"] = "disabled"

        WH.UIConfiguration.ButtonState([self.Button7], False)
        WH.UIConfiguration.set_text(self.Entry7_1_2, "1")
        WH.UIConfiguration.set_text(self.Entry7_2_2, "1")
        self.Entry7_1_2.configure(state="readonly")
        self.Entry7_2_2.configure(state="readonly")


if __name__ == '__main__':
    window = tkinter.Tk()
    FrameStabilityAnalysis(window)
    window.mainloop()
import tkinter
from tkinter.ttk import Combobox
import WidgetHelper as WH


class UIBuilder:
    """Helper methods for building Tkinter GUI widgets from info dictionaries."""
    @staticmethod
    def make_control_frame(owner, parent, info):
        """Required: name, row, col"""

        name = info['name']
        frame = tkinter.Frame(parent)
        frame.grid(row=info["row"], column=info["col"], rowspan=info.get("rowspan", 1), columnspan=info.get("columnspan", 1),
                    padx=info.get("padx", 4), pady=info.get("pady", 2), sticky=info.get("sticky", "n"))
        frame.grid_rowconfigure(0, minsize=20)
        setattr(owner, name, frame)
        owner.FrameAddress[name] = frame
        return frame

    @staticmethod
    def make_button(owner, info):
        """ Required: name, row, col """
        name = info["name"]
        parent = info['parent']
        button_kwargs = {}

        if "textvariable" in info:
            button_kwargs["textvariable"] = info["textvariable"]
        else:
            button_kwargs["text"] = info.get("text", "")

        if "command" in info:
            button_kwargs["command"] = info["command"]

        if "width" in info:
            button_kwargs["width"] = info["width"]

        widget = tkinter.Button(parent, **button_kwargs)

        if "state" in info:
            widget["state"] = info["state"]

        widget.grid(row=info["row"], column=info["col"], rowspan=info.get("rowspan", 1), columnspan=info.get("columnspan", 1),
                    padx=info.get("padx", 1), pady=info.get("pady", 1), sticky=info.get("sticky", ""))

        setattr(owner, name, widget)
        owner.ButtonAddress[name] = widget
        return widget

    @staticmethod
    def make_label(owner, info):
        name = info["name"]
        parent = info['parent']
        label_kwargs = {}

        if "text" in info:
            label_kwargs["text"] = info["text"]
        if "textvariable" in info:
            label_kwargs["textvariable"] = info["textvariable"]
        if "width" in info:
            label_kwargs["width"] = info["width"]
        widget = tkinter.Label(parent, **label_kwargs)

        widget.grid(
            row=info["row"], column=info["col"], rowspan=info.get("rowspan", 1), columnspan=info.get("columnspan", 1),
            padx=info.get("padx", 1), pady=info.get("pady", 1), sticky=info.get("sticky", "")
        )
        setattr(owner, name, widget)
        owner.LabelAddress[name] = widget
        return widget

    @staticmethod
    def make_entry(owner, info):
        """ Required: name, textvariable, row, col """

        name = info["name"]
        parent = info['parent']
        entry_kwargs = {
            "textvariable": info["textvariable"],
            "width": info.get("width", 4),
            "relief": info.get("relief", "ridge"),
        }

        if "state" in info:
            entry_kwargs["state"] = info["state"]

        widget = tkinter.Entry(parent, **entry_kwargs)

        widget.grid(
            row=info["row"], column=info["col"], rowspan=info.get("rowspan", 1), columnspan=info.get("columnspan", 1),
            padx=info.get("padx", 1), pady=info.get("pady", 1), sticky=info.get("sticky", "")
        )

        if "default" in info:
            WH.UIConfiguration.set_text(widget, str(info["default"]))

        setattr(owner, name, widget)
        owner.EntryAddress[name] = widget

        return widget

    @staticmethod
    def make_combobox(owner, info):
        """ Required: name, textvariable, values, row, col """
        name = info["name"]
        parent = info['parent']

        widget = Combobox(parent, width=info.get("width", 8), textvariable=info["textvariable"],
                          state=info.get("state", "readonly"), values=info["values"])

        widget.set(info.get("default", info["values"][0]))

        widget.grid(row=info["row"], column=info["col"], rowspan=info.get("rowspan", 1), columnspan=info.get("columnspan", 1),
            padx=info.get("padx", 1), pady=info.get("pady", 1), sticky=info.get("sticky", ""))

        setattr(owner, name, widget)
        owner.ComboBoxAddress[name] = widget

        return widget

    @staticmethod
    def make_checkbutton(owner, info):
        """ Required: name, text, variable, row, col """
        name = info["name"]
        parent = info['parent']
        widget = tkinter.Checkbutton(parent,text=info["text"], variable=info["variable"], command=info.get("command"))

        widget.grid(row=info["row"], column=info["col"], rowspan=info.get("rowspan", 1), columnspan=info.get("columnspan", 1),
                    padx=info.get("padx", 1), pady=info.get("pady", 1), sticky=info.get("sticky", ""))

        setattr(owner, name, widget)
        owner.CheckButtonAddress[name] = widget

        return widget


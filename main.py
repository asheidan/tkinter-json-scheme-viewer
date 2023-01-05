#!/usr/bin/env python3

from collections import OrderedDict
import json
import os, os.path
import sys
from tkinter import ttk
import tkinter as tk
import tkinter.font as tk_font
from typing import Dict, List, Optional, Sequence, Tuple


def append_to(tree, text: str, parent: str = "", tags: Sequence = (), values: Sequence = ()) -> str:
    return tree.insert(parent=parent, index="end", text=text, values=values, tags=tags, open=True)


class Application(tk.Frame):
    def __init__(self, master=None, structure=()):
        super().__init__(master=master)

        self.structure = structure

        self.default_font = tk_font.nametofont("TkDefaultFont")
        self.default_font.configure(size=-11)
        #tk_font.nametofont("TkBoldFont").configure(size=-11)

        #self.grid()
        self.pack(fill='both')

        self.create_widgets()
        self.bind_keys()

    def create_widgets(self):
        style = ttk.Style(self)

        #print(style.theme_names())
        #style.theme_use('alt')

        style.configure('Treeview', rowheight=17)
        style.configure('Treeview.Heading', font=self.default_font)

        # print(tk_font.families())
        #mono_font = tk_font.Font( #family="Fira Code", size=-11,)
        font_bold = tk_font.Font(weight='bold', size=-11)

        self.tree_view = ttk.Treeview(self, columns=("Type",), height=50, selectmode="browse", displaycolumns=('Type',))  # , show="tree")
        self.tree_view.tag_configure('parent', font=font_bold)

        #self.tree_view.heading('Name', text='Name')
        self.tree_view.heading('Type', text='Type')

        self.tree_view.column(0, stretch=True)

        #self.tree_view.grid()
        self.tree_view.pack(fill='both')

        self.parse_structure(structure=self.structure)

    def parse_structure(self, structure, parent=""):
        for name, type_description, properties in structure:
            current = append_to(tree=self.tree_view, parent=parent, text=(name or ""), values=[type_description], tags=('parent',) if properties else ())
            if properties:
                self.parse_structure(parent=current, structure=properties)

    def toggle_type_column(self, event: tk.Event):
        widget = event.widget

        # This should only be a widget with columns
        display_columns = widget["displaycolumns"]

        match display_columns:
            case ('#all',):
                widget["displaycolumns"] = []
            case '':
                widget["displaycolumns"] = ('Type',)
                widget.column('Type', width=int(widget.winfo_width()/(len(widget["displaycolumns"])+1)))
            case other:
                if 'Type' in other:
                    widget["displaycolumns"] = tuple(c for c in other if c != 'Type')
                else:
                    widget["displaycolumns"] = other + ('Type',)



    def bind_keys(self):
        self.tree_view.bind('<KeyPress-j>', lambda event: event.widget.event_generate('<Down>', when='tail'))
        self.tree_view.bind('<KeyPress-k>', lambda event: event.widget.event_generate('<Up>', when='tail'))
        self.tree_view.bind('<KeyPress-h>', lambda event: event.widget.event_generate('<Left>', when='tail'))
        self.tree_view.bind('<KeyPress-l>', lambda event: event.widget.event_generate('<Right>', when='tail'))

        self.tree_view.bind('<KeyPress-T>', self.toggle_type_column)


class JSONSchema:
    schema_version = None

    @classmethod
    def from_json(cls, json_structure: Dict, version=None) -> "JSONSchema":
        if ref := json_structure.get("$ref"):
            if "#" != ref[0]:

                return cls.from_file(ref)

        schema_version = json_structure.get("$schema") or version
        schema_class = JSONSchemaDraft4
        for subclass in JSONSchema.__subclasses__():
            if schema_version == subclass.schema_version:
                schema_class = subclass

                break

        schema = schema_class.from_json(json_structure)

        return schema

    @classmethod
    def from_file(cls, filename) -> "JSONSchema":
        with open(filename, "r") as json_file:
            data = json.load(json_file, object_pairs_hook=OrderedDict)

        with cd(os.path.dirname(filename)):
            schema = JSONSchema.from_json(data)

        return schema


class JSONSchemaDraft4(JSONSchema):
    schema_version = "http://json-schema.org/draft-04/schema#"

    @classmethod
    def from_json(cls, json_structure) -> "JSONSchemaDraft4":
        name = json_structure.get("title")

        type_info = json_structure.get("type", "")
        if 'object' == type_info:
            if object_title := json_structure.get("title"):
                type_info = object_title

                # Some schemas add this as a suffix to all classes which I don't want to see
                # TODO: Move this to a setting
                type_info = type_info.replace("Representation", "")

        if "array" == type_info:
            item_schema = JSONSchema.from_json(json_structure.get("items", {}), version=cls.schema_version)
            type_info += f"<{item_schema.type_info}>"
            properties = {"items": item_schema}
        else:
            properties = OrderedDict((k, JSONSchema.from_json(v, version=cls.schema_version)) for k, v in json_structure.get("properties", {}).items())

        if "string" == type_info:
            if type_format := json_structure.get("format"):
                type_info += f"<{type_format}>"

        return cls(name=name, type_info=type_info, properties=properties)

    def __init__(self, type_info: str, properties: OrderedDict, name: Optional[str] = None) -> None:
        self.name = name
        self.type_info = type_info
        self.properties = properties

    def as_structure(self, name=None) -> Tuple:
        #print(repr(self.properties))
        return (name or self.name, self.type_info, [p.as_structure(k) for k, p in self.properties.items()])


class cd:
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.previous_path = None

    def __enter__(self):
        self.previous_path = os.getcwd()
        # print(f"cd: {self.previous_path} -> {self.path}", file=sys.stderr)
        os.chdir(self.path)

        return self

    def __exit__(self, ex_type, ex_value, ex_traceback):
        os.chdir(self.previous_path)


def main() -> None:
    #root: tk.Tk = tk.Tk()
    #root.mainloop()

    if 1 < len(sys.argv):
        schema = JSONSchema.from_file(sys.argv[1])

    from pprint import pprint
    pprint(schema.as_structure())

    app = Application(structure=[schema.as_structure()])
    app.master.title("Foo")

    app.mainloop()


if __name__ == "__main__":
    main()

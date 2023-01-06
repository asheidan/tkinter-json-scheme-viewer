#!/usr/bin/env python3

from collections import OrderedDict
import json
import os, os.path
import sys
from tkinter import ttk
import tkinter as tk
import tkinter.font as tk_font
from typing import Dict, List, Optional, Sequence, Tuple


def append_to(tree, text: str, parent: str = "", tags: Sequence = (), values: Sequence = (), open=True) -> str:
    return tree.insert(parent=parent, index="end", text=text, values=values, tags=tags, open=open)


class Application(tk.Frame):
    TYPE_COLUMN_WIDTH = 100

    def __init__(self, schema: "JSONSchema", master=None):
        super().__init__(master=master)

        self.schema = schema

        self.tree_to_schema = {}

        self.winfo_toplevel().resizable(True, True)
        #self.columnconfigure(1, weight=1)
        #self.grid(sticky="news")
        #self.pack(fill='both')

        self.create_widgets()
        self.bind_keys()

        root_item = self.add_schema(schema=self.schema)
        #self.after(0, lambda: self.tree_view.focus(root_item))

        self.pack(fill=tk.BOTH)

        self.tree_view.grab_set()
        #print(self.grab_current(), file=sys.stderr)
        self.tree_view.selection_set(root_item)
        self.tree_view.focus(root_item)
        self.tree_view.focus_force()

    def create_widgets(self):
        style = ttk.Style(self)

        #print(style.theme_names())
        #style.theme_use('alt')

        # print(tk_font.families())
        self.default_font = tk_font.nametofont("TkDefaultFont")
        self.default_font.configure(size=-11)
        #tk_font.nametofont("TkBoldFont").configure(size=-11)
        #mono_font = tk_font.Font( #family="Fira Code", size=-11,)
        font_bold = tk_font.Font(weight='bold', size=-11)
        font_smaller = tk_font.Font(size=-9)

        style.configure('Treeview', rowheight=17, indent=10)
        style.configure('Treeview.Heading', font=self.default_font)

        self.panes = tk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.panes.pack(fill=tk.BOTH, expand=1)

        # treeview pane
        self.tree_view = ttk.Treeview(self.panes, height=50, selectmode="browse", takefocus=1,
                                      columns=("Type",), displaycolumns=('Type',), show="tree")
        self.tree_view.tag_configure('parent', font=font_bold)
        self.tree_view.tag_configure('definitions', font=font_smaller, foreground='#999')
        self.tree_view.tag_configure('properties', font=font_smaller, foreground='#77b')
        self.tree_view.heading('Type', text='Type')
        self.tree_view.column('#0', stretch=True, minwidth=200)
        self.tree_view.column('Type', stretch=False,
                              minwidth=self.TYPE_COLUMN_WIDTH, width=self.TYPE_COLUMN_WIDTH)
        self.panes.add(self.tree_view, minsize=200)

        # details pane
        self.details = ttk.Treeview(self.panes, selectmode="none", show="tree", columns=("Value",),
                                    takefocus=False)
        self.details.column('#0', stretch=False, width=100, minwidth=100, anchor="e")
        self.details.column('Value', stretch=True, minwidth=100)
        self.panes.add(self.details)

    def add_schema(self, schema: "JSONSchema", parent: str = "", name: str = "") -> str:
        properties = schema.properties
        current_root = append_to(tree=self.tree_view, parent=parent,
                                 text=schema.treeview_text() or name,
                                 values=schema.treeview_values(),
                                 tags=('parent',) if properties else ())
        self.tree_to_schema[current_root] = schema

        if properties:
            required_properties = schema.details.get("required", ())
            parent_node = append_to(tree=self.tree_view, parent=current_root, text="properties", tags=('properties',))
            for key, property_schema in properties.items():
                is_required = key in required_properties
                required_indicator = " *" if is_required else ""
                #current = append_to(tree=self.tree_view, parent=current_root, text=key)
                self.add_schema(parent=parent_node, schema=property_schema, name=key + required_indicator)

        if schema.additional_properties is not None:
            #print("add_schema", schema.additional_properties, file=sys.stderr)
            match schema.additional_properties:
                case bool():

                    append_to(tree=self.tree_view, parent=current_root,
                              text="additionalProperties", values=(schema.additional_properties,),
                              tags=('properties',))
                case OrderedDict():
                    parent_node = append_to(tree=self.tree_view, parent=current_root,
                                            text="additionalProperties", tags=('properties',))
                    for key, property_schema in schema.additional_properties.items():
                        #current = append_to(tree=self.tree_view, parent=current_root, text=key)
                        self.add_schema(parent=parent_node, schema=property_schema, name=key)
                case _:  # Probably JSONSchema
                    parent_node = append_to(tree=self.tree_view, parent=current_root,
                                            text="additionalProperties", tags=('properties',))
                    self.add_schema(schema=schema.additional_properties, parent=parent_node)

        if schema.pattern_properties:
            parent_node = append_to(tree=self.tree_view, parent=current_root, text="patternProperties", tags=('properties',))
            for key, property_schema in schema.pattern_properties.items():
                #current = append_to(tree=self.tree_view, parent=current_root, text=key)
                self.add_schema(parent=parent_node, schema=property_schema, name=key)


        if schema.definitions:
            definitions = append_to(tree=self.tree_view, parent=current_root, text="definitions", tags=('definitions',), open=False)
            for key, definition_schema in schema.definitions.items():
                self.add_schema(parent=definitions, schema=definition_schema, name=key)

        return current_root

    def toggle_type_column(self, event: tk.Event) -> None:
        #widget = event.widget
        widget = self.tree_view

        # This should only be a widget with columns
        display_columns = widget["displaycolumns"]

        match display_columns:
            case ('#all',):
                widget["displaycolumns"] = []
            case '':
                widget["displaycolumns"] = ('Type',)
                widget.column('Type', width=self.TYPE_COLUMN_WIDTH)
            case other:
                if 'Type' in other:
                    widget["displaycolumns"] = tuple(c for c in other if c != 'Type')
                    widget.column('#0', width=widget.column('#0')['width'] + self.TYPE_COLUMN_WIDTH)
                else:
                    widget["displaycolumns"] = other + ('Type',)
                    widget.column('Type', width=self.TYPE_COLUMN_WIDTH)

    def update_selection(self, event: tk.Event) -> None:
        selection = self.tree_view.selection()
        selected_id = selection[0]

        # Let's clear and add to see if we get flickering and have to optimize
        self.details.delete(*self.details.get_children())

        if selected_schema := self.tree_to_schema.get(selected_id):
            for key, value in selected_schema.details.items():
                if key in ("definitions", "properties", "patternProperties", "additionalProperties", "items"):

                    continue

                formatted_value = value
                if isinstance(value, (list, dict, OrderedDict)):
                    formatted_value = json.dumps(value)  # , indent=2)
                append_to(self.details, text=key + ":", values=(formatted_value,))

    def bind_keys(self):
        widget = self.tree_view

        self.tree_view.bind('<KeyPress-j>', lambda _event: widget.event_generate('<Down>', when='tail'))
        self.tree_view.bind('<KeyPress-k>', lambda _event: widget.event_generate('<Up>', when='tail'))
        self.tree_view.bind('<KeyPress-h>', lambda _event: widget.event_generate('<Left>', when='tail'))
        self.tree_view.bind('<KeyPress-l>', lambda _event: widget.event_generate('<Right>', when='tail'))

        self.tree_view.bind('<KeyPress-T>', self.toggle_type_column)

        self.tree_view.bind('<<TreeviewSelect>>', self.update_selection)


class JSONSchema:
    schema_version = None

    @classmethod
    def from_json(cls, json_structure: Dict, version=None) -> "JSONSchema":
        if ref := json_structure.get("$ref"):
            if "#" == ref[0]:
                pass
            elif ref.startswith("http"):
                pass
            else:
                return cls.from_file(ref)

            # TODO: Add possibility to jump to "local" definitions.
            # This will prevent the possibility of infinite loops.
            # Maybe adding a stack with historic positions which are pushed
            # when navigating to a reference and then pop the stack when
            # returning.

        schema_version = json_structure.get("$schema") or version

        # Use draft-04 as the default until we have multiple versions
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

        # Uses the fact that we are single threaded to change to the directory
        # of the file we are reading to be able to handle relative paths in the
        # schemas. This is not a nice way of solving it, but it works as long
        # as we are running in a single thread.
        with cd(os.path.dirname(filename)):
            schema = JSONSchema.from_json(data)

        return schema

    def __init__(self, type_info: str,
                 properties: OrderedDict, additional_properties: OrderedDict,
                 pattern_properties: Optional[OrderedDict] = None,
                 name: Optional[str] = None,
                 definitions: Optional[OrderedDict] = None, details: Optional[Dict] = None,
                 ) -> None:
        self.name = name
        self.type_info = type_info

        self.properties = properties
        self.additional_properties = additional_properties
        self.pattern_properties = pattern_properties

        self.definitions = definitions

        self.details = details

    def treeview_text(self) -> str:
        return self.name or ""

    def treeview_values(self) -> Tuple:
        k = "$ref"
        return (self.type_info or (k if k in self.details else ""),)

    def _as_structure(self, name=None) -> Tuple:
        #print(repr(self.properties))
        return (name or self.name, [self.type_info], [p._as_structure(k) for k, p in self.properties.items()])


class JSONSchemaDraft4(JSONSchema):
    schema_version = "http://json-schema.org/draft-04/schema#"

    @classmethod
    def from_json(cls, json_structure) -> "JSONSchemaDraft4":
        # TODO: This should all be moved to the main class.
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
            properties = OrderedDict((k, JSONSchema.from_json(v, version=cls.schema_version))
                                     for k, v in json_structure.get("properties", {}).items())

        if type_format := json_structure.get("format"):
            type_info += f"<{type_format}>"

        additional_properties = json_structure.get("additionalProperties")
        #if additional_properties is not None:
        #    print("from_json", additional_properties, file=sys.stderr)
        if isinstance(additional_properties, OrderedDict):
            additional_properties = JSONSchema.from_json(additional_properties, version=cls.schema_version)

        if pattern_properties := json_structure.get("patternProperties"):
            pattern_properties = OrderedDict((k, JSONSchema.from_json(v, version=cls.schema_version))
                                             for k, v in pattern_properties.items())

        if definitions := json_structure.get("definitions"):
            definitions = OrderedDict((k, JSONSchema.from_json(v, version=cls.schema_version))
                                      for k, v in definitions.items())

        return cls(name=name, type_info=type_info,
                   properties=properties, additional_properties=additional_properties,
                   pattern_properties=pattern_properties,
                   definitions=definitions, details=json_structure)


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

    #from pprint import pprint
    #pprint(schema.as_structure())

    app = Application(schema=schema)
    app.master.title("Foo")

    app.mainloop()


if __name__ == "__main__":
    main()

from pathlib import Path
import re
from typing import List
from pprint import pprint
from dataclasses import dataclass

TEMPLATE = Path(__file__).parent / "output_template.pyi"

TYPES_MAP = {
    "bool": "bool",
    "string": "str",
    "int": "int",
    "idx": "int",
}

ARG_OVERRIDES = {
    "MediaPoolItem: list": "MediaPoolItem: List[MediaPoolItem]",
    "MediaPoolItem: Any": "MediaPoolItem: MediaPoolItem",
    "mediaPoolItem: Any": "MediaPoolItem: MediaPoolItem",
    "project: Any": "project: Project",
    "Project: list": "Project: List[Project]",
    "idx: Any": "idx: int",
    "color: Any": "color: str",
}

CLASS_NAMES = set()


@dataclass
class Function:
    name: str
    args: List[str]
    return_type: str
    description: str

    @property
    def processed_args(self) -> str:
        args_output = []
        for arg in self.args:
            if arg == "...":
                args_output.remove(args_output[-1])
                args_output[-1] = f"*{args_output[-1]}"
                if args_output[-1].endswith("1"):
                    args_output[-1] = args_output[-1][:-1]
                continue
            if "=" in arg:
                args_output.append(arg)
                continue
            if arg.startswith("["):
                matching_type = next(
                    iter(name for name in CLASS_NAMES if name.lower() in arg.lower()),
                    "Any",
                )
                args_output.append(
                    f"{re.sub(r'[^A-Za-z]', '', arg)}: list[{matching_type}]"
                )
                continue
            if arg.startswith("{"):
                matching_type = next(
                    iter(name for name in CLASS_NAMES if name.lower() in arg.lower()),
                    "Any",
                )
                args_output.append(
                    f"{re.sub(r'[^A-Za-z]', '', arg)}: dict[{matching_type}]"
                )
                continue
            if arg.lower().endswith("name") or arg.lower().endswith("path"):
                args_output.append(f"{arg}: str")
                continue
            if (
                arg.lower().endswith("id")
                or arg.lower().endswith("idx")
                or arg.lower().endswith("index")
            ):
                args_output.append(f"{arg}: int")
                continue
            if arg.lower().endswith("type") or arg.lower().endswith("mode"):
                args_output.append(f"{arg}: str")
                continue

            matching_type = next(
                iter(name for name in CLASS_NAMES if name.lower() == arg.lower()),
                "Any",
            )
            args_output.append(arg + ": " + matching_type)
        args_output = [ARG_OVERRIDES.get(a, a) for a in args_output]

        return ", ".join(args_output)


def generate_resolve_type_hints(readme_file: Path) -> str:
    readme = readme_file.read_text()

    output = TEMPLATE.read_text()

    # split into sections, by ------ lines
    sections = re.split(r"[\w ]+\n-{4,99}", readme)

    functions_section = next(
        iter(s for s in sections if "Some commonly used API functions" in s)
    ).replace("\n\n", "\n")

    raw_classes = re.findall(r"(^\w+\n( +.+\n)+)", functions_section, re.MULTILINE)

    classes = {"GalleryStill": []}

    for object, _ in raw_classes:
        object_name = object.split("\n")[0]
        func_parts = re.findall(
            r" +(?P<name>\w+)\((?P<args>.+){0,1}\) +--> (?P<return>[\w\[\]]+) +# (?P<desc>[ \w\n\W]+?(?=  \w|\n$))",
            object,
        )
        functions = []

        for name, args, ret_type, desc in func_parts:
            args = args.split(",") if args else []
            desc = re.sub(r" +# *", "", desc.strip()).replace("\n", "\n\t\t")
            functions.append(
                Function(
                    name.strip(),
                    [i.strip() for i in args],
                    ret_type.strip(),
                    desc.strip(),
                )
            )

        classes[object_name] = functions
        CLASS_NAMES.add(object_name)

    for class_name, functions in classes.items():
        # fix types
        for func in functions:
            returns_list = "[" in func.return_type
            raw_type = func.return_type.replace("[", "").replace("]", "")

            return_type_found = next(
                iter(v for t, v in TYPES_MAP.items() if t.lower() == raw_type.lower()),
                next(
                    iter(t for t in classes.keys() if t.lower() == raw_type.lower()),
                    "Any",
                ),
            )
            if returns_list:
                return_type_found = f"List[{return_type_found}]"
            func.return_type = return_type_found

        # generate stubs
        output += f"\nclass {class_name}:\n\t...\n"
        for func in functions:
            # check for duplicate functions
            if func.name in [f.name for f in functions if f != func]:
                output += f"\t@overload\n"
            output += (
                f"\tdef {func.name}({func.processed_args}) -> {func.return_type}:\n"
            )
            output += f'\t\t"""{func.description}"""\n'
            output += "\t\t...\n"
        output += "\n"

    return output


if __name__ == "__main__":
    readme = Path(__file__).parent / "original_resolve_docs" / "README.txt"
    output = Path(__file__).parent / "output" / "DaVinciResolveScript.pyi"
    stubs = generate_resolve_type_hints(readme)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(stubs)

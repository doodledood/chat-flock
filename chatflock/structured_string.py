from typing import List, Optional

import dataclasses


@dataclasses.dataclass
class Section:
    name: str
    text: Optional[str] = None
    list: Optional[List[str]] = None
    sub_sections: Optional[List["Section"]] = None
    list_item_prefix: Optional[str] = "-"
    uppercase_name: bool = True

    def to_text(self, level: int = 0) -> str:
        result = f'{"#" * (level + 1)} {self.name.upper() if self.uppercase_name else self.name}'

        if self.text is not None:
            result += "\n" + self.text

        if self.list is not None:
            result += "\n" + "\n".join(
                [
                    f'{self.list_item_prefix if self.list_item_prefix else str(i + 1) + "."} {item}'
                    for i, item in enumerate(self.list)
                ]
            )

        if self.sub_sections is not None:
            for sub_section in self.sub_sections:
                result += "\n\n" + sub_section.to_text(level + 1)

        return result


@dataclasses.dataclass
class StructuredString:
    sections: List[Section]

    def __getitem__(self, item: str) -> Section:
        if not isinstance(item, str):
            raise TypeError(f"Item must be of type str, not {type(item)}.")

        relevant_sections = [section for section in self.sections if section.name == item]
        if len(relevant_sections) == 0:
            raise KeyError(f"No section with name {item} exists.")

        return relevant_sections[0]

    def __setitem__(self, key: str, value: Section) -> None:
        if not isinstance(key, str):
            raise TypeError(f"Key must be of type str, not {type(key)}.")

        if not isinstance(value, Section):
            raise TypeError(f"Value must be of type Section, not {type(value)}.")

        try:
            section = self[key]

            # Remove old section and replace with new one, in the same place
            self.sections.insert(self.sections.index(section), value)
            self.sections.remove(section)
        except KeyError:
            self.sections.append(value)

    def __str__(self) -> str:
        result = ""
        for section in self.sections:
            result += section.to_text() + "\n\n"

        return result

    def __repr__(self) -> str:
        return self.__str__()

from typing import Tuple, Dict
from typing import Union
import functools

def load_response(filename, decodes: bool = False) ->\
        Tuple[ int
             , Dict[str, Union[bytes, str]]
             , bytes
             ]:
    """
    Args:
        filename: str
        decodes: bool indicating whether the value of the headers dict should
          be decoded into str

    Returns:
        - int as the status code
        - dict like {str: bytes or str} as the headers dict
        - bytes as the packet load
    """

    with open(filename, "rb") as f:
        response = f.read()

    header_bytes, _, content = response.partition(b"\r\n\r\n")
    header_items = header_bytes.split(b"\r\n")
    status_code = int(header_items[0].split()[1].strip())
    header = {k.decode().lower(): (val.decode() if decodes else val)
            for k, val in
                map(functools.partial(bytes.split, sep=b": ", maxsplit=1),
                    header_items[1:])}

    return status_code, header, content

import json
from struct import *

def write_as_bin(data):
    """
    höhe
    diff
    number_txes
    block_size
    timestamp
    :param data:
    :return:
    """
    tmp_file = open("checkpoints.dat","wb")
    for block in data["blocks"]:
        tmp_file.write(pack("I", block["h"]))
        tmp_file.write(pack("I", block["b"]))
        tmp_file.write(pack("Q", block["d"]))
        tmp_file.write(pack("I", block["t"]))
        tmp_file.write(pack("H", block["n"]))
    tmp_file.close()

def load_from_bin():
    outer = {
        "top":0,
        "name:": "monero-checkpoints",
        "blocks": [],
    }

    tmp_file = open("tmp.dat","rb")
    tmp_dat = tmp_file.read()
    tmp_file.close()
    for i in range(0,len(tmp_dat),22):
        line = tmp_dat[i:i+22]
        b_tuple = unpack("IIQIH",line)
        top = b_tuple[0]
        inner = {
            "h": b_tuple[0],
            "b": b_tuple[1],
            "d": b_tuple[2],
            "t": b_tuple[3],
            "n": b_tuple[4],
        }
        outer["blocks"].append(inner)
        outer["top"] = top
    return outer



def read_dict():
    read = open("checkpoints.json","r")
    dict = json.load(read)
    read.close()
    return dict

if __name__ == "__main__":
    write_as_bin(read_dict())
    data = load_from_bin()
    for block in data["blocks"]:
        print(block["h"])
        print(block["t"])

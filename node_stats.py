import os
import json
import sys
from struct import unpack, pack

import requests
import matplotlib.pyplot as plt

port = "18081"
url_base = "http://node.xmr.to:{}/{}"
url = url_base.format(port, "json_rpc")
url_not = url_base.format(port, "get_transactions")
v_dpi = 600


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def size_to_s(size):
    bytes = int(size)
    k_bytes = bytes / 1000
    m_bytes = k_bytes / 1000
    g_bytes = m_bytes / 1000
    return str(bytes) + "b " + str(k_bytes) + "kb " + str(m_bytes) + "mb " + str(g_bytes) + "gb"


def make_request(payload):
    try:
        headers = {'content-type': 'application/json'}
        response = requests.post(url, data=json.dumps(payload), headers=headers).json()
        return response
    except IOError:
        print(bcolors.FAIL + "Fehler bei Verbindung mit Server" + bcolors.ENDC)


def get_height():
    payload = {
        "jsonrpc": "2.0",
        "id": "2.0",
        "method": "get_block_count",
    }
    return make_request(payload)["result"]["count"]


def get_block_hash():
    payload = {
        "jsonrpc": "2.0",
        "id": "0",
        "method": "on_get_block_hash",
        "params": [
            912345
        ]
    }
    return make_request(payload)["result"]


def get_block_headers_range(s_start, e_end):
    result = ""
    if start >= 0 and e_end < get_height():
        payload = {
            "jsonrpc": "2.0",
            "id": "0",
            "method": "get_block_headers_range",
            "params": {
                "start_height": s_start,
                "end_height": e_end
            }
        }
        result = make_request(payload)
    return result


def get_transaction(hashes):
    payload = {
        "txs_hashes": [
        ]
    }
    for current_hash in hashes:
        payload["txs_hashes"].append(current_hash)
    try:
        headers = {'content-type': 'application/json'}
        response = requests.post(url_not, data=json.dumps(payload), headers=headers).json()
        return response
    except IOError:
        print(bcolors.FAIL + "Fehler bei Verbindung mit Server" + bcolors.ENDC)
        return []


def write_as_bin(d_data):
    tmp_file = open("checkpoints.dat", "wb")
    for block in d_data["blocks"]:
        tmp_file.write(pack("I", block["h"]))
        tmp_file.write(pack("I", block["b"]))
        tmp_file.write(pack("Q", block["d"]))
        tmp_file.write(pack("I", block["t"]))
        tmp_file.write(pack("H", block["n"]))
    tmp_file.close()


def load_from_bin():
    outer = {
        "top": 0,
        "name:": "monero-checkpoints",
        "blocks": [],
    }

    tmp_file = open("checkpoints.dat","rb")
    tmp_dat = tmp_file.read()
    tmp_file.close()
    top = 0
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


def write_checkpoints(end):
    filename = "checkpoints.dat"
    # load existing
    top = -1
    if os.path.isfile(filename):
        outer = load_from_bin()
        top = outer["top"]
    else:
        outer = {
            "top": 0,
            "name": "monero-checkpoints",
            "blocks": [],
        }
    best = top
    step = 10000
    for i in range(top + 1, end, step):
        if (i + step) > end:
            blocks = get_block_headers_range(i, end - 1)
        else:
            blocks = get_block_headers_range(i, i + step - 1)
        for block_header in blocks["result"]["headers"]:
            c_h = block_header["height"]
            best = c_h
            inner = {
                "h": c_h,
                "d": block_header["difficulty"],
                "n": block_header["num_txes"],
                "b": block_header["block_size"],
                "t": block_header["timestamp"],
            }
            outer["blocks"].append(inner)
    outer["top"] = best
    write_as_bin(outer)
    return outer


def analyze_emission(s_start, e_end):
    total_block_reward = []
    fee_per_step = []
    emission_per_step = []
    index_list = []
    step = 40
    last = 0
    fee_sum = 0
    progress = 0
    for i in range(s_start, e_end, step):
        # print progress
        if int((i - s_start) * 100 / (e_end - start)) > progress:
            progress = int((i - s_start) * 100 / (e_end - start))
            print(bcolors.OKBLUE + "Progress: " + str(progress) + "% " + bcolors.ENDC)
        payload = {
            "jsonrpc": "2.0",
            "id": "0",
            "method": "get_coinbase_tx_sum",
            "params": {
                "height": i,
                "count": step,
            }
        }
        result = make_request(payload)
        if result and "error" not in result:
            added = result["result"]["emission_amount"]
            fee = result["result"]["fee_amount"]
            fee_sum = fee_sum + fee
            fee_per_step.append(fee)
            emission_per_step.append(added)
            total_block_reward.append((last + added))
            index_list.append(i)
            last = last + added
        else:
            print(bcolors.FAIL + "error fetching emission data, plot may be inaccurate" + bcolors.ENDC)
    # coinbase tx sum ana
    print("Total Emission: " + str(last + fee_sum))
    print("Block reward: " + str(last))
    print("Fee: " + str(fee_sum))
    print("Fee/reward ratio: " + str(fee_sum * 100 / (last + fee_sum)))

    # emission curve
    plt.plot(index_list, total_block_reward)
    plt.ylabel("Total Coinbase Emission")
    plt.xlabel("Block height")
    plt.title("Emission")
    plt.savefig("plots/bc_emission.png", dpi=v_dpi)
    plt.show()


def load_bc_from_file():
    filename = "checkpoints.json"
    read = open(filename, "r")
    c_object = json.load(read.readline())
    read.close()
    return c_object


def analyze_size(s_start, e_end, data):
    before_size = 1
    increment_size = 0
    total_size = 0
    list = data["blocks"]
    size = []
    for i in range(0, s_start):
        current = list[i]["b"]
        before_size += current
        total_size += current
        size.append(total_size)
    for i in range(s_start, e_end):
        current = list[i]["b"]
        increment_size += current
        total_size += current
        size.append(total_size)

    print("Total size: " + size_to_s(total_size))
    print("Increment size: " + size_to_s(increment_size))
    print("Ratio old/new: " + str((increment_size * 100 / before_size)) + "%")

    plt.plot(range(start, end), size[start:end])
    plt.ylabel("Blockchain size")
    plt.xlabel("Block height")
    plt.title("blockchain size")
    plt.savefig("plots/bc_size.png", dpi=v_dpi)
    plt.show()
    return increment_size


def analyze_diff(start, end, data):
    list = data["blocks"]
    plot = []
    for i in range(start, end):
        plot.append(list[i]["d"])
    plt.plot(range(start, end), plot)
    plt.ylabel("Difficulty")
    plt.xlabel("Block height")
    plt.title("difficulty")
    plt.savefig("plots/bc_difficulty.png", dpi=v_dpi)
    plt.show()


def analyze_tx_count(start, end, data, interval_size):
    list = data["blocks"]
    plot = []
    sum_txs = 0
    empty = 0
    for i in range(start, end):
        current = list[i]["n"]
        plot.append(current)
        sum_txs += current
        if current == 0:
            empty += 1
    print("Number of transactions: " + str(sum_txs))
    if sum_txs != 0:
        print("Estimated average tx size: " + size_to_s(interval_size / sum_txs))
    else:
        print("Estimated average tx size: 0")
    print("Avg. tx per block: " + str(sum_txs / (end - start)))
    print("Number of empty blocks: " + str(empty))
    print("Ratio of empty blocks: " + str(empty * 100 / (end - start)) + "%")
    plt.plot(range(start, end), plot)
    plt.ylabel("Tx count")
    plt.xlabel("Block height")
    plt.title("transactions per block")
    plt.savefig("plots/bc_tx.png", dpi=v_dpi)
    plt.show()
    return sum_txs


def analyze_fee(start, end):
    txes = []
    for i in range(start, end):
        block = get_block(i)
        if "tx_hashes" in block["result"]:
            h_tx = []
            for hash in block["result"]["tx_hashes"]:
                h_tx.append(hash)
            txes.append(get_transaction(h_tx))


def is_restreicted():
    payload = {
        "jsonrpc": "2.0",
        "id": "0",
        "method": "get_coinbase_tx_sum",
        "params": {
            "height": 0,
            "count": 1,
        }
    }
    response = make_request(payload)
    if "error" in response:
        return True
    else:
        return False


if __name__ == "__main__":
    end = 0
    start = 0
    if len(sys.argv) == 2:
        end = get_height() - 1
        start = end - int(sys.argv[1])
    elif len(sys.argv) == 3:
        end = int(sys.argv[2])
        start = int(sys.argv[1])
    else:
        print("Usage: ")
        print("python node_stats.py <number> | prints the data for the last n blocks")
        print("python node_stats.py <start> <end> | prints the data between start and end")
        exit(0)

    data = write_checkpoints(end)
    print("Länge: " + str(len(data["blocks"])))
    print("Analyze Blocks between: " + str(start) + " - " + str(end))
    interval_size = analyze_size(start, end, data)
    analyze_tx_count(start, end, data, interval_size)
    analyze_diff(start, end, data)
    # data not used anymore
    del data
    # check if node is not restricted
    if is_restreicted():
        print(bcolors.FAIL + "The selected node has the \"--restricted-rpc\" flag set can't get emission data" + bcolors.ENDC)
        exit(0)
    # long comp time
    if input(bcolors.WARNING + "Emission takes a long time to analyze do you really want to start it?(y/n)" + bcolors.ENDC) == "y":
        analyze_emission(start, end)

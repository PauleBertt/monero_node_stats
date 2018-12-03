**Monero Blockchain Stats**
===========================
This work in progress tool tries to visualize some stats about the Monero-Blockchain
like growth and the number of transactions



Dependencies:
---------------------------
requests<br>
matplotlib<br>

_install via:_<br>

    pip3 install requests matplotlib

Usage:
--------------------------- 
    python node_stats.py <number>      | prints the data for the last n blocks
    python node_stats.py <start> <end> | prints the data between start and end
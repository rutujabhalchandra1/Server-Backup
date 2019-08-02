#!/usr/bin/env python3

import json
import time
import pexpect
import subprocess
import csv
import os

destination_dir = ' server_logs/'
def scp_data_to_devserver(ip_address, user_name, password, file_path, timeout=600):
    scp_output = ""
    buffering = True
    file_name = []

    # Record start time
    scp_start_time = time.time()
    scp_cmd = "scp -r" + user_name + "@" + "[" + ip_address + "]:" + file_path + "*" + destination_dir
    print(scp_cmd)
    child = pexpect.spawn(scp_cmd, timeout=timeout)
    print("here")
    i = child.expect(["Password:", pexpect.TIMEOUT, pexpect.EOF])
    print(i)
    if i == 0:
        child.sendline(password)
        # Keep tracking the scp output till timeout
        while buffering:
            print("inside while")
            now_time = time.time()
            # delta will be in seconds
            print("delta")
            delta = now_time - scp_start_time
            print(int(delta))
            print(timeout)
            if int(delta) < timeout:
                try:
                    i = child.expect(
                        ["ETA", pexpect.TIMEOUT, pexpect.EOF], timeout=timeout
                    )
                    print(i)
                    scp_output += str(child.before)
                    print(scp_output)
                    if i != 0:
                        buffering = False
                except Exception as e:
                    print(e)
                    buffering = False
                    print("Unable to SCP")
            else:
                if delta is not None:
                    print("SCP timed out")
                buffering = False
    if "No space left on device" in scp_output:
        print("No space left on device")
    elif "100%" in scp_output:
        files = scp_output.split()
        for i in files:
            if i.endswith('tgz'):
                file_name = [i]
        print("SCP succeeded")
    else:
        print("Failed to copy the file")
    return buffering


if __name__ == "__main__":

    with open("server_details.json") as f:
        data = json.load(f)
        for i in data:
            ip_address = i["ip_address"]
            user_name = i["username"]
            password = i["password"]
            file_path = i["file_path"]
            tag = i["tag"]
            scp_data_to_devserver(ip_address, user_name, password, file_path)

            files = os.listdir(destination_dir)
            for file_name in files:
                try:
                    clowder_cmd = 'clowder put -- type=BACKUP ' + file_name + '--timeout 100000'
                    output = subprocess.check_output(clowder_cmd, shell=True)
                    output = output.decode()
                    time = str(time.time())
                    with open('output.csv', 'a') as writeFile:
                        writer = csv.writer(writeFile)
                        writer.writerows('UUID', 'TAG', 'Time', 'File name')
                        writer.writerows(output, i["tag"], time, file_name )
                except Exception as e:
                    print(e)

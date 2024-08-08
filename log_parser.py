import os
import re
import json
import argparse
from dataclasses import dataclass, asdict


@dataclass
class RequestInfo:
    ip: str = ''
    duration: int = 0
    method: str = ''
    url: str = ''
    date: str = ''
    time: str = ''


def total_completed_requests(file) -> int:
    file.seek(0)
    counter: int = 0

    for line in file:
        if len(line) > 1:
            counter += 1

    return counter


def total_http_requests(file) -> dict:
    file.seek(0)
    request = RequestInfo()
    method_counter: dict = {}
    result: dict = {}

    for line in file:
        request.method = re.search(r'\b(GET|POST|HEAD|PUT|DELETE|OPTIONS|PATCH|CONNECT)\b', line)[0]
        method_counter.setdefault(request.method, 0)
        method_counter[request.method] += 1

    for method, count in sorted(method_counter.items(), key=lambda x: x[1], reverse=True):
        result[method] = count

    return result


def three_most_frequently_used_ip(file) -> dict:
    file.seek(0)
    request = RequestInfo()

    all_ips: dict = {}
    for line in file:
        request.ip = re.search(r'([0-9]{1,3}[\.]){3}[0-9]{1,3}', line)[0]
        all_ips.setdefault(request.ip, 0)
        all_ips[request.ip] += 1

    top_three_ips: dict = {}
    sorted_ips: list = sorted(all_ips.items(), key=lambda x: x[1], reverse=True)
    for i in range(3):
        top_three_ips[sorted_ips[i][0]] = sorted_ips[i][1]

    return top_three_ips


def three_longest_requests(file) -> list:
    file.seek(0)

    all_requests: list = []
    for line in file:
        all_requests.append(RequestInfo(
            ip=re.search(r'([0-9]{1,3}[\.]){3}[0-9]{1,3}', line)[0],
            duration=int(re.search(r'\b(\d+)\b$', line)[0]),
            method=re.search(r'\b(GET|POST|HEAD|PUT|DELETE|OPTIONS|PATCH|CONNECT)\b', line)[0],
            url=line.split()[10][1:-1],
            date=re.search(r'\d{2}/\w{3}/\d{4}', line)[0],
            time=re.search(r'\b\d{2}/\w+/\d{4}:(\d{2}:\d{2}:\d{2})\b', line).group(1)
        ))

    sorted_request: list = sorted(all_requests, key=lambda r: r.duration, reverse=True)
    return [asdict(req) for req in sorted_request[:3]]


def parse_arguments():
    parser = argparse.ArgumentParser(description='Log file analysis')
    parser.add_argument('log_path', metavar='log_path', type=str, help='Path to log file or directory')
    parser.add_argument('-o', '--output', metavar='output_file', type=str, help='JSON output file')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()

    log_path = args.log_path
    output_file = args.output

    if os.path.isfile(log_path):
        log_files = [log_path]
    elif os.path.isdir(log_path):
        log_files = [os.path.join(log_path, file) for file in os.listdir(log_path) if file.endswith('.log')]
    else:
        raise ValueError('The specified path is not a directory or file')

    results: list = []
    for log_file in log_files:
        with open(log_file, 'r', encoding='UTF-8') as file:
            result: dict = {
                'Log file': file.name.split('/')[-1],
                'Total completed requests': total_completed_requests(file),
                'Number of requests by HTTP methods': total_http_requests(file),
                'Top 3 IP addresses from which requests were made': three_most_frequently_used_ip(file),
                'Top 3 longest requests': three_longest_requests(file)
            }
            results.append(result)

    if output_file:
        with open(output_file, 'w', encoding='UTF-8') as file:
            json.dump(results, file, indent=4)

    for result in results:
        print(f'Log File: {result["Log file"]}')
        print(f'Total completed requests: {result["Total completed requests"]}')
        print('Number of requests by HTTP methods:')
        for method, count in result['Number of requests by HTTP methods'].items():
            print(f'  {method}: {count}')
        print('Top 3 IP addresses from which requests were made:')
        for ip, count in result['Top 3 IP addresses from which requests were made'].items():
            print(f'  {ip}: {count}')
        print('Top 3 longest requests:')
        for request in result['Top 3 longest requests']:
            print(f'  Method: {request["method"]}')
            print(f'  URL: {request["url"]}')
            print(f'  IP: {request["ip"]}')
            print(f'  Duration: {request["duration"]} ms')
            print(f'  Date: {request["date"]}')
            print(f'  Time: {request["time"]}')
            print()

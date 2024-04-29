from scapy.all import rdpcap, IP, UDP
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from collections import Counter
import json

pacotes = rdpcap('udp.pcap')

app = FastAPI()

udp_port_counter = Counter()

for packet in pacotes:
    if IP in packet and UDP in packet:
        udp_port_counter[packet[UDP].dport] += 1

@app.get("/udp-port-stats", response_class=HTMLResponse)
async def get_udp_port_stats():
    sorted_ports = sorted(udp_port_counter.items(), key=lambda x: x[1], reverse=True)
    ports = [port for port, count in sorted_ports]
    counts = [count for port, count in sorted_ports]
    
    content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>UDP Port Statistics</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            table, th, td {
                border: 1px solid black;
                border-collapse: collapse;
            }
            th, td {
                padding: 10px;
            }
            th {
                text-align: left;
            }
            #bar-chart {
                width: 80%;
                height: 65%;
            }
        </style>
    </head>
    <body>
        <h1>UDP Port Usage Statistics</h1>
        <div>
            <canvas id="bar-chart"></canvas>
        </div>
        <table>
            <tr>
                <th>Port</th>
                <th>Count</th>
            </tr>
    """
    for port, count in sorted_ports:
        content += f"<tr><td>{port}</td><td>{count}</td></tr>"
    content += """
        </table>
        <script>
            var ctx = document.getElementById('bar-chart').getContext('2d');
            var chart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: """ + json.dumps(ports) + """,
                    datasets: [{
                        label: 'Packet Count',
                        backgroundColor: 'rgba(0, 123, 255, 0.5)',
                        borderColor: 'rgba(0, 123, 255, 1)',
                        data: """ + json.dumps(counts) + """
                    }]
                },
                options: {
                    scales: {
                        yAxes: [{
                            ticks: {
                                beginAtZero: true
                            }
                        }]
                    },
                    responsive: true,
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: 'UDP Port Usage'
                    }
                }
            });
        </script>
    </body>
    </html>
    """
    return content
